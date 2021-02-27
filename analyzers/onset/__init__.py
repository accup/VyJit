import numpy as np
import math

from collections import deque

from _lib.analyzer import BaseAnalyzer, group, field


def get_logarithmic_frequencies(
    f_min: float,
    n_bins: int,
    bins_per_octave: int,
    bin_offset: float,
    dtype: np.dtype = np.float_,
) -> np.ndarray:
    bins = np.arange(n_bins, dtype=dtype)
    return f_min * (2 ** ((bins + bin_offset) / bins_per_octave))


def cqt_kernel(
    sample_rate: float,
    window_size: int,
    f_min: float,
    n_bins: int,
    bins_per_octave: int,
    q: float = 5.0,
    window=np.hamming,
):
    freqs = get_logarithmic_frequencies(
        f_min, n_bins, bins_per_octave,
        bin_offset=0.0, dtype=np.float32,
    )
    lens = np.ceil(q * (sample_rate / freqs))
    lens = np.minimum(window_size, lens).astype(np.int_)
    qs = lens / (sample_rate / freqs)

    kernel = np.zeros((n_bins, window_size), dtype=np.complex64)
    for k in range(n_bins):
        rindex = np.arange(lens[k] - 1, -1, -1)
        kernel[k, window_size - lens[k]:] = (
            window(lens[k])
            * np.exp(1j * math.tau * qs[k] * rindex / lens[k])
        ) / lens[k]

    return kernel


class Analyzer (BaseAnalyzer):
    sample_rate = field.float_()
    window_size = field.int_()
    frame_step = field.int_()

    group('Filterbank')
    f_min = field.float_('Sample rate', default=32.7, step=1.0)
    n_bins = field.int_('Bins', default=36 * 9, min=1)
    bins_per_octave = field.int_('Bins per octave', default=36, min=1)
    q = field.float_('Q', default=5.0, min=0.0, step=1.0)

    group('History')
    use_history = field.bool_('Use history', default=False)
    histories = field.int_('Histories', default=1, min=1)

    group('Miscellaneous')
    scale = field.float_(default=1.0, step=0.1)

    @n_bins.validate
    @bins_per_octave.validate
    @histories.validate
    def validate_positive_int(self, value: int):
        return 0 < value

    @window_size.compute
    def update_window(self):
        self.window = np.hanning(self.window_size)

    @sample_rate.compute
    @window_size.compute
    @f_min.compute
    @n_bins.compute
    @bins_per_octave.compute
    @q.compute
    def update_kernel(self):
        self.kernel = cqt_kernel(
            sample_rate=self.sample_rate,
            window_size=self.window_size,
            f_min=self.f_min,
            n_bins=self.n_bins,
            bins_per_octave=self.bins_per_octave,
            q=self.q,
        )

    @sample_rate.compute
    @window_size.compute
    @f_min.compute
    @n_bins.compute
    @bins_per_octave.compute
    @q.compute
    @histories.compute
    def update_history(self):
        self.history = deque(maxlen=self.histories)

    def __init__(self):
        self.update_window()
        self.update_kernel()
        self.update_history()

    def analyze(self, signal: np.ndarray):
        # signal *= self.window[:, np.newaxis]
        spectrum = self.kernel @ signal[:, 0]
        spectrum = np.abs(spectrum)
        result = spectrum.copy()

        if self.use_history:
            for prev in self.history:
                result -= prev

        self.history.append(spectrum)

        return {
            'spectrum': self.scale * result,
        }
