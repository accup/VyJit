import numpy as np
import sounddevice as sd

import socketio

import threading
import asyncio
import traceback

from _lib.util import numpy_to_bytes

from typing import Union, Optional, Callable, Awaitable, AsyncIterable


async def signal_input(
    loop: asyncio.AbstractEventLoop,
    event: asyncio.Event,
    put_buffer: Callable[[np.ndarray], Awaitable[None]],
    sample_rate: float,
    channels: int,
    window_size: int,
    block_size: int = 0,
    device: Optional[Union[int, str]] = None,
    dtype: np.dtype = np.float32,
):
    buffer = np.zeros((window_size, channels), dtype=dtype)
    buffer_lock = threading.Lock()

    def callback(indata: np.ndarray, frames, time, status):
        with buffer_lock:
            length = min(buffer.shape[0], indata.shape[0])
            left_length = buffer.shape[0] - length
            buffer[:left_length, :] = buffer[length:, :]
            buffer[left_length:, :] = indata[indata.shape[0] - length:, :]

            asyncio.run_coroutine_threadsafe(
                put_buffer(np.copy(buffer)),
                loop=loop,
            )

    with sd.InputStream(
        samplerate=sample_rate,
        blocksize=block_size,
        device=device,
        channels=channels,
        dtype=dtype,
        callback=callback,
    ):
        await event.wait()


async def signal_analysis(
    sio: socketio.AsyncServer,
    get_buffer: Callable[[], Awaitable[Union[None, np.ndarray]]],
    get_sid_results_pairs: Callable[[], AsyncIterable],
):
    while True:
        buffer = await get_buffer()
        if buffer is None:
            break

        try:
            async for sid, results in get_sid_results_pairs(buffer):
                await sio.emit(
                    'results',
                    data=numpy_to_bytes(results),
                    room=sid,
                )
        except KeyboardInterrupt:
            raise
        except Exception:
            await sio.emit(
                'internal_error',
                data=traceback.format_exc(),
                room=sid,
            )
            await sio.disconnect(sid)
