from importlib import import_module
from pkgutil import walk_packages
from inspect import stack, getmodule


def import_submodules():
    caller_package = getmodule(stack()[1][0])
    submodules = dict()
    for _, name, _ in walk_packages(caller_package.__path__):
        submodules[name] = import_module(
            name='.' + name,
            package=caller_package.__package__,
        )
    return submodules
