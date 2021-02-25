import numpy as np
import librosa

from _lib.analyzer import BaseAnalyzer, field


def get_chroma_fft_bins(
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
    n_fft: int,
    fft_bin_min: float,
    bins_per_octave: int,
    n_octaves: int,
    dtype=np.float_,
):
    low_chroma_fft_bins = get_chroma_fft_bins(
        fft_bin_min, bins_per_octave, n_octaves,
        bin_offset=-1, dtype=dtype,
    )[:, :, np.newaxis]
    mid_chroma_fft_bins = get_chroma_fft_bins(
        fft_bin_min, bins_per_octave, n_octaves,
        bin_offset=0, dtype=dtype,
    )[:, :, np.newaxis]
    high_chroma_fft_bins = get_chroma_fft_bins(
        fft_bin_min, bins_per_octave, n_octaves,
        bin_offset=1, dtype=dtype,
    )[:, :, np.newaxis]

    fft_fft_bins = np.arange(n_fft)[np.newaxis, np.newaxis, :]

    filter_bank = np.zeros(
        (bins_per_octave, n_octaves, n_fft),
        dtype=dtype,
    )
    low_chroma_fft_bins = np.broadcast_to(
        low_chroma_fft_bins, filter_bank.shape)
    mid_chroma_fft_bins = np.broadcast_to(
        mid_chroma_fft_bins, filter_bank.shape)
    high_chroma_fft_bins = np.broadcast_to(
        high_chroma_fft_bins, filter_bank.shape)
    fft_fft_bins = np.broadcast_to(fft_fft_bins, filter_bank.shape)

    low_to_mid = np.logical_and(
        low_chroma_fft_bins < fft_fft_bins,
        fft_fft_bins <= mid_chroma_fft_bins,
    )
    mid_to_high = np.logical_and(
        mid_chroma_fft_bins < fft_fft_bins,
        fft_fft_bins < high_chroma_fft_bins,
    )

    fft_bin = fft_fft_bins[low_to_mid]
    low = low_chroma_fft_bins[low_to_mid]
    mid = mid_chroma_fft_bins[low_to_mid]
    filter_bank[low_to_mid] = (fft_bin - low) / (mid - low)

    fft_bin = fft_fft_bins[mid_to_high]
    mid = mid_chroma_fft_bins[mid_to_high]
    high = high_chroma_fft_bins[mid_to_high]
    filter_bank[mid_to_high] = (high - fft_bin) / (high - mid)

    return filter_bank


class Analyzer (BaseAnalyzer):
    scale = field.float_(default=1.0, step=1.0)
    fft_bin_min = field.float_(default=5.0)
    bins_per_octave = field.int_(default=12, min=1)
    n_octaves = field.int_(default=6, min=1)

    @bins_per_octave.validate
    @n_octaves.validate
    def positive(self, value: int):
        return 1 <= value

    def __init__(self):
        self.update_filter_bank()

    @fft_bin_min.compute
    @bins_per_octave.compute
    @n_octaves.compute
    def update_filter_bank(self):
        self.filter_bank = chroma_filter_bank(
            n_fft=2048 // 2 + 1,
            fft_bin_min=self.fft_bin_min,
            bins_per_octave=self.bins_per_octave,
            n_octaves=self.n_octaves,
        )

    def analyze(self, signal: np.ndarray, sample_rate: float):
        spectrum = np.abs(np.fft.rfft(signal[:, 0]))
        chroma = self.filter_bank @ spectrum
        # weight_sum = np.sum(np.arange(self.n_octaves) * chroma, axis=1)
        # power = np.sum(chroma, axis=1)
        # # octave = (weight_sum / np.sum(chroma, axis=1) + 0.5).astype(np.int_)
        # octave = np.argmax(chroma, axis=1)
        # result = np.zeros_like(chroma)
        # result[np.arange(self.bins_per_octave), octave] = power
        # result = result * self.scale
        return self.scale * chroma.T.reshape(-1)
