import numpy as np

from ..util.convert import ConvertibleType
from typing import Any, Optional, Iterable, Callable, Tuple, List, Dict


GLOBAL_GROUP = ''


class analyzer_property:
    def __init__(
        self,
        client_name: Optional[str] = None,
        *,
        default,
        detail: Optional[Dict[str, ConvertibleType]] = None,
        hook: Callable[['BaseAnalyzer', Any], Any] = lambda obj, x: x,
    ):
        self.client_name = client_name
        self.default_value = default
        self.hook = hook
        self.detail = {} if detail is None else detail
        self.compute_callbacks: List[
            Callable[['BaseAnalyzer'], Any]
        ] = []
        self.validate_callbacks: List[
            [Callable[['BaseAnalyzer', Any], bool]]
        ] = []

        self.detail['group'] = GLOBAL_GROUP

    def __set_name__(self, owner, name: str):
        if self.client_name is None:
            self.client_name = name
        self.name = name

    def __get__(self, instance: 'BaseAnalyzer', owner=None):
        if instance is None:
            return self

        if self.name in instance.__dict__:
            return instance.__dict__[self.name]['value']
        else:
            return self.default_value

    def __set__(self, instance: 'BaseAnalyzer', value):
        if self.name not in instance.__dict__:
            instance.__dict__[self.name] = {
                'value': self.default_value,
                'updating': False
            }
        value_dict = instance.__dict__[self.name]
        if value_dict['updating']:
            raise RuntimeError(
                "Recursive update detected in the property {self.name!r}."
            )
        if all(check(instance, value) for check in self.validate_callbacks):
            value_dict['updating'] = True
            value_dict['value'] = self.hook(instance, value)
            for callback in self.compute_callbacks:
                callback(instance)
            value_dict['updating'] = False

    def __call__(self, hook: Callable[['BaseAnalyzer', Any], Any]):
        old_hook = self.hook
        self.hook = lambda obj, x: hook(obj, old_hook(obj, x))
        return self

    def compute(self, callback: Callable[['BaseAnalyzer'], Any]):
        self.compute_callbacks.append(callback)
        return callback

    def validate(self, callback: Callable[['BaseAnalyzer', Any], bool]):
        self.validate_callbacks.append(callback)
        return callback


class AnalyzerMeta (type):
    def __init__(
        cls,
        name: str,
        bases: Tuple['AnalyzerMeta', ...],
        namespace: Dict[str, Any],
    ):
        super().__init__(name, bases, namespace)

        cls._properties: Dict[str, str] = dict()

        for base in bases:
            cls._properties.update(base._properties)

        for name, value in namespace.items():
            if isinstance(value, analyzer_property):
                cls._properties[value.client_name] = value.name

        global GLOBAL_GROUP
        GLOBAL_GROUP = ''


class BaseAnalyzer (metaclass=AnalyzerMeta):
    def analyze(self, signal: np.ndarray):
        raise NotImplementedError

    def get_client_properties(
        self,
        client_names: Optional[Iterable[str]] = None,
    ):
        if client_names is None:
            client_names = type(self)._properties.keys()

        return {
            client_name: getattr(
                self,
                type(self)._properties[client_name],
            )
            for client_name in client_names
        }

    def get_client_property_details(
        self,
        client_names: Optional[Iterable[str]] = None,
    ):
        if client_names is None:
            client_names = type(self)._properties.keys()

        return {
            client_name: {
                'value': getattr(
                    self,
                    type(self)._properties[client_name],
                ),
                'detail': getattr(
                    type(self),
                    type(self)._properties[client_name],
                ).detail,
            }
            for client_name in client_names
        }


def group(name: str):
    global GLOBAL_GROUP
    GLOBAL_GROUP = str(name)
