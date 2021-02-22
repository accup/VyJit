import numpy as np

from _lib.analyzer import BaseAnalyzer, analyzer_property


class Analyzer (BaseAnalyzer):
    normalized = analyzer_property(default=False)
    scale = analyzer_property(default=1.0)

    def analyze(self, signal: np.ndarray, sample_rate: float):
        signal *= self.scale
        if self.normalized:
            signal /= max(1e-10, np.abs(signal.max()))
        return signal[:, 0]
