from pkgutil import walk_packages, ModuleType
from inspect import stack, getmodule


def list_submodules(package: ModuleType):
    package = getmodule(stack()[1][0])
    return [name for _, name, _ in walk_packages(package.__path__)]
