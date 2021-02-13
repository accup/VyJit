import numpy as np
import sounddevice as sd

import socketio
from aiohttp import web
import jinja2
import aiohttp_jinja2

import threading
import asyncio

import sys

from _lib.analyzer import BaseAnalyzer
from _lib.util import numpy_to_bytes

from argparse import ArgumentParser, Namespace, ArgumentDefaultsHelpFormatter

from typing import Optional, Tuple, Dict, Sequence

import analyzers


class AnalyzerRoutine:
    def define_parser(self, parser: ArgumentParser):
        parser.add_argument(
            '--sample-rate', type=float,
            default=16000.0,
            help='sample rate of input signal in hertz',
        )
        parser.add_argument(
            '--channels', type=int,
            default=1,
            help='the number of signal channels',
        )
        parser.add_argument(
            '--default-time-step', type=int,
            default=2048,
            help='default signal clipping interval in samples',
        )
        parser.add_argument(
            '--default-window-size', type=int,
            default=2048,
            help='default signal clipping window size in samples',
        )
        parser.add_argument(
            '--skip', action='store_true',
            help='skip samples when the input data queue is full',
        )

    def setup(self, args: Namespace):
        self.sample_rate: float = args.sample_rate
        self.channels = args.channels

        self.indata_cache_lock = threading.Lock()
        self.indata_cache = np.zeros(
            (args.default_window_size, self.channels),
            dtype=np.float32,
        )

        self.skip: bool = args.skip
        self.analyzer_dict: Dict[web.WebSocketResponse,
                                 Tuple[asyncio.Lock, BaseAnalyzer]] = dict()

    def _reshape_indata_cache(self, window_size: int):
        with self.indata_cache_lock:
            x = self.indata_cache
            y = np.zeros((window_size, self.channels), dtype=np.float32)
            w = min(x.shape[0], y.shape[0])
            y[y.shape[0] - w:, :] = x[x.shape[0] - w:, :]
            self.indata_cache = y

    def get_property(self, name: str):
        if name == 'window_size':
            with self.indata_cache_lock:
                return self.indata_cache.shape[0]
        else:
            raise ValueError("Unknown property name {!r}.".format(name))

    def set_property(self, name: str, value):
        if name == 'window_size':
            self._reshape_indata_cache(value)
        else:
            raise ValueError("Unknown property name {!r}.".format(name))

    def _put_indata(self, indata: np.ndarray):
        try:
            self.indata_queue.put_nowait(indata)
        except asyncio.QueueFull:
            print('Skipped')

    def _input_stream_callback(self, indata: np.ndarray, frames, time, status):
        with self.indata_cache_lock:
            x = indata
            y = self.indata_cache
            w = min(y.shape[0], x.shape[0])
            y[:y.shape[0] - w, :] = y[w:, :]
            y[y.shape[0] - w:, :] = x[x.shape[0] - w:, :]

            self.loop.call_soon_threadsafe(self._put_indata, np.copy(y))

    async def analysis_coroutine(self):
        while True:
            indata = await self.indata_queue.get()
            if indata is None:
                break

            async with self.analyzer_dict_lock:
                items = list(self.analyzer_dict.items())

            for sid, (lock, analyzer) in items:
                async with lock:
                    results = analyzer.analyze(indata)
                    results = numpy_to_bytes(results)
                    await self.sio.emit(
                        'results',
                        data=results,
                        room=sid,
                    )

    def main(self):
        asyncio.run(self.main_coroutine())

    async def main_coroutine(self):
        self.loop = asyncio.get_event_loop()
        self.indata_queue = asyncio.Queue(1 if self.skip else 0)
        self.analyzer_dict_lock = asyncio.Lock()

        from routes import routes
        app = web.Application()
        self.sio = socketio.AsyncServer(async_mode='aiohttp')
        # Require to attach firstly
        self.sio.attach(app)
        app.add_routes(routes)
        aiohttp_jinja2.setup(
            app,
            loader=jinja2.FileSystemLoader('_template'),
        )
        self.sio.on('start_analysis', self.handle_start_analysis)
        self.sio.on('disconnect', self.handle_disconnect)
        self.sio.on('set_properties', self.handle_set_properties)

        host = 'localhost'
        port = 8080
        print('Launch at http://{}:{}'.format(host, port))
        if self.skip:
            print('Overflowed segments will be skipped.')

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._input_stream_callback,
            ):
                await self.analysis_coroutine()
        finally:
            await runner.cleanup()

    async def handle_start_analysis(self, sid, name: str):
        analyzer = analyzers.SUBMODULES[name].Analyzer()
        data = analyzer.get_client_properties()

        async with self.analyzer_dict_lock:
            print(sid)
            self.analyzer_dict[sid] = asyncio.Lock(), analyzer

        await self.sio.emit('properties', data, room=sid)

    async def handle_disconnect(self, sid):
        async with self.analyzer_dict_lock:
            print(
                self.analyzer_dict.pop(sid, None)
            )

    async def handle_set_properties(
        self,
        sid,
        properties: dict,
    ):
        async with self.analyzer_dict_lock:
            lock, analyzer = self.analyzer_dict[sid]

        async with lock:
            for name, value in properties.items():
                setattr(
                    analyzer,
                    type(analyzer)._properties[name],
                    value,
                )

            data = analyzer.get_client_properties(properties.keys())
        await self.sio.emit('properties', data, room=sid)

    def run(self, command_line_args: Optional[Sequence[str]] = None):
        parser = ArgumentParser(
            prog=sys.argv[0],
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        self.define_parser(parser)
        args = parser.parse_args(command_line_args)

        self.setup(args)
        self.main()


if __name__ == '__main__':
    AnalyzerRoutine().run()
