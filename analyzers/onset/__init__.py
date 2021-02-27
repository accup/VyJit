import numpy as np
from collections import deque

from _lib.analyzer import BaseAnalyzer, group, field


def get_logarithmic_frequencies(
    f_min: float,
    n_bins: int,
    bins_per_octave: int,
    bin_offset: float,
    dtype: np.dtype = np.float_,
) -> np.ndarray:
    freqs = np.arange(n_bins, dtype=dtype)
    freqs += bin_offset
    freqs /= bins_per_octave
    # np.exp2(freqs, out=freqs)
    # freqs *= f_min
    return f_min * 2 ** freqs


def logarithmic_filter_bank(
    sample_rate: float,
    n_rfft: int,
    f_min: float,
    n_bins: int,
    bins_per_octave: int,
    width: float = 1.0,
    dtype=np.float_,
):
    lo_freqs = get_logarithmic_frequencies(
        f_min, n_bins, bins_per_octave,
        bin_offset=-width, dtype=dtype,
    )[:, np.newaxis]
    mi_freqs = get_logarithmic_frequencies(
        f_min, n_bins, bins_per_octave,
        bin_offset=0.0, dtype=dtype,
    )[:, np.newaxis]
    hi_freqs = get_logarithmic_frequencies(
        f_min, n_bins, bins_per_octave,
        bin_offset=width, dtype=dtype,
    )[:, np.newaxis]
    ft_freqs = np.linspace(
        0.0, sample_rate / 2, n_rfft, endpoint=True,
    )[np.newaxis, :]

    filter_bank = np.zeros((n_bins, n_rfft), dtype=dtype)
    lo_freqs = np.broadcast_to(lo_freqs, shape=filter_bank.shape)
    mi_freqs = np.broadcast_to(mi_freqs, shape=filter_bank.shape)
    hi_freqs = np.broadcast_to(hi_freqs, shape=filter_bank.shape)
    ft_freqs = np.broadcast_to(ft_freqs, shape=filter_bank.shape)

    lo_to_mi = np.logical_and(lo_freqs < ft_freqs, ft_freqs <= mi_freqs)
    lo = lo_freqs[lo_to_mi]
    mi = mi_freqs[lo_to_mi]
    ft = ft_freqs[lo_to_mi]
    filter_bank[lo_to_mi] = (ft - lo) / (mi - lo)

    mi_to_hi = np.logical_and(mi_freqs < ft_freqs, ft_freqs <= hi_freqs)
    mi = mi_freqs[mi_to_hi]
    hi = hi_freqs[mi_to_hi]
    ft = ft_freqs[mi_to_hi]
    filter_bank[mi_to_hi] = (hi - ft) / (hi - mi)

    return filter_bank


class Analyzer (BaseAnalyzer):
    sample_rate = field.float_()
    window_size = field.int_()
    frame_step = field.int_()

    group('Filterbank')
    f_min = field.float_('Sample rate', default=32.7, step=1.0)
    n_bins = field.int_('Bins', default=36 * 9, min=1)
    bins_per_octave = field.int_('Bins per octave', default=36, min=1)
    width = field.float_('Width', default=1.0, min=0.0, step=0.1)

    group('History')
    use_history = field.bool_('Use history', default=False)
    histories = field.int_('Histories', default=1, min=1)

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
    @width.compute
    def update_filter_bank(self):
        self.filter_bank = logarithmic_filter_bank(
            sample_rate=self.sample_rate,
            n_rfft=self.window_size // 2 + 1,
            f_min=self.f_min,
            n_bins=self.n_bins,
            bins_per_octave=self.bins_per_octave,
            width=self.width,
        )
        self.filter_bank_sum = self.filter_bank.sum(axis=1)

    @sample_rate.compute
    @window_size.compute
    @f_min.compute
    @n_bins.compute
    @bins_per_octave.compute
    @width.compute
    @histories.compute
    def update_history(self):
        self.history = deque(maxlen=self.histories)

    def __init__(self):
        self.update_window()
        self.update_filter_bank()
        self.update_history()

    def analyze(self, signal: np.ndarray):
        signal *= self.window[:, np.newaxis]
        spectrum = np.abs(np.fft.rfft(signal[:, 0]))
        spectrum = self.filter_bank @ spectrum
        result = spectrum.copy()

        if self.use_history:
            for prev in self.history:
                result -= prev

        self.history.append(spectrum)

        return {
            'spectrum': result,
            'filter_bank_sum': self.filter_bank_sum,
        }
