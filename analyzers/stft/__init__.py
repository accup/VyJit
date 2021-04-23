import numpy as np
import scipy as sp
import scipy.signal

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
    # the scale of a spectrum
    scale = field.float_(default=1.0, step=1.0)
    # whether to scale a spectrum or not
    use_scale = field.bool_(default=False)
    # * When the client-side name is not specified,
    #   the attribute name will be used instead.

    # define another group (in the global scope)
    group('Window')
    # the name of a window function
    window_name = field.str_('Window', default='hann')

    # define the validation of the property (window names in scipy)
    @window_name.validate
    def validate_window_name(self, value: str):
        return value in [
            'boxcar',
            'triang',
            'blackman',
            'hamming',
            'hann',
            'bartlett',
            'flattop',
            'parzen',
            'bohman',
            'blackmanharris',
            'nuttall',
            'barthann',
        ]

    # define the callback of the properties
    @window_size.compute
    @window_name.compute
    def update_window(self):
        self.window = sp.signal.get_window(
            self.window_name,
            self.window_size,
        )
        self.window_sum = self.window.sum() ** 2.0

    def __init__(self):
        # require to call the callbacks above in the initializer
        # (not called automatically)
        self.update_window()

    def analyze(self, signal: np.ndarray):
        # from (frames, channels) to (channels, frames)
        signal = signal.T
        # multiply the window
        signal *= self.window
        # calculate the one side of the power spectrum
        spectrum = np.abs(np.fft.rfft(signal, axis=1)) ** 2

        if self.use_scale:
            spectrum *= self.scale

        # send the result to the client side
        return {
            # 1D numpy array can be sent directly
            'window': self.window,
            # Multi-dimensional numpy array must be converted
            # into the Python list of the 1D numpy arrays
            # because there is no multi-dimensional JavaScript TypedArray.
            'spectrum': list(spectrum),
        }
