from .core import BaseAnalyzer, analyzer_property

from typing import Any, Optional, Callable


class int_property (analyzer_property[int]):
    def __init__(
        self,
        client_name: Optional[str] = None,
        display_name: Optional[str] = None,
        *,
        default: int = 0,
        min: Optional[int] = None,
        max: Optional[int] = None,
        step: Optional[int] = None,
        hook: Callable[[BaseAnalyzer, Any], int] = lambda obj, x: int(x),
    ):
        super().__init__(
            client_name=client_name,
            display_name=display_name,
            default=default,
            detail={
                'type': 'int',
                'min': min,
                'max': max,
                'step': step,
            },
            hook=hook,
        )


class float_property (analyzer_property[float]):
    def __init__(
        self,
        client_name: Optional[str] = None,
        display_name: Optional[str] = None,
        *,
        default: float = 0.0,
        min: Optional[float] = None,
        max: Optional[float] = None,
        step: Optional[float] = None,
        hook: Callable[[BaseAnalyzer, Any], float] = lambda obj, x: float(x),
    ):
        super().__init__(
            client_name=client_name,
            display_name=display_name,
            default=default,
            detail={
                'type': 'float',
                'min': min,
                'max': max,
                'step': step,
            },
            hook=hook,
        )


class str_property (analyzer_property[str]):
    def __init__(
        self,
        client_name: Optional[str] = None,
        display_name: Optional[str] = None,
        *,
        default: str = '',
        hook: Callable[[BaseAnalyzer, Any], str] = lambda obj, x: str(x),
    ):
        super().__init__(
            client_name=client_name,
            display_name=display_name,
            default=default,
            detail={
                'type': 'str',
            },
            hook=hook,
        )


class bool_property (analyzer_property[bool]):
    def __init__(
        self,
        client_name: Optional[str] = None,
        display_name: Optional[str] = None,
        *,
        default: bool = False,
        hook: Callable[[BaseAnalyzer, Any], bool] = lambda obj, x: bool(x),
    ):
        super().__init__(
            client_name=client_name,
            display_name=display_name,
            default=default,
            detail={
                'type': 'bool',
            },
            hook=hook,
        )


int_ = int_property
float_ = float_property
str_ = str_property
bool_ = bool_property
