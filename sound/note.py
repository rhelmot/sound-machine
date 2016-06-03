from . import SAMPLE_RATE
from .signal import ConstantSignal, Signal

__all__ = ('Note',)

try:
    numty = (int, float, long)
except NameError:
    numty = (int, float)

class Note(Signal):
    """
    An abstraction over the signal base class to add timing information.
    The idea is that a note has a signal and then the value that that signal should be
    used as, in beats, in addition to the length of a beat.

    All the binary operators on Sample objects now work with beats instead of seconds.
    """
    def __init__(self, src, value, beat):
        """
        :param src:     The signal to use as a source for the note
        :param value:   The value of the note in beats
        :param beat:    The length of a beat in samples
        """
        self.src = ConstantSignal.wrap(src)
        self.value = value
        self.beat = beat
        self.duration = self.src.duration
        self.pure = self.src.pure

    def amplitude(self, frame):
        return self.src.amplitude(frame)

    def __add__(self, other):
        if other == 0:
            return self
        return Note(self.src + other.src, max(self.value, other.value), other.beat)

    def __mul__(self, other):
        if type(other) in numty:
            return Note(self.src * other, self.value, self.beat)
        return Note(self.src * other.src, max(self.value, other.value), other.beat)

    def __neg__(self):
        return Note(-self.src, self.value, self.beat)

    def __rshift__(self, other):
        if type(other) not in numty:
            raise TypeError("Can't shift by %s" % repr(other))
        realshift = other * self.beat / SAMPLE_RATE
        return Note(self.src >> realshift, self.value + other, self.beat)

    def __and__(self, other):
        return self + (other >> self.value)

    def __mod__(self, other):
        if type(other) not in numty:
            raise TypeError("Can't loop by %s" % repr(other))
        if other == 0:
            other = self.value
        return Note(self.src % (other * self.beat / SAMPLE_RATE), float('inf'), self.beat)
