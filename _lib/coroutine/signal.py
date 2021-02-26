import numpy as np
import sounddevice as sd

import socketio

import asyncio
import traceback

from _lib.util import numpy_to_bytes

from .core import AnalyzerInfo

from typing import Union, Optional, Callable, Awaitable, Dict


async def signal_input(
    loop: asyncio.AbstractEventLoop,
    event: asyncio.Event,
    put_block: Callable[[np.ndarray], None],
    sample_rate: float,
    channels: int,
    block_size: int = 0,
    device: Optional[Union[int, str]] = None,
    dtype: np.dtype = np.float32,
):
    def callback(indata: np.ndarray, frames, time, status):
        loop.call_soon_threadsafe(put_block, indata.copy())

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
    analyzer_dict: Dict[str, AnalyzerInfo],
    get_block: Callable[[], Awaitable[Union[None, np.ndarray]]],
):
    while True:
        block = await get_block()
        if block is None:
            break

        for info in analyzer_dict.values():
            try:
                length = min(info.buffer.shape[0], block.shape[0])
                left_length = info.buffer.shape[0] - length
                info.buffer[:left_length] = info.buffer[length:]
                info.buffer[left_length:] = block[block.shape[0] - length:]

                results = info.analyzer.analyze(np.copy(info.buffer))

                await sio.emit(
                    'results',
                    data=numpy_to_bytes(results),
                    room=info.sid,
                )
            except KeyboardInterrupt:
                raise
            except Exception:
                await sio.emit(
                    'internal_error',
                    data=traceback.format_exc(),
                    room=info.sid,
                )
                await sio.disconnect(info.sid)
