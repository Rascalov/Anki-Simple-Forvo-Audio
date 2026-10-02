import pathlib
import sys
import types

"""
Makes the add-on importable as a package without running __init__.py.

The repository directory *is* the add-on package, but its name contains
hyphens and its __init__.py imports aqt. Registering a synthetic package that
points at the directory lets the pure modules be imported by their relative
names with no Anki present.
"""

PACKAGE = "forvo_addon"
ROOT = pathlib.Path(__file__).resolve().parent.parent

if PACKAGE not in sys.modules:
    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(ROOT)]
    sys.modules[PACKAGE] = package
