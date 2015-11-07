In order to bring Python scripts under the management of the custom module system this library provides, a `CodeReloader` object needs to be created, and the top level directories the scripts are within registered with it.

The following examples illustrates how this is done for a selection of different use cases.

### Example 1: One file in a subdirectory ###

**Note:** Modules become available for importing through directory contents
being registered with this library.  And how the contents of those directories
are made available for importing differs from the standard Python module way.

Let's say you have a directory 'stuff' and the following subdirectory and
file are in there:

```
  stuff/services/net.py
```

And net.py has the following class defined inside it:

```
  NetService
```

You might register the contents of the 'stuff' directory under the base
namespace 'server' in this manner:

```
  from livecoding import reloader
  cr = reloader.CodeReloader()
  cr.AddDirectory("server", "stuff")
```

Now this will result in a 'services' submodule for 'server' and the contents
of the Python scripts in the corresponding 'services' directory will be placed
in this submodule.

Then it is now possible to do the following:

```
  import server
  from server import services
  from server.services import NetService
```

### Example 2: Two files in a subdirectory ###

**Note:** Modules directly map to directory structure which means that the
contents of all python scripts within a given directory are placed in the
module for that directory.

Let's say you have a directory 'stuff' and the following subdirectory and
files are in there:

```
  stuff/services/net.py
  stuff/services/data.py
```

And net.py has the following class defined inside it:

```
  NetService
```

And data.py has the following class defined inside it:

```
  DataService
```

Now registering the directory in the same manner as the first example, it
is possible to do the following:

```
  import server
  from server import services
  from server.services import NetService
  from server.services import DataService
```

### Example 3: Directory contents can be merged into a namespace ###

**Note:** By registering two directories under the same base namespace
the contents get merged into the corresponding modules which are created.

Let's say you have a directory 'stuff1' and the following subdirectory and
file are in there:

```
  stuff1/services/net.py
```

But you also have a directory 'stuff2' with a matching subdirectory and
a different file:

```
  stuff2/services/data.py
```

These files provide the same classes as in the previous example.  Next both
'stuff1' and 'stuff2' are registered under the same base namespace:

```
  from livecoding import reloader
  cr = reloader.CodeReloader()
  cr.AddDirectory("server", "stuff1")
  cr.AddDirectory("server", "stuff2")
```

And it is still possible to do the following:

```
  from server.services import NetService
  from server.services import DataService
```