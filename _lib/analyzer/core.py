import numpy as np

from typing import Any, Optional, Iterable, Tuple, Dict


class analyzer_property:
    def __init__(
        self,
        client_name: Optional[str] = None,
        *,
        default,
        validate=lambda obj, x: True,
    ):
        self.client_name = client_name
        self.default_value = default
        self.validate = validate

    def __set_name__(self, owner, name: str):
        if self.client_name is None:
            self.client_name = name
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        return instance.__dict__.setdefault(self.name, self.default_value)

    def __set__(self, instance, value):
        if self.validate(instance, value):
            instance.__dict__[self.name] = value

    def __call__(self, validate):
        self.validate = validate
        return self


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


class BaseAnalyzer (metaclass=AnalyzerMeta):
    def analyze(self, signal: np.ndarray, sample_rate: float):
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
