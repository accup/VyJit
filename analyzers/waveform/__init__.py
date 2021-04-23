import numpy as np

from _lib.analyzer import BaseAnalyzer, group, field


class Analyzer (BaseAnalyzer):
    # automatically define the default group (empty string group) at first

    # the sample rate of input signals
    sample_rate = field.float_('Sample rate')
    # the number of channels
    channels = field.int_('Channels')
    # the length of input signals
    window_size = field.int_('Window size')
    # the length of the interval between signal clippings
    frame_step = field.int_('Frame step')

    # define group (in the global scope)
    group('Scaling')
    # the scale of a waveform
    scale = field.float_(default=1.0, step=1.0)
    # whether to scale a waveform or not
    use_scale = field.bool_(default=False)
    # * When the client-side name is not specified,
    #   the attribute name will be used instead.

    # # The initializer can be omitted when no callback is defined.
    # def __init__(self):
    #     pass

    def analyze(self, signal: np.ndarray):
        # sum values along the channels axis
        signal = signal.sum(axis=1)

        if self.use_scale:
            signal *= self.scale

        # send the result to the client side
        return {
            # 1D numpy array can be sent directly
            'waveform': signal,
        }
