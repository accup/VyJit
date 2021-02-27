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

        info_list = list(analyzer_dict.values())
        for info in info_list:
            try:
                block_size = block.shape[0]
                # The buffer and the frame-step must be kept in variables
                # because they may be changed.
                buffer = info.buffer
                buffer_size = buffer.shape[0]
                frame_step = info.frame_step
                next_frame = info.next_frame
                for frame in range(0, block_size, frame_step):
                    required_length = frame_step - next_frame
                    length = min(required_length, block_size - frame)
                    left_length = buffer_size - length
                    buffer[:left_length] = buffer[length:]
                    buffer[left_length:] = block[block_size - length:]
                    if required_length <= length:
                        results = info.analyzer.analyze(np.copy(buffer))

                        await sio.emit(
                            'results',
                            data=numpy_to_bytes(results),
                            room=info.sid,
                        )
                        next_frame = 0
                    else:
                        next_frame += length
                info.next_frame = next_frame
            except KeyboardInterrupt:
                raise
            except Exception:
                await sio.emit(
                    'internal_error',
                    data=traceback.format_exc(),
                    room=info.sid,
                )
                await sio.disconnect(info.sid)
