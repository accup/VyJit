import numpy as np

import socketio
from aiohttp import web
import jinja2
import aiohttp_jinja2

import asyncio
import importlib
import traceback

from _lib.analyzer import analyzer_property
from .signal import signal_input, signal_analysis

from .core import AnalyzerInfo

from typing import Dict, Awaitable


def register_handlers(  # noqa: C901
    sio: socketio.AsyncServer,
    analyzer_dict: Dict[str, AnalyzerInfo],
    sample_rate: int,
    channels: int,
    default_window_size: int,
    default_frame_step: int,
    dtype: np.dtype = np.float32,
):
    async def on_start_analysis(sid: str, name: str):
        analyzer_module_name = 'analyzers.{}'.format(name)
        try:
            analyzer_module = importlib.import_module(analyzer_module_name)
            analyzer_class = analyzer_module.Analyzer
            if hasattr(analyzer_class, 'sample_rate'):
                prop = analyzer_class.sample_rate
                if isinstance(prop, analyzer_property):
                    prop.default_value = sample_rate
                    prop.detail['readonly'] = True
            if hasattr(analyzer_class, 'channels'):
                prop = analyzer_class.channels
                if isinstance(prop, analyzer_property):
                    prop.default_value = channels
                    prop.detail['readonly'] = True
            if hasattr(analyzer_class, 'window_size'):
                prop = analyzer_class.window_size
                if isinstance(prop, analyzer_property):
                    prop.default_value = default_window_size
            if hasattr(analyzer_class, 'frame_step'):
                prop = analyzer_class.frame_step
                if isinstance(prop, analyzer_property):
                    prop.default_value = default_frame_step

            analyzer = analyzer_class()
            data = analyzer.get_client_property_details()

            analyzer_info = AnalyzerInfo(
                sid,
                analyzer,
                np.zeros((default_window_size, channels), dtype=dtype),
                default_frame_step,
                0,
            )
            analyzer_dict[sid] = analyzer_info

            await sio.emit('define_properties', data, room=sid)
        except Exception:
            await sio.emit(
                'internal_error',
                traceback.format_exc(),
                room=sid,
            )
            await sio.disconnect(sid)

    async def on_disconnect(sid: str):
        analyzer_dict.pop(sid, None)

    async def on_set_properties(sid: str, properties: dict):
        if sid not in analyzer_dict:
            return
        info = analyzer_dict[sid]
        for name, value in properties.items():
            if value is None:
                continue
            attr_name = type(info.analyzer)._properties[name]
            if attr_name == 'window_size':
                if not isinstance(value, int):
                    continue
                old_buf = info.buffer
                new_buf = np.zeros((value, channels), dtype=dtype)
                length = min(new_buf.shape[0], old_buf.shape[0])
                left_length = new_buf.shape[0] - length
                new_buf[left_length:] = old_buf[old_buf.shape[0] - length:]
                info.buffer = new_buf
                info.next_frame = 0
            elif attr_name == 'frame_step':
                if not isinstance(value, int) or value <= 0:
                    continue
                info.frame_step = value
                info.next_frame = 0
            setattr(info.analyzer, attr_name, value)
        data = info.analyzer.get_client_properties(properties.keys())
        await sio.emit('properties', data, room=sid)

    sio.on('start_analysis', on_start_analysis)
    sio.on('disconnect', on_disconnect)
    sio.on('set_properties', on_set_properties)


async def display_queue_info(
    indata_queue: asyncio.Queue,
    queue_info: Dict[str, int],
    exception_queue: asyncio.Queue,
):
    while exception_queue.qsize() == 0:
        print(
            '    \r'
            '{} blocks queued, '
            '{} blocks skipped, '
            '{} blocks analyzed.'.format(
                indata_queue.qsize(),
                queue_info['skip'],
                queue_info['get'],
            ),
            end='',
            flush=True,
        )
        queue_info['get'] = 0
        queue_info['skip'] = 0
        await asyncio.sleep(2.0)


async def application_main(
    host: str,
    port: int,
    sample_rate: float,
    channels: int,
    device: int,
    default_window_size: int,
    default_frame_step: int,
    skip: bool,
):
    loop = asyncio.get_event_loop()
    event = asyncio.Event()
    indata_queue = asyncio.Queue(1 if skip else 0)
    exception_queue = asyncio.Queue()
    analyzer_dict: Dict[str, AnalyzerInfo] = dict()
    queue_info = {'get': 0, 'skip': 0}

    def put_block(block: np.ndarray):
        try:
            indata_queue.put_nowait(block)
        except asyncio.QueueFull:
            queue_info['skip'] += 1

    async def get_block():
        buffer = await indata_queue.get()
        if buffer is not None:
            queue_info['get'] += 1
        return buffer

    from routes import routes
    app = web.Application()
    sio = socketio.AsyncServer(async_mode='aiohttp')
    # Require to attach firstly
    sio.attach(app)
    app.add_routes(routes)
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(['analyzers', '_template']),
    )
    register_handlers(
        sio=sio,
        analyzer_dict=analyzer_dict,
        sample_rate=sample_rate,
        channels=channels,
        default_window_size=default_window_size,
        default_frame_step=default_frame_step,
    )

    print('Launch at http://{}:{}'.format(host, port))
    print('Press Ctrl+C to quit.')
    if skip:
        print('* Overflowed segments will be skipped.')

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    async def catch_task_exception(awaitable: Awaitable[None]):
        try:
            await awaitable
        except Exception as e:
            await exception_queue.put(e)

    input_task = loop.create_task(
        catch_task_exception(
            signal_input(
                loop=loop,
                event=event,
                put_block=put_block,
                sample_rate=sample_rate,
                channels=channels,
                block_size=0,
                device=device,
                dtype=np.float32,
            ),
        )
    )
    analysis_task = loop.create_task(
        catch_task_exception(
            signal_analysis(
                sio=sio,
                analyzer_dict=analyzer_dict,
                get_block=get_block,
            )
        )
    )
    # Sleep a short time in order to catch exceptions
    # from the above tasks immediately.
    await asyncio.sleep(0.1)

    try:
        await display_queue_info(indata_queue, queue_info, exception_queue)
    finally:
        while not indata_queue.empty():
            indata_queue.get_nowait()
        await indata_queue.put(None)
        event.set()
        await asyncio.wait([input_task, analysis_task])
        await runner.cleanup()

    if not exception_queue.empty():
        raise exception_queue.get_nowait()
