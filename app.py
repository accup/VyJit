import sys
import asyncio

import _lib.coroutine as coroutine

from argparse import ArgumentParser, Namespace, ArgumentDefaultsHelpFormatter

from typing import Optional, Sequence


class AnalyzerRoutine:
    def define_parser(self, parser: ArgumentParser):
        parser.add_argument(
            '--host', type=str,
            default='localhost',
            help='host of the analyzer server',
        )
        parser.add_argument(
            '--port', type=int,
            default=8080,
            help='port of the analyzer server',
        )
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
            default=128,
            help='default signal clipping interval in samples',
        )
        parser.add_argument(
            '--default-window-size', type=int,
            default=2048,
            help='default signal clipping window size in samples',
        )
        parser.add_argument(
            '--no-skip', action='store_false', dest='skip',
            help='do not skip samples when the input data queue is full',
        )

    def setup(self, args: Namespace):
        self.host = args.host
        self.port = args.port
        self.sample_rate: float = args.sample_rate
        self.channels: int = args.channels
        self.default_window_size: int = args.default_window_size
        self.default_frame_step: int = args.default_frame_step
        self.skip: bool = args.skip

    def main(self):
        try:
            asyncio.run(
                coroutine.application_main(
                    host=self.host,
                    port=self.port,
                    sample_rate=self.sample_rate,
                    channels=self.channels,
                    default_window_size=self.default_window_size,
                    default_frame_step=self.default_frame_step,
                    skip=self.skip,
                )
            )
        except KeyboardInterrupt:
            pass

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
