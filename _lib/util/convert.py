import numpy as np


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


def numpy_to_bytes(data):
    """Convert contained numpy array to data-type info and bytes.

    This function modifies a given object.
    """
    if isinstance(data, dict):
        if '__dtype' in data:
            raise ValueError("'__dtype' is an illegal key.")
        for key, value in data.items():
            data[key] = numpy_to_bytes(value)
        return data
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = numpy_to_bytes(data[i])
        return data
    elif isinstance(data, np.ndarray):
        if len(data.shape) != 1:
            raise ValueError(
                "Multi-dimensional numpy array is not convertible."
            )
        jstype = DTYPE_JSTYPE_MAP[data.dtype]
        data = data.astype(data.dtype.newbyteorder('>'))
        return {
            '__dtype': jstype,
            '__bytes': data.tobytes(),
        }
    else:
        return data


def bytes_to_numpy(data):
    """Convert contained data-type info and bytes to numpy array.

    This function modifies a given object.
    """
    if isinstance(data, dict):
        if '__dtype' in data:
            dtype = JSTYPE_DTYPE_MAP[data['__dtype']]
            data = np.frombuffer(
                data['__bytes'],
                dtype=dtype.newbyteorder('>'),
            )
            data = data.astype(dtype)
            return data
        else:
            for key, value in data.items():
                data[key] = bytes_to_numpy(value)
            return data
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = bytes_to_numpy(data[i])
        return data
    else:
        return data
