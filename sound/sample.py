import wave
import struct

from . import SAMPLE_RATE, sd
from .signal import Signal

class RawData(Signal):
    def __init__(self, data):
        self.data = data
        self.duration = len(data)

    def amplitude(self, frame):
        if frame < 0: return 0
        try:
            return self.data[frame]
        except IndexError:
            return 0

    @staticmethod
    def from_file(filename):
        fp = wave.open(filename)
        n = fp.getnframes()
        bdata = fp.readframes(n)
        idata = struct.unpack('h'*n, bdata)
        fdata = [float(x)/(2**15 - 1) for x in idata]
        return RawData(fdata)

    @staticmethod
    def record(seconds):
        data = sd.rec(seconds * SAMPLE_RATE, blocking=True)
        return RawData(data)
