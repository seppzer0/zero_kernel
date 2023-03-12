import os
import glob
import shutil
import customcmd as ccmd


def remove(elements, allow_errors: bool = False):
    """An ultimate analog to 'rm -rf'."""
    # if a given argument is a string --> convert it into a one-element list
    if isinstance(elements, str):
        elements = [elements]
    for e in elements:
        # a simple list-through removal
        if "*" not in e:
            if os.path.isdir(e):
                shutil.rmtree(e, ignore_errors=allow_errors)
            elif os.path.isfile(e):
                os.remove(e)
        # a recursive "glob" removal
        else:
            for fn in glob.glob(e):
                remove(fn)


def git(directory):
    """Clean up git directories."""
    goback = os.getcwd()
    os.chdir(directory)
    cmd = "git clean -fdx && git reset --hard HEAD"
    ccmd.launch(cmd)
    os.chdir(goback)


def root(extra=[]):
    """
    Fully clean the root directory.
    NOTE: .vscode is not cleaned, __pycache__ --> via py3clean
    """
    trsh = ["android_*",
            "clang*",
            "AnyKernel3",
            "rtl8812au",
            "source",
            "kernel",
            "localversion",
            "assets",
            "release-light",
            "conanfile.py"]
    # add extra elements to clean up from root directory
    if extra:
        for e in extra:
            trsh.append(e)
    # clean
    remove(trsh, allow_errors=True)
    ccmd.launch("py3clean .")
