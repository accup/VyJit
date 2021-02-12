from importlib import import_module
from pkgutil import walk_packages
from inspect import stack, getmodule


def import_submodules():
    caller_package = getmodule(stack()[1][0])
    name_list = []
    for _, name, _ in walk_packages(caller_package.__path__):
        import_module('.' + name, caller_package.__package__)
        name_list.append(name)
    return name_list
