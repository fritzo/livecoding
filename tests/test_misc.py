from __future__ import with_statement
import livecoding, support
import types, sys, os, unittest, weakref, __builtin__, copy

aFileName = os.path.join("A", "a.py")
a2FileName = os.path.join("A", "a2.py")
bFileName = os.path.join("B", os.path.join("C", "b.py"))

aContentsBase = """
class ClassA:
    var = 1
    def FunctionA(self):
        return "a1"
"""

aContentsBaseType = """
class ClassA(type):
    var = 1
    def FunctionA(self):
        return "a1"
"""

aContentsBaseObject = """
class ClassA(object):
    var = 1
    def FunctionA(self):
        return "a1"
"""

aContentsBaseTypeClassVariableRemoval = """
class ClassA(type):
    def FunctionA(self):
        return "a1"
"""

aContentsClassVariableRemoval = """
class ClassA:
    def FunctionA(self):
        return "a1"
"""

aContentsFunctionChange = """
class ClassA:
    var = 1
    def FunctionA(self):
        return "a2"
"""

a2ContentsBase = """
class ClassA2:
    def FunctionA2(self):
        return "a2"
"""

bContentsBase = """
from base import ClassA
class ClassB(ClassA):
    def FunctionB(self):
        return "b1"
"""

d1 = {
    "A": {
        "a.py": aContentsBase,
    },
    "B": {
        "C": {
            "b.py": bContentsBase,
        },
    },
}

def GetDirectoryStructure():
    return copy.deepcopy(d1)

class SupportTestCase(unittest.TestCase):
    def test_monkeypatching(self):
        # Verify that the monkeypatcher leaves things as they were before
        # it replaced them.  Given that it automatically detects what to
        # replace where, it should be sufficient to check this one.
        self.failUnless(isinstance(os.listdir, types.BuiltinFunctionType))
        with support.MonkeyPatcher() as mp:
            self.failUnless(not isinstance(os.listdir, types.BuiltinFunctionType))
        self.failUnless(isinstance(os.listdir, types.BuiltinFunctionType))

class ImportTestCase(unittest.TestCase):
    def test_importing(self):
        with support.MonkeyPatcher() as mp:
            mp.SetDirectoryStructure(GetDirectoryStructure())

            cm = livecoding.CodeManager()
            cm.AddDirectory("A", "base")

            from base import ClassA
            a = ClassA()
            self.failUnlessEqual(a.FunctionA(), "a1")

    def test_subclassing_dependencies(self):
        with support.MonkeyPatcher() as mp:
            mp.SetDirectoryStructure(GetDirectoryStructure())

            cm = livecoding.CodeManager()
            cm.AddDirectory("A", "base")
            cm.AddDirectory("B", "base")

            from base import ClassA
            from base.C import ClassB
            a, b = ClassA(), ClassB()
            self.failUnlessEqual(a.FunctionA(), b.FunctionA())

    def test_directory_removal(self):
        with support.MonkeyPatcher() as mp:
            mp.SetDirectoryStructure(GetDirectoryStructure())

            cm = livecoding.CodeManager()
            cm.AddDirectory("A", "base")
            cm.AddDirectory("B", "base")
            cm.RemoveDirectory("B")

            try:
                from base import C
                self.fail("namespace entry 'C' still available")
            except ImportError:
                pass

            cm.RemoveDirectory("A")

            try:
                import base
                self.fail("namespace entry 'base' still available")
            except ImportError:
                pass

    def test_garbage_collection(self):
        """ It is an expectation that when all known references to the code
            manager are released, then the code manager will be released itself. """
        with support.MonkeyPatcher() as mp:
            mp.SetDirectoryStructure(GetDirectoryStructure())

            cm = livecoding.CodeManager()
            cm.AddDirectory("A", "base")

        cmProxy = weakref.ref(cm)
        del cm
        # At this point the code manager will have been cleaned up.
        self.failUnless(cmProxy() is None)

class UpdateTestCase(unittest.TestCase):
    def test_file_update(self):
        with support.MonkeyPatcher() as mp:
            mp.SetDirectoryStructure(GetDirectoryStructure())

            cm = livecoding.CodeManager()
            cm.AddDirectory("A", "base")
            cm.AddDirectory("B", "base")

            mp.SetFileContents(aFileName, aContentsFunctionChange)

            cm.ProcessChangedFile(aFileName, changed=True)

            from base.C import ClassB
            b = ClassB()
            self.failUnlessEqual(b.FunctionA(), "a2")

    def test_file_update_inheritance_change(self):
        with support.MonkeyPatcher() as mp:
            mp.SetDirectoryStructure(GetDirectoryStructure())
            # 'ClassA' starts inherited from 'object' 
            mp.SetFileContents(aFileName, aContentsBaseObject)

            cm = livecoding.CodeManager()
            cm.AddDirectory("A", "base")
            cm.AddDirectory("B", "base")

            # 'ClassA' has changed to no longer be inherited from 'object'.
            mp.SetFileContents(aFileName, aContentsBase)

            cm.ProcessChangedFile(aFileName, changed=True)

            from base.C import ClassB
            b = ClassB()
            import sys
            sys.stderr.write(str(ClassB) +" "+ str(hasattr(ClassB, "__class__")))
            # self.failUnlessEqual(b.FunctionA(), "a2")

    def test_file_update_class_variable_removal(self):
        with support.MonkeyPatcher() as mp:
            mp.SetDirectoryStructure(GetDirectoryStructure())

            cm = livecoding.CodeManager()
            cm.AddDirectory("A", "base")
            cm.AddDirectory("B", "base")

            from base import ClassA
            from base.C import ClassB

            self.failUnless(hasattr(ClassA, "var"), "Variable on ClassA was not removed")
            self.failUnless(hasattr(ClassB, "var"), "Variable on ClassB (via ClassA) was not removed")

            mp.SetFileContents(aFileName, aContentsClassVariableRemoval)

            cm.ProcessChangedFile(aFileName, changed=True)

            self.failUnless(not hasattr(ClassA, "var"), "Variable on ClassA was not removed")
            self.failUnless(not hasattr(ClassB, "var"), "Variable on ClassB (via super class 'ClassA') was not removed")

    def test_file_update_type_class_variable_removal(self):
        with support.MonkeyPatcher() as mp:
            mp.SetDirectoryStructure(GetDirectoryStructure())
            # Substitute a ClassA which inherits from 'type'.
            mp.SetFileContents(aFileName, aContentsBaseType)

            cm = livecoding.CodeManager()
            cm.AddDirectory("A", "base")
            cm.AddDirectory("B", "base")

            from base import ClassA
            from base.C import ClassB

            self.failUnless(hasattr(ClassA, "var"), "Variable on ClassA was not removed")
            self.failUnless(hasattr(ClassB, "var"), "Variable on ClassB (via ClassA) was not removed")

            # Substitute a ClassA which inherits from 'type' without the variable 'var'.
            mp.SetFileContents(aFileName, aContentsBaseTypeClassVariableRemoval)

            cm.ProcessChangedFile(aFileName, changed=True)

            self.failUnless(not hasattr(ClassA, "var"), "Variable on ClassA was not removed")
            self.failUnless(not hasattr(ClassB, "var"), "Variable on ClassB (via super class 'ClassA') was not removed")

    def test_file_addition_bad(self):
        with support.MonkeyPatcher() as mp:
            mp.SetDirectoryStructure(GetDirectoryStructure())

            cm = livecoding.CodeManager()
            cm.AddDirectory("A", "base")

            try:
                cm.ProcessChangedFile(bFileName)
                self.fail("did not expect to handle file change for unhandled directory")
            except RuntimeError:
                pass

    def test_file_addition_good(self):
        with support.MonkeyPatcher() as mp:
            mp.SetDirectoryStructure(GetDirectoryStructure())
            cm = livecoding.CodeManager()
            cm.AddDirectory("A", "base")

            mp.SetFileContents(a2FileName, a2ContentsBase)

            cm.ProcessChangedFile(a2FileName)

            try:
                from base import ClassA2
            except ImportError:
                self.fail("newly added file was not correctly added to the namespace")

    def test_file_removal(self):
        with support.MonkeyPatcher() as mp:
            mp.SetDirectoryStructure(GetDirectoryStructure())
            cm = livecoding.CodeManager()
            cm.AddDirectory("A", "base")

            # Add the file 'a2.py'.
            mp.SetFileContents(a2FileName, a2ContentsBase)

            # Prod the code manager to use it.
            cm.ProcessChangedFile(a2FileName)

            # Remove the file 'a2.py'.
            mp.RemoveDirectoryEntry(a2FileName)

            # Prod the code manager to remove it.
            cm.ProcessChangedFile(a2FileName)

            # We are checking that what the file contributed is still there.
            try:
                from base import ClassA2
            except ImportError:
                self.fail("...")

