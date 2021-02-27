import numpy as np
import scipy as sp
import scipy.signal
import math

from _lib.analyzer import BaseAnalyzer, group, field


def get_chroma_frequencies(
    f_min: float,
    bins_per_octave: int,
    n_octaves: int,
    bin_offset: float,
    dtype: np.dtype = np.float_,
) -> np.ndarray:
    octave = np.arange(n_octaves, dtype=dtype)[np.newaxis, :]
    offset = (
        (bin_offset + np.arange(bins_per_octave))
        / bins_per_octave
    )[:, np.newaxis]
    return f_min * 2.0 ** (octave + offset)


def chroma_filter_bank(
    sample_rate: float,
    n_rfft: int,
    f_min: float,
    bins_per_octave: int,
    n_octaves: int,
    alpha: float = 1.0,
    beta: float = 1.0,
    gamma: float = 1.0,
    ord: float = 2.0,
    dtype=np.float_,
):
    mid_chroma_freqs = get_chroma_frequencies(
        f_min, bins_per_octave, n_octaves,
        bin_offset=0.0, dtype=dtype,
    )[:, :, np.newaxis]
    fft_freqs = np.linspace(
        0.0, sample_rate / 2, n_rfft, endpoint=True,
    )[np.newaxis, np.newaxis, :]

    xy = alpha * np.exp(math.tau * 1j * (fft_freqs / mid_chroma_freqs))
    z = beta * (mid_chroma_freqs - fft_freqs)

    filter_bank = np.maximum(
        0.0,
        (1.0 - gamma * np.linalg.norm(np.stack([xy, z]), ord=ord, axis=0)),
    )

    return filter_bank


class Analyzer (BaseAnalyzer):
    sample_rate = field.float_()
    window_size = field.int_()
    frame_step = field.int_()

    group('scaling')
    scale = field.float_(default=7.0, step=1.0)

    group('filter_bank')
    f_min = field.float_(default=32.70, min=1.0)
    bins_per_octave = field.int_(default=60, min=1)
    n_octaves = field.int_(default=8, min=1)
    alpha = field.float_(default=0.3, step=0.1)
    beta = field.float_(default=0.3, step=0.1)
    gamma = field.float_(default=0.3, step=0.1)
    ord = field.float_(default=1.0, min=0.0, step=0.1)

    group('preemphasis')
    use_preemphasis = field.bool_(default=True)
    preemphasis_coef = field.float_(default=0.97, min=0.0, max=1.0, step=0.01)

    group('misc')
    use_window = field.bool_(default=True)

    @bins_per_octave.validate
    @n_octaves.validate
    def validate_positive_integer(self, value: int):
        return 1 <= value

    @ord.validate
    def validate_positive_float(self, value: float):
        return 0.0 <= value

    @f_min
    def validate_f_min(self, value: float):
        return 1.0 <= value

    def __init__(self):
        self.update_window()
        self.update_filter_bank()
        self.update_chroma_weight()

    @window_size.compute
    def update_window(self):
        self.window = np.hanning(self.window_size)

    @window_size.compute
    @sample_rate.compute
    @f_min.compute
    @bins_per_octave.compute
    @n_octaves.compute
    @alpha.compute
    @beta.compute
    @gamma.compute
    @ord.compute
    def update_filter_bank(self):
        self.filter_bank = chroma_filter_bank(
            sample_rate=self.sample_rate,
            n_rfft=self.window_size // 2 + 1,
            f_min=self.f_min,
            bins_per_octave=self.bins_per_octave,
            n_octaves=self.n_octaves,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            ord=self.ord,
        )
        self.filter_bank_sum = (
            np.maximum(1e-10, self.filter_bank.sum(axis=-1))
        )

    @bins_per_octave.compute
    @n_octaves.compute
    def update_chroma_weight(self):
        self.chroma_weight = np.zeros(
            (self.bins_per_octave, self.n_octaves),
            dtype=np.float_,
        )

    def analyze(self, signal: np.ndarray):
        if self.use_preemphasis:
            signal = sp.signal.lfilter(
                b=[1.0, -self.preemphasis_coef],
                a=1,
                x=signal,
                axis=0,
            )

        if self.use_window:
            signal *= self.window[:, np.newaxis]

        spectrum = np.abs(np.fft.rfft(signal[:, 0]))
        chroma = self.scale * (self.filter_bank @ spectrum)

        return {
            'spectrum': chroma.T.flatten(),
        }
