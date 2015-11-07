## Overview ##

There are two key facets this library:

  * The code reloading functionality it provides.
  * The bypassing of the standard [module system](http://docs.python.org/tutorial/modules.html) with a custom one.

The standard module system is still there and continues to work with the custom one, but only the custom one is covered by the code reloading functionality of this library.

In order to decide whether you want the flexibility of the code reloading which this library provides, you need to decide whether you can live with writing the reloadable scripts within the custom module system.

## The Benefits of Code Reloading ##

  * Automatic code reloading on script file changes.
  * Less interruptions to developer workflow.

Code reloading allows a running application to change its behaviour in response to changes in the Python scripts it uses.  When the library detects a Python script has been modified, it reloads that script and replaces the objects it had previously made available for use with newly reloaded versions.

As a tool, it allows a programmer to avoid interruption to their workflow and a corresponding loss of focus.  It enables them to remain in a [state of flow](http://en.wikipedia.org/wiki/Flow_(psychology)).  Where previously they might have needed to restart the application in order to put changed code into effect, those changes can be applied immediately.

## The Custom Module System ##

**Q.** What is a custom module system?

> When you import a module, Python looks within its library paths for a
> file or [directory](http://docs.python.org/tutorial/modules.html#packages) matching
> the given module name.  This works according to specific rules and provides a
> very flexible way of building libraries of code.

> After a module is imported for the first time, it is then cached and subsequent
> attempts to import it receive the cached version.

> A custom module system bypasses this process and takes care of creating the
> modules, placing them in the cache itself.  Any attempt to import the modules
> then gets the custom versions.

**Q.** Are standard modules still importable?

> Yes.

> The custom module system places its modules in the cache.  Any attempt to
> import a module which is not in the cache will follow the standard importing
> process as before.  The custom system operates as a layer that builds on top
> of the standard one.

**Q.** Are scripts within the custom module system independent?

> There would be no point in each script being isolated, with no ability to share what it provides with other scripts managed by the same system.  The loading of scripts under a given script directory is coordinated in such a way that importing what another script provides just works.

> `directory/x/scriptA.py` may export the object `namespace.x.Something`, and if `directory/scriptB.py` subclasses it, the loading process will detect it and load the scripts in the correct order for dependencies to just work.

> This is simple to verify.  Create a script directory, add two scripts which each declare a class.  Have one script import the class from the other and have its class subclass the imported on.  As long as there are no circular dependencies, the scripts will load and both classes will be available as defined.

**Q.** Why use a custom module system?

> There are many different reasons.  A developer might choose to use one for any
> number of the following.

  * It's the easiest way to get automatic code reloading.

> The simplest reason would be that a developer wants the benefits of automatic code
> reloading, but does not know how to get this working with the standard
> library reloading functionality.  This is not a good reason to choose to use
> this framework.  The advantages of sticking with standard library functionality
> are huge, and to give them up just to get automatic code reloading, may not
> be in the best interests of the developer.

  * Avoiding the standard module system.

> The Python module system provides a useful structure, which the import system
> can use to identify modules to allow the importing of.  But packaging modules
> in this way can inhibit a developer.

> Working without the package system can allow a developer to concentrate on the
> code and avoid having their workflow impacted by the need to work within the
> packaging system.

  * Preloading modules.

> With the standard module system, a module may be imported for the first time
> at any time during the life of the application.  If the module blocks when this
> happens, then this can affect the performance of the application.  If the application
> has a visualisation aspect, like a computer game, then this may stutter as a result.

> This framework preloads all the scripts registered with it, meaning that any
> attempt to import a module will always obtain a preloaded cached module.

  * Getting code validation before an application runs.

> As mentioned above, with the standard module system, a module may be imported for
> the first time any time during the life of the application.  If the module is
> broken and an error occurs when it is imported, then the time spent running the
> application to this point is potentially wasted.

> The preloading that this library does, highlights errors in script files modified
> when the application was not running immediately when it is next run.

> In addition, when the library reloads script files, the contributions of the
> original version of the script file stay in place until it is next loaded
> without error, and with passing unit tests.  This prevents broken code, both
> completely unimportable and also functionally incorrect according to the unit
> tests, from being put in place.

**Q.** Can you tell me more about the standard library reloading functionality?

> For many years, Python has provided a way to reload modules that (kind of) works with
> its standard module system.

> _Python 3.0:_ The [reload](http://docs.python.org/3.0/library/imp.html#imp.reload) function in the [imp module](http://docs.python.org/3.0/library/imp.html).

> _Earlier versions:_ The [reload](http://docs.python.org/2.6/library/functions.html#reload) built-in.

> At some later stage when time becomes available, this page may provide detail
> describing the different purpose Python's reloading functionality serves.  For
> now, it is up to the reader to decide.