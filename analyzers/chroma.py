import numpy as np
import scipy as sp
import scipy.signal
import librosa
import math

from _lib.analyzer import BaseAnalyzer, field


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


def get_chroma_phases(
    f_min: float,
    bins_per_octave: int,
    n_octaves: int,
    dtype: np.dtype = np.float_,
) -> np.ndarray:
    octave = np.arange(n_octaves, dtype=dtype)[np.newaxis, :]
    offset = np.arange(bins_per_octave, dtype=dtype)[:, np.newaxis]
    return math.tau * (np.log2(f_min) + octave + offset / bins_per_octave)


def get_phases(frequencies: np.ndarray):
    return math.tau * np.log2(frequencies)


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
    window_size = field.int_()
    sample_rate = field.float_()

    scale = field.float_(default=1.0, step=1.0)

    f_min = field.float_(default=32.70, min=1.0)
    bins_per_octave = field.int_(default=36, min=1)
    n_octaves = field.int_(default=8, min=1)
    alpha = field.float_(default=3.0, step=0.1)
    beta = field.float_(default=0.01, step=0.1)
    gamma = field.float_(default=0.01, step=0.1)
    ord = field.float_(default=0.15, min=0.0, step=0.1)

    weight_factor = field.float_(default=1.0, min=0.0, max=1.0, step=0.01)

    use_window = field.bool_(default=True)

    use_pass_filter = field.bool_(default=True)
    pass_filter_min = field.float_(default=0.0, min=0.0, step=50.0)
    pass_filter_max = field.float_(default=0.0, min=0.0, step=50.0)

    normalize = field.bool_(default=False)
    use_log = field.bool_(default=False)

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

    @pass_filter_min.validate
    @pass_filter_max.validate
    def validate_in_nyquist(self, value: float):
        return 0.0 <= value <= self.sample_rate / 2

    def __init__(self):
        self.update_window()
        self.update_filter_bank()
        self.update_chroma_weight()
        self.update_pass_filter()
        self.pass_filter_max = self.sample_rate / 2.0

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

    @window_size.compute
    @sample_rate.compute
    @pass_filter_min.compute
    @pass_filter_max.compute
    def update_pass_filter(self):
        self.pass_filter = np.zeros(
            self.window_size // 2 + 1,
            dtype=np.float_,
        )
        b_min = int(self.pass_filter_min * self.window_size / self.sample_rate)
        b_max = int(self.pass_filter_max * self.window_size / self.sample_rate)
        self.pass_filter[b_min:b_max+1] = 1.0

    def analyze(self, signal: np.ndarray):
        if self.use_window:
            signal *= self.window[:, np.newaxis]
        spectrum = np.abs(np.fft.rfft(signal[:, 0]))

        if self.use_pass_filter:
            spectrum *= self.pass_filter
        chroma = self.scale * (self.filter_bank @ spectrum)
        if self.normalize:
            chroma /= self.filter_bank_sum
        if self.use_log:
            chroma = 10.0 + np.log(np.maximum(1e-10, chroma))

        self.chroma_weight *= 1.0 - self.weight_factor
        self.chroma_weight += self.weight_factor * chroma
        bins = np.arange(self.bins_per_octave)
        arg_octaves = np.argmax(self.chroma_weight, axis=1)
        power = np.sum(self.chroma_weight, axis=1)
        result = np.zeros_like(chroma)
        result[bins, arg_octaves] = power
        return {
            'spectrum': self.chroma_weight.T.flatten(),
            'chroma': result.T.flatten(),
            'use_pass_filter': self.use_pass_filter,
            'pass_filter': (self.filter_bank @ self.pass_filter).T.reshape(-1),
        }
