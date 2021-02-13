from _lib.util.submodule import import_submodules

SUBMODULES = import_submodules()

__all__ = [
    'SUBMODULES',
    *SUBMODULES.keys(),
]

del import_submodules
