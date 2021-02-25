import numpy as np
import librosa

from _lib.analyzer import BaseAnalyzer, field


def get_chroma_frequencies(
    f_min: float,
    bins_per_octave: int,
    n_octaves: int,
    bin_offset: int,
    dtype: np.dtype = np.float_,
) -> np.ndarray:
    octave = np.arange(n_octaves, dtype=dtype)[np.newaxis, :]
    offset = (
        np.arange(bin_offset, bin_offset + bins_per_octave)
        / bins_per_octave
    )[:, np.newaxis]
    return f_min * 2.0 ** (octave + offset)


def chroma_filter_bank(
    sample_rate: float,
    n_rfft: int,
    f_min: float,
    bins_per_octave: int,
    n_octaves: int,
    dtype=np.float_,
):
    low_chroma_freqs = get_chroma_frequencies(
        f_min, bins_per_octave, n_octaves,
        bin_offset=-1, dtype=dtype,
    )[:, :, np.newaxis]
    mid_chroma_freqs = get_chroma_frequencies(
        f_min, bins_per_octave, n_octaves,
        bin_offset=0, dtype=dtype,
    )[:, :, np.newaxis]
    high_chroma_freqs = get_chroma_frequencies(
        f_min, bins_per_octave, n_octaves,
        bin_offset=1, dtype=dtype,
    )[:, :, np.newaxis]

    fft_freqs = np.linspace(
        0.0, sample_rate / 2, n_rfft, endpoint=True,
    )[np.newaxis, np.newaxis, :]

    filter_bank = np.zeros(
        (bins_per_octave, n_octaves, n_rfft),
        dtype=dtype,
    )
    low_chroma_freqs = np.broadcast_to(
        low_chroma_freqs, filter_bank.shape)
    mid_chroma_freqs = np.broadcast_to(
        mid_chroma_freqs, filter_bank.shape)
    high_chroma_freqs = np.broadcast_to(
        high_chroma_freqs, filter_bank.shape)
    fft_freqs = np.broadcast_to(fft_freqs, filter_bank.shape)

    low_to_mid = np.logical_and(
        low_chroma_freqs < fft_freqs,
        fft_freqs <= mid_chroma_freqs,
    )
    mid_to_high = np.logical_and(
        mid_chroma_freqs < fft_freqs,
        fft_freqs < high_chroma_freqs,
    )

    freq = fft_freqs[low_to_mid]
    low = low_chroma_freqs[low_to_mid]
    mid = mid_chroma_freqs[low_to_mid]
    filter_bank[low_to_mid] = (freq - low) / (mid - low)

    freq = fft_freqs[mid_to_high]
    mid = mid_chroma_freqs[mid_to_high]
    high = high_chroma_freqs[mid_to_high]
    filter_bank[mid_to_high] = (high - freq) / (high - mid)

    return filter_bank


class Analyzer (BaseAnalyzer):
    window_size = field.int_()
    sample_rate = field.float_()

    scale = field.float_(default=1.0, step=1.0)
    f_min = field.float_(default=32.70, min=0.0)
    bins_per_octave = field.int_(default=12, min=1)
    n_octaves = field.int_(default=6, min=1)

    weight_factor = field.float_(default=0.95, min=0.0, max=1.0, step=0.01)

    use_pass_filter = field.bool_(default=False)
    pass_filter_min = field.float_(default=0.0, min=0.0, step=50.0)
    pass_filter_max = field.float_(default=0.0, min=0.0, step=50.0)

    use_log = field.bool_(default=False)

    @bins_per_octave.validate
    @n_octaves.validate
    def validate_positive(self, value: int):
        return 1 <= value

    @pass_filter_min.validate
    @pass_filter_max.validate
    def validate_in_nyquist(self, value: float):
        return 0.0 <= value <= self.sample_rate / 2

    def __init__(self):
        self.update_window()
        self.update_filter_bank()
        self.update_chroma_weight()
        self.update_pass_filter()
        self.pass_filter_max = self.sample_rate / 2

    @window_size.compute
    def update_window(self):
        self.window = np.hanning(self.window_size)

    @window_size.compute
    @f_min.compute
    @bins_per_octave.compute
    @n_octaves.compute
    def update_filter_bank(self):
        self.filter_bank = chroma_filter_bank(
            sample_rate=self.sample_rate,
            n_rfft=self.window_size // 2 + 1,
            f_min=self.f_min,
            bins_per_octave=self.bins_per_octave,
            n_octaves=self.n_octaves,
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
        spectrum = np.abs(np.fft.rfft(self.window * signal[:, 0]))
        if self.use_pass_filter:
            spectrum *= self.pass_filter
        chroma = self.filter_bank @ spectrum
        if self.use_log:
            chroma = 10.0 + np.log(np.maximum(1e-10, chroma))
        self.chroma_weight *= 1.0 - self.weight_factor
        self.chroma_weight += self.weight_factor * chroma
        # power = np.sum(chroma, axis=1)
        power = np.sum(chroma)
        # octave = np.argmax(self.chroma_weight, axis=None)
        argmax = np.unravel_index(np.argmax(self.chroma_weight), chroma.shape)
        result = np.zeros_like(chroma)
        # result[np.arange(self.bins_per_octave), octave] = power
        result[argmax] = power
        result = result * self.scale
        return {
            'chroma': result.T.reshape(-1),
            'use_pass_filter': self.use_pass_filter,
            'pass_filter': (self.filter_bank @ self.pass_filter).T.reshape(-1),
        }
