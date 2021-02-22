import numpy as np

from typing import Union, Tuple, List, Dict


ConvertibleType = Union[
    int, float, str, bytes, np.ndarray,
    np.int8, np.uint8, np.int16, np.uint16,
    np.int32, np.uint32, np.float32, np.float64,
    Tuple['ConvertibleType'], List['ConvertibleType'],
    Dict[str, 'ConvertibleType'],
]
PortableType = Union[
    int, float, str, bytes,
    Tuple['PortableType'], List['PortableType'],
    Dict[str, 'PortableType'],
]


DTYPE_JSTYPE_MAP = {
    np.dtype(np.int8): 'int8',
    np.dtype(np.uint8): 'uint8',
    np.dtype(np.int16): 'int16',
    np.dtype(np.uint16): 'uint16',
    np.dtype(np.int32): 'int32',
    np.dtype(np.uint32): 'uint32',
    np.dtype(np.float32): 'float32',
    np.dtype(np.float64): 'float64',
}
JSTYPE_DTYPE_MAP = {
    value: key
    for key, value in DTYPE_JSTYPE_MAP.items()
}


def numpy_to_bytes(data: ConvertibleType) -> PortableType:
    """Convert contained numpy array to data-type info and bytes.
    """
    if isinstance(data, dict):
        if '_dtype' in data:
            raise ValueError("'_dtype' is an illegal key.")

        return {
            key: numpy_to_bytes(value)
            for key, value in data.items()
        }
    elif isinstance(data, tuple):
        return tuple(
            numpy_to_bytes(value)
            for value in data
        )
    elif isinstance(data, list):
        return [
            numpy_to_bytes(value)
            for value in data
        ]
    elif isinstance(data, np.ndarray):
        if len(data.shape) != 1:
            raise ValueError(
                "Multi-dimensional numpy array is not convertible."
            )
        jstype = DTYPE_JSTYPE_MAP[data.dtype]
        data = data.astype(data.dtype.newbyteorder('>'))
        return {
            '_dtype': jstype,
            '_buffer': data.tobytes(),
        }
    elif isinstance(data, (int, float, str)):
        return data
    else:
        return data.item()


def bytes_to_numpy(data: PortableType) -> ConvertibleType:
    """Convert contained data-type info and bytes to numpy array.
    """
    if isinstance(data, dict):
        if '_dtype' in data:
            dtype = JSTYPE_DTYPE_MAP[data['_dtype']]
            data = np.frombuffer(
                data['_buffer'],
                dtype=dtype.newbyteorder('>'),
            )
            data = data.astype(dtype)
            return data
        else:
            return {
                key: bytes_to_numpy(value)
                for key, value in data.items()
            }
    elif isinstance(data, tuple):
        return tuple(
            bytes_to_numpy(value)
            for value in data
        )
    elif isinstance(data, list):
        return [
            bytes_to_numpy(value)
            for value in data
        ]
    else:
        return data
