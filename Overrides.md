Overrides are just a way to dynamically intercept when a function in
any instance of a given class is called, and to be able to incorporate
some other arbitary code to be either executed in place of the original
function or combined with it in some manner.

As part of the livecoding library, this functionality is of course
directly linked to its custom importing.  While it is of course
possible to build matching functionality on top of the standard Python
module importing, this library does not do that, or aim to do so at
this time.

**Note**: This part of the code is still a work in progress, and still requires
more work for it to be as flexible as it needs to be to be usable in the
way described below.  For instance, at the moment the injection of overrides
is not quite finished.  There is also no way to specify how overrides should
be placed, whether they should replace the function they override or whether
they should be executed before, after or wrap that function.

### The inline approach ###

The easiest approach to various types of logging, whether general
information of interest, or to account for where cpu time is spent or
whatever, is the imperative approach.  Littering the code with inline
statements, the purpose of which is often forgotten, and the statements
remaining until they are removed on a whim at some later date.  Some
common examples follow.

Designating that time spent in specific functions should be specially
counted under specific time usage labels.

```
  def SendMessage(self, srcID, dstID, msg):
      # Clock the cpu time spent in the following function up to the
      # given label.
      TrackCpu("message sending", self.SendMessage_, srcID, dstID, msg)
      
  def SendMessage_(self, srcID, dstID, msg):
      # ... body of function ...
```

Logging information about when a function is entered, arguments of interest
and when it is exited.

```
  def ProcessEvent(self, itemID, typeID, quantity):
      logging.log(INFO, "ProcessEvent entered: %s %s %s" % itemID, typeID, quantity)
      
      # ... body of function ...
      
      logging.log(INFO, "ProcessEvent exited")      
```

Providing call stacks in case of unexpected occurances in order to provide
context about why they are happening.

```
  def HandleSomething(self, *args, **kwargs):
      ...
      if ... some check for unexpected circumstance ...:
          LogTraceback()
```

One downside of this approach is that if the amount of logging or the way in
which it is done is a detriment to the running of the application, the
application most likely needs to be taken down and the code updated with
the logging removed.

And another downside mentioned earlier above is that it is easy to lose track
of all the many places different information is logged throughout a code base.

### The override approach ###

An alternative approach which does not have those downsides is decoupling
the logging from the code.  Instead of writing the logging into the code, it
would be declared as belonging to a particular function and dynamically put
in place.  While it does not handle all the inline cases like where
statements are placed in specific parts of a function, it does handles most
cases which cover either replacing or being combined with the original
function.

Envisioned uses are:

  * Putting replacement versions of functions in place.
    * Perhaps to replace a broken deployed version.
  * Wrapping the calling of a function.
    * Perhaps to clock the cpu time spent in it.
    * Perhaps to log when it was entered and with what arguments.

There are other advantages over the inline approach.  Various useful
behaviours can be added to the system which places overrides and the uses
made of it can just use them naturally.  It might otherwise be considered too
much effort, overhead or impractical to incorporate these behaviours into the
inline approach.

For instance only leaving an override in place for N calls. An example use of
this is when obtaining and recording stacktraces where live code is behaving
in unexpected ways, but not to do so until someone finally gets around to
removing the inline code which does the work.  Being able to add the override
but only until it is called the first time, would take care of this.

Also being able to provide an overview of the existing overrides.  A system
which takes care of storing all the overrides can easily allow the user to see
all the overrides which are currently in place and perhaps also record why
they were put there.  It might also notify the user that overrides which had a
temporary durarion or a limited number of calls have been removed and whether
they have a result.

**Note:** The extent to which overrides are implemented in this library is that
which allows placement of overrides and also the limited duration of placement.

Given a file 'server/services/netService.py' containing the class
'Connection' where a programmer has left in a print statement and because
you're not redirecting output and it is being written to your applications
console, it is causing unwanted server load.

```
  class Connection:
      def OnIncomingData(self, ):
          ...
          print "XXX HERE", someAttribute
          ...
```

And a replacement function.

```
  def OnIncomingData(self):
      ...
      # print "XXX HERE", someAttribute
      ...
```

It can be installed in a running application by first having it made available
through your own systems, then telling your code manager to install it and
where to install it.  The 'Connection' class is in the namespace
'applib.services.Connection' so you would execute the following code.

```
  def OnIncomingData(self):
      ...
      # print "XXX HERE", someAttribute
      ...

  # cm is a reference to your code manager which you obtain from somewhere.
  cm.OverrideClassFunction("applib.services", "Connection", "OnIncomingData", OnIncomingData)
```

And from this point on while the application continues to run, the new version
of 'OnIncomingData' should be used.