import os
import sys
import logging
import types

# Temporary hack to bring in the namespace prototype.
if __name__ == "__main__":
    currentPath = sys.path[0]
    parentPath = os.path.dirname(currentPath)
    namespacePath = os.path.join(parentPath, "prototype-namespacing")
    if namespacePath not in sys.path:
        sys.path.append(namespacePath)

# ----------------------------------------------------------------------------

import namespace

MODE_OVERWRITE = 1
MODE_UPDATE = 2

class CodeReloader:
    def __init__(self, mode=MODE_OVERWRITE):
        self.mode = mode
        self.directoriesByPath = {}

        self.leakedAttributes = {}

    # ------------------------------------------------------------------------
    # Directory registration support.

    def AddDirectory(self, baseNamespace, baseDirPath):
        handler = self.directoriesByPath[baseDirPath] = ReloadableScriptDirectory(baseDirPath, baseNamespace)
        handler.Load()
        return handler

    def RemoveDirectory(self, baseDirPath):
        handler = self.directoriesByPath[baseDirPath]
        handler.Unload()

    def FindDirectory(self, filePath):
        filePathLower = filePath.lower()
        for dirPath, scriptDirectory in self.directoriesByPath.iteritems():
            if filePathLower.startswith(dirPath.lower()):
                return scriptDirectory

    # ------------------------------------------------------------------------
    # External events.

    def ProcessChangedFile(self, filePath, added=False, changed=False, deleted=False):
        scriptDirectory = self.FindDirectory(filePath)
        if scriptDirectory is None:
            logging.error("File change event for invalid path '%s'", filePath)
            return

        oldScriptFile = scriptDirectory.FindScript(filePath)
        if oldScriptFile:
            # Modified or deleted.
            if changed:
                self.ReloadScript(oldScriptFile)
            elif deleted:
                pass
        else:
            # Added.
            pass

    # ------------------------------------------------------------------------
    # Script reloading support.

    def ReloadScript(self, oldScriptFile):
        logging.info("ReloadScript")
        
        newScriptFile = self.CreateNewScript(oldScriptFile)
        if newScriptFile is None:
            return False

        self.UseNewScript(oldScriptFile, newScriptFile)

        return True

    def CreateNewScript(self, oldScriptFile):
        filePath = oldScriptFile.filePath
        namespacePath = oldScriptFile.namespacePath

        logging.info("CreateNewScript namespace='%s', file='%s'", namespacePath, filePath)

        # Read in and compile the modified script file.
        scriptDirectory = self.FindDirectory(filePath)
        newScriptFile = scriptDirectory.LoadScript(filePath, namespacePath)

        # Try and execute the new script file.
        if newScriptFile.Run():
            # Before we can go ahead and use the new version of the script file,
            # we need to verify that it is suitable for use.  That it ran without
            # error is a good start.  But we also need to verify that the
            # attributes provided by each are compatible.
            if self.ScriptCompatibilityCheck(oldScriptFile, newScriptFile):
                newScriptFile.version = oldScriptFile.version + 1
                return newScriptFile
        else:
            # The execution failed, log context for the programmer to examine.
            newScriptFile.LogLastError()

        return None

    def UseNewScript(self, oldScriptFile, newScriptFile):
        logging.info("UseNewScript")

        filePath = newScriptFile.filePath
        namespacePath = newScriptFile.namespacePath

        # The new version of the script being returned, means that it is
        # has been checked and approved for use.
        scriptDirectory = self.FindDirectory(filePath)

        # Leak the attributes the old version contributed.
        self.AddLeakedAttributes(oldScriptFile)

        # Insert the attributes from the new script file, allowing overwriting
        # of entries contributed by the old script file.
        namespace = scriptDirectory.GetNamespace(namespacePath)
        if self.mode == MODE_OVERWRITE:
            scriptDirectory.UnregisterScript(oldScriptFile)
            scriptDirectory.RegisterScript(newScriptFile)

            scriptDirectory.SetModuleAttributes(newScriptFile, namespace, overwritableAttributes=self.leakedAttributes)

            # Remove as leaks the attributes the new version contributed.
            self.RemoveLeakedAttributes(newScriptFile)
        elif self.mode == MODE_UPDATE:
            self.UpdateModuleAttributes(oldScriptFile, newScriptFile, namespace, overwritableAttributes=self.leakedAttributes)

            # Remove as leaks the attributes the new version contributed.
            self.RemoveLeakedAttributes(oldScriptFile)

    def UpdateModuleAttributes(self, oldScriptFile, newScriptFile, namespace, overwritableAttributes=set()):
        logging.info("UpdateModuleAttributes")

        moduleName = namespace.__name__
        filePath = newScriptFile.filePath
        
        # Track what files have contributed to the namespace.
        if filePath not in namespace.__file__:
            logging.error("On an update, a script file's path is expected to have already been registered")

        contributedAttributes = set()

        if False:
            for k, v, valueType in scriptFile.GetExportableAttributes():
                # By default we never overwrite.  This way we can identify duplicate contributions.
                if hasattr(namespace, k):
                    if k not in overwritableAttributes:
                        logging.error("Duplicate namespace contribution for '%s.%s' from '%s', our class = %s", moduleName, k, scriptFile.filePath, v.__file__ == scriptFile.filePath)
                        continue

                if valueType in (types.ClassType, types.TypeType):
                    pass
                elif isinstance(v, (types.UnboundMethodType, types.FunctionType, types.MethodType)):
                    if isinstance(v, types.FunctionType):
                        v = RebindFunction(v, oldLocals)
                        pass
                    elif hasattr(v, "im_func"):
                        pass

                    setattr(namespace, k, v)

                logging.info("InsertModuleAttribute %s.%s", moduleName, k)

                pass

                contributedAttributes.add(k)

        oldScriptFile.SetContributedAttributes(contributedAttributes)

    # ------------------------------------------------------------------------
    # Leaked attribute support

    def IsAttributeLeaked(self, attributeName):
        return attributeName in self.leakedAttributes

    def GetLeakedAttributeVersion(self, attributeName):
        return self.leakedAttributes[attributeName][1]

    def AddLeakedAttributes(self, oldScriptFile):
        filePath = oldScriptFile.filePath
    
        for attributeName in oldScriptFile.contributedAttributes:
            self.leakedAttributes[attributeName] = (filePath, oldScriptFile.version)

    def RemoveLeakedAttributes(self, newScriptFile):
        for attributeName in newScriptFile.contributedAttributes:
            if attributeName in self.leakedAttributes:
                del self.leakedAttributes[attributeName]

    # ------------------------------------------------------------------------
    # Attribute compatibility support

    def ScriptCompatibilityCheck(self, oldScriptFile, newScriptFile):
        logging.info("ScriptCompatibilityCheck '%s'", oldScriptFile.filePath)

        # Do not allow replacement of old contributions, whether from the old
        # script file given, or contributions it has inherited itself, if the
        # new contributions are not compatible.
        pass
        # Overwrite:
        # - Different types.
        # Update:
        # - Change from old style class to new style class.
        return True


# TODO: Determine if these are really necessary any more?

class ReloadableScriptFile(namespace.ScriptFile):
    version = 1


class ReloadableScriptDirectory(namespace.ScriptDirectory):
    scriptFileClass = ReloadableScriptFile

