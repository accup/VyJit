import numpy as np

from _lib.analyzer import BaseAnalyzer, analyzer_property


class Analyzer (BaseAnalyzer):
    @analyzer_property('f', default=1.0)
    def factor(self, value: float):
        return 0.0 < value < 0.5

    def analyze(self, signal: np.ndarray):
        return {
            'size': signal.size * self.factor,
            'signal': list(signal),
        }
