import abc
import numpy as np

from ..util.convert import ConvertibleType
from typing import (Any, Callable, Dict, Generic, Iterable, List, Optional,
                    Tuple, Type, TypeVar, overload)


T = TypeVar('T')
U = TypeVar('U')


GLOBAL_GROUP = ''


class analyzer_property (Generic[T]):
    def __init__(
        self,
        client_name: Optional[str] = None,
        display_name: Optional[str] = None,
        *,
        default: T,
        detail: Optional[Dict[str, ConvertibleType]] = None,
        hook: Callable[['BaseAnalyzer', Any], Any] = lambda obj, x: x,
    ):
        self.client_name = client_name
        self.display_name = display_name
        self.default_value = default
        self.hook = hook
        self.detail = {} if detail is None else detail
        self.compute_callbacks: List[Callable[['BaseAnalyzer'], Any]] = []
        self.validate_callbacks: List[Callable[['BaseAnalyzer', T], bool]] = []

        self.detail['group'] = GLOBAL_GROUP

    def __set_name__(self, owner, name: str):
        if self.client_name is None:
            self.client_name = name
        if self.display_name is None:
            self.display_name = self.client_name
        self.name = name
        self.detail['display_name'] = self.display_name

    @overload
    def __get__(
        self,
        instance: None,
        owner=None,
    ) -> 'Type[analyzer_property[T]]':
        ...

    @overload
    def __get__(
        self,
        instance: 'BaseAnalyzer',
        owner=None,
    ) -> T:
        ...

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        if self.name in instance.__dict__:
            value: T = instance.__dict__[self.name]['value']
        else:
            value = self.default_value
        return value

    def __set__(self, instance: 'BaseAnalyzer', value: T):
        if self.name not in instance.__dict__:
            instance.__dict__[self.name] = {
                'value': self.default_value,
                'updating': False
            }
        value_dict = instance.__dict__[self.name]
        if value_dict['updating']:
            raise RuntimeError("Recursive update detected in the property "
                               "{!r}.".format(self.name))
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

    def compute(
        self,
        callback: Callable[['BaseAnalyzer'], U],
    ) -> Callable[['BaseAnalyzer'], U]:
        self.compute_callbacks.append(callback)
        return callback

    def validate(
        self,
        callback: Callable[['BaseAnalyzer', T], bool],
    ) -> Callable[['BaseAnalyzer', T], bool]:
        self.validate_callbacks.append(callback)
        return callback


class AnalyzerMeta (abc.ABCMeta):
    def __init__(
        cls,
        name: str,
        bases: Tuple['AnalyzerMeta', ...],
        namespace: Dict[str, Any],
    ):
        super().__init__(name, bases, namespace)

        cls._analyzer_properties: Dict[str, str] = dict()

        for base in bases:
            if not isinstance(base, AnalyzerMeta):
                raise TypeError("The base class of the analyzer class "
                                "must be an analyzer class.")
            cls._analyzer_properties.update(base._analyzer_properties)

        for key, value in namespace.items():
            if isinstance(value, analyzer_property) and \
                    value.client_name is not None:
                cls._analyzer_properties[value.client_name] = key

        global GLOBAL_GROUP
        GLOBAL_GROUP = ''


class BaseAnalyzer (metaclass=AnalyzerMeta):
    def analyze(self, signal: np.ndarray):
        raise NotImplementedError

    def get_property_name(self, client_name: str):
        return type(self)._analyzer_properties[client_name]

    def get_client_properties(
        self,
        client_names: Optional[Iterable[str]] = None,
    ):
        if client_names is None:
            client_names = type(self)._analyzer_properties.keys()

        return {
            client_name: getattr(self, self.get_property_name(client_name))
            for client_name in client_names
        }

    def get_client_property_details(
        self,
        client_names: Optional[Iterable[str]] = None,
    ):
        if client_names is None:
            client_names = type(self)._analyzer_properties.keys()

        return {
            client_name: {
                'value': getattr(
                    self,
                    self.get_property_name(client_name),
                ),
                'detail': getattr(
                    type(self),
                    self.get_property_name(client_name),
                ).detail,
            }
            for client_name in client_names
        }


def group(name: str):
    global GLOBAL_GROUP
    GLOBAL_GROUP = str(name)
