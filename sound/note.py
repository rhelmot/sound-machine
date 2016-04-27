from .sound import Sound, SAMPLE_RATE
from .signal import ConstantSignal

class Note(Sound):
    def __init__(self, src, value, beat):
        self.src = ConstantSignal.wrap(src)
        self.value = value
        self.beat = beat
        self.duration = self.src.duration
        self.pure = self.src.pure

    def amplitude(self, frame):
        return self.src.amplitude(frame)

    def __add__(self, other):
        return Note(self.src + other.src, max(self.value, other.value), other.beat)

    def __mul__(self, other):
        if type(other) in (float, int, long):
            return Note(self.src * other, self.value, self.beat)
        return Note(self.src * other.src, max(self.value, other.value), other.beat)

    def __neg__(self):
        return Note(-self.src, self.value, self.beat)

    def __rshift__(self, other):
        if type(other) not in (int, float, long):
            raise TypeError("Can't shift by %s" % repr(other))
        realshift = other * self.beat / SAMPLE_RATE
        return Note(self.src >> realshift, self.value + other, self.beat)

    def __and__(self, other):
        return self + (other >> self.value)

    def __mod__(self, other):
        if type(other) not in (int, float, long):
            raise TypeError("Can't loop by %s" % repr(other))
        if other == 0:
            other = self.value
        return Note(self.src % (other * self.beat / SAMPLE_RATE), float('inf'), self.beat)
