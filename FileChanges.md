The file change library included with this code reloading framework is what makes it truly useful.  It would be cumbersome to have to explicitly execute a statement to trigger the reloading of a script file managed by this framework every time it changed.  And automatic detection of changes hooked up to automatic reloading of the script files, is a huge boost to productivity.

By default a `CodeReloader` instance will enable this automatic process.  But in the event that you have your own way of notifying the framework of changed script files, you can disable this functionality and provide your own file change notification events.

These examples should illustrate how to do either.

### Example: Custom file change detection ###

**Note:** This gives a complete overview of file changes being detected and
then the changes being put in place.

Let's say you have a directory 'stuff' and the following subdirectory and
file are in there:

```
  stuff/services/net.py
```

And 'net.py' has the following class defined inside it:

```
  class NetService:
      ...
      def Test(self):
      	  return 1
      ...
```

You have registered the contents of the 'stuff' directory under the base
namespace 'server' in this manner:

```
  from livecoding import reloader
  cr = reloader.CodeReloader(monitorFileChanges=False)
  cr.AddDirectory("server", "stuff")
```

At this point all your files for your application have their contents ready
for importing and use.  Your application is running.. but you have just
realised that you need the method 'Test' to return 2 and not 1.  So you
edit it.

```
  class NetService:
      ...
      def Test(self):
      	  return 2
      ...
```

Because you have your own code to detect file changes you need to pass on the
event to the code manager.

```
  # filePath is be an absolute path ending in ".../stuff/services/net.py"
  cr.ProcessChangedFile(filePath, added=False, changed=True, deleted=False)
```

Now when Test is called on the instance of 'NetService', it will return 2.

**Warning:** If however your file change notifications are done notifies the
code manager in a thread other than the one your application is running on,
this will be unsafe.  There is no guarantee that you will not change
something which low level code in another thread is in the middle of using
in a way which will break. For instance it might be instancing a class
which you have just changed.

### Example: Using the provided file change detection ###

**Note:** Most people will probably want to have file changes detected for
them.  This is just a matter of telling the code manager when you
instantiate it.

The only difference from the first example is that when you instance the code
manager, you do not need to tell it to do the file change detection internally as this is the default behaviour.

```
  from livecoding import reloader
  cr = reloader.CodeReloader()
```

**Warning:** As mentioned in the last example it is unsafe to put in place
changes while other threads are running.  And this mechanism uses a separate
thread to put updates in place so it is definitely unsafe in this way.

### With Stackless Python ###

**Note:** If your application is written using Stackless Python, then it is
best that you use a Stackless tasklet to dispatch file change notifications.
This is a little more complicated but should be covered enough below to
address any issues which need to be resolved.  It is also the recommended
and best way to go about it, being safer than the above alternatives.

Because Stackless does not come with any built-in way of having a tasklet
sleep for a specified period of time, the file change detection needs to be
wrapped by the user to take into account how tasklet sleeping is done in
their framework.

For instance, some frameworks I have used put a 'sleep' method in place on
the 'stackless' module.  So for the purposes of demonstrating what you will
need to do, the following statement will stand in for generic methods of
sleeping in units of seconds.

```
  stackless.sleep(1.0)
```

#### Example: Custom file change detection on the same thread ####

If you poll for file changes in a tasklet, then you can pass them
directly onto the code manager in the same way shown above.

```
  def ManageFileChanges(self, cr):
      while True:
          # Pass the callback all the pending file changes should
          # be passes through.
      	  DispatchFileChanges(cr.ProcessChangedFiles)
      	  # Stall for second before checking again.
          stackless.sleep(1.0)
```

#### Example: Custom file change detection on a different thread ####

In order to be able to safely dispatch the file changes on the main
thread from the one they are detected on, a queue can be used in the
'ManageFileChanges' tasklet to receive them from the other thread.

```
  def ManageFileChanges(self, cr, queue):
      while True:
          # Pass the callback all the pending file changes should
          # be passes through.
	  try:
              while True:
                  filePath, added, changed, deleted = queue.get_nowait()
                  cr.ProcessChangedFiles(filePath, added, changed, deleted)
          except Queue.Empty:
              pass
      	  # Stall for second before checking again.
          stackless.sleep(1.0)

  import reloader
  cr = reloader.CodeReloader(monitorFileChanges=False)
  
  # queue is sourced from elsewhere and the thread managing the
  # file changes has a reference to it to send things through.

  import stackless
  stackless.tasklet(ManageFileChanges)(cr, queue)
```

#### Example: Using the provided file change detection ####

Because using Stackless Python requires that the application manage how and
when the scheduler is run, it is impossible for this library to just start a
tasklet internally and know that it will be run and that its file changes
will get handled properly.  Therefore this library cannot provide any
automatic Stackless based file change detection.  Another reason not to do
this is that it is to the benefit of the user to know how and when tasklets
are scheduled and best they manage the higher level parts of scheduling
file change detection using the provided detection method.

What this library can do is expose most of the file change handling logic
as a prewritten function in the alternative code manager class
'StacklessCodeManager' which can be scheduled in the following manner.

```
  def ManageFileChanges(self, cr):
      while True:
          cr.DispatchPendingFileChanges()
          stackless.sleep(1.0)

  from livecoding import reloader
  cr = reloader.StacklessCodeReloader(monitorFileChanges=False)

  import stackless
  stackless.tasklet(ManageFileChanges)(cr)
```