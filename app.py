import numpy as np

import socketio
from aiohttp import web
import jinja2
import aiohttp_jinja2

import sys
import asyncio
import importlib
import traceback

from _lib.analyzer import BaseAnalyzer
import _lib.coroutine as coroutine

from argparse import ArgumentParser, Namespace, ArgumentDefaultsHelpFormatter

from typing import Optional, Tuple, Dict, Sequence


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
            '--default-frame-step', type=int,
            default=0,
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
        self.channels: int = args.channels
        self.window_size: int = args.default_window_size
        self.frame_step: int = args.default_frame_step

        self.skip: bool = args.skip
        self.queue_info_lock = asyncio.Lock()
        self.queue_info = {'get': 0, 'skip': 0}
        self.analyzer_dict: Dict[str,
                                 Tuple[asyncio.Lock, BaseAnalyzer]] = dict()

    async def _put_buffer(self, indata: np.ndarray):
        async with self.queue_info_lock:
            try:
                self.indata_queue.put_nowait(indata)
            except asyncio.QueueFull:
                self.queue_info['skip'] += 1

    async def _get_buffer(self):
        buffer = await self.indata_queue.get()
        if buffer is not None:
            async with self.queue_info_lock:
                self.queue_info['get'] += 1
        return buffer, self.sample_rate

    async def _get_analyzer_sets(self):
        async with self.analyzer_dict_lock:
            items = list(self.analyzer_dict.items())
        return items

    async def display_queue_info(self):
        while True:
            async with self.queue_info_lock:
                print(
                    '\r{} blocks queued, '
                    '{} blocks skipped, '
                    '{} blocks analyzed.'.format(
                        self.indata_queue.qsize(),
                        self.queue_info['skip'],
                        self.queue_info['get'],
                    ),
                    end='',
                    flush=True,
                )
                self.queue_info['get'] = 0
                self.queue_info['skip'] = 0
            await asyncio.sleep(2.0)

    def main(self):
        try:
            asyncio.run(self.main_coroutine())
        except KeyboardInterrupt:
            pass

    async def main_coroutine(self):
        loop = asyncio.get_event_loop()
        event = asyncio.Event()
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
        print('Press Ctrl+C to quit.')
        if self.skip:
            print('* Overflowed segments will be skipped.')

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        input_task = loop.create_task(
            coroutine.signal_input(
                loop=loop,
                event=event,
                put_buffer=self._put_buffer,
                sample_rate=self.sample_rate,
                channels=self.channels,
                window_size=self.window_size,
                block_size=self.frame_step,
                device=None,
                dtype=np.float32,
            )
        )
        analysis_task = loop.create_task(
            coroutine.signal_analysis(
                sio=self.sio,
                get_buffer=self._get_buffer,
                get_analyzer_sets=self._get_analyzer_sets,
            )
        )

        try:
            await self.display_queue_info()
        finally:
            while not self.indata_queue.empty():
                self.indata_queue.get_nowait()
            await self.indata_queue.put(None)
            event.set()
            await asyncio.wait([input_task, analysis_task])
            await runner.cleanup()

    async def handle_start_analysis(self, sid, name: str):
        analyzer_module_name = 'analyzers.{}'.format(name)
        try:
            analyzer_module = importlib.import_module(analyzer_module_name)
            analyzer = analyzer_module.Analyzer()
            data = analyzer.get_client_properties()

            async with self.analyzer_dict_lock:
                self.analyzer_dict[sid] = asyncio.Lock(), analyzer

            await self.sio.emit('properties', data, room=sid)
        except Exception:
            await self.sio.emit(
                'internal_error',
                traceback.format_exc(),
                room=sid,
            )

    async def handle_disconnect(self, sid):
        async with self.analyzer_dict_lock:
            self.analyzer_dict.pop(sid, None)

    async def handle_set_properties(
        self,
        sid,
        properties: dict,
    ):
        async with self.analyzer_dict_lock:
            if sid not in self.analyzer_dict:
                return
            lock, analyzer = self.analyzer_dict[sid]

        async with lock:
            for name, value in properties.items():
                if value is None:
                    continue
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
