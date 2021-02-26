import numpy as np

from dataclasses import dataclass

from _lib.analyzer import BaseAnalyzer


@dataclass
class AnalyzerInfo:
    sid: str
    analyzer: BaseAnalyzer
    buffer: np.ndarray
    frame_step: int
