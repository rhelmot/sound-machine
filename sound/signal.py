from . import SAMPLE_RATE

class Signal(object):
    # pylint: disable=unused-argument,no-self-use
    def amplitude(self, frame):
        return 0

    duration = 0
    pure = True

    def __add__(self, other):
        if other == 0:
            return self
        if type(other) is DelaySignal:
            return SequenceSignal((self, 0), (other.src, other.delay))
        return MixSignal(self, ConstantSignal.wrap(other))

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        if other == 0:
            return self
        return self + -ConstantSignal.wrap(other)

    def __rsub__(self, other):
        return -self + ConstantSignal.wrap(other)

    def __mul__(self, other):
        if other == 1:
            return self
        if other == 0 or (type(other) == ConstantSignal and other._amplitude == 0):
            return ConstantSignal(0)
        return EnvelopeSignal(self, ConstantSignal.wrap(other))

    def __rmul__(self, other):
        return self * other

    def __div__(self, other):
        if type(other) not in (int, float, long):
            raise TypeError("Can't divide by %s" % repr(other))
        return self * (1./other)

    def __rdiv__(self, other):
        raise TypeError("Can't divide by %s" % repr(self))

    def __neg__(self):
        return InvertSignal(self)

    def __rshift__(self, other):
        if type(other) not in (int, float, long):
            raise TypeError("Can't shift by %s" % repr(other))
        return DelaySignal(self, int(other*SAMPLE_RATE))

    def __lshift__(self, other):
        return self >> -other

    def __and__(self, other):
        return self + (other >> (float(self.duration) / SAMPLE_RATE))

    def __mod__(self, other):
        if type(other) not in (int, float, long):
            raise TypeError("Can't loop by %s" % repr(other))
        return LoopSignal(self, other * SAMPLE_RATE)

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step is not None:
                raise KeyError(key)
            start = 0 if key.start is None else key.start
            stop = float(self.duration)/SAMPLE_RATE if key.stop is None else key.stop
            return SigSlice(self, start, stop)
        else:
            raise KeyError(key)

    def purify(self, preprocess=False):
        if not preprocess and self.pure:
            return self
        return Purifier(self, preprocess=preprocess)

class LoopSignal(Signal):
    def __init__(self, src, length):
        self.src = src
        self.length = int(length)
        self.duration = float('inf')
        self.pure = True
        self.cache = None if src.pure else [None]*int(src.duration)

    def amplitude(self, frame):
        cur_frame = frame % self.length
        out = 0.

        while frame >= 0 and cur_frame < self.src.duration:
            if self.cache is None:
                out += self.src.amplitude(cur_frame)
            else:
                if self.cache[cur_frame] is None:
                    self.cache[cur_frame] = self.src.amplitude(cur_frame)
                out += self.cache[cur_frame]
            frame -= self.length
            cur_frame += self.length

        return out

class DelaySignal(Signal):
    def __init__(self, src, delay):
        """
        delay is in samples
        """
        self.src = src
        self.delay = delay
        self.duration = src.duration + int(self.delay)
        self.pure = src.pure

    def amplitude(self, frame):
        return self.src.amplitude(frame - self.delay)

    def __rshift__(self, other):
        if type(other) not in (int, float, long):
            raise TypeError("Can't shift by %s" % repr(other))
        return DelaySignal(self.src, self.delay + int(other*SAMPLE_RATE))

    def __add__(self, other):
        if type(other) is DelaySignal:
            return SequenceSignal((self.src, self.delay), (other.src, other.delay))
        else:
            return super(DelaySignal, self).__add__(other)

class SequenceSignal(Signal):
    def __init__(self, *data):
        """
        data is a sequence of tuples of (Signal, starttime)
        starttime is in samples
        """
        if len(data) == 1 and hasattr(data[0], '__iter__'):
            data = data[0]
        data = list(data)
        assert all(type(x[1]) in (int, float, long) for x in data)
        self.srcs = sorted(((src, start, start + src.duration) for src, start in data), key=lambda x: x[1])
        self.duration = max(src[2] for src in self.srcs)
        self.pure = all(src[0].pure for src in self.srcs)

    def amplitude(self, frame):
        # TODO: optimize this maybe?
        out = 0.
        for src, start, end in self.srcs:
            if frame >= start and frame < end:
                out += src.amplitude(frame - start)
        return out

    def __rshift__(self, other):
        if type(other) not in (int, float, long):
            raise TypeError("Can't shift by %s" % repr(other))
        return SequenceSignal((src, start + int(other*SAMPLE_RATE)) for (src, start, _) in self.srcs)

    def __add__(self, other):
        if type(other) is DelaySignal:
            return SequenceSignal((other.src, other.delay), *((src, start) for (src, start, _) in self.srcs))
        elif type(other) is SequenceSignal:
            return SequenceSignal((src, start) for src, start, _ in self.srcs + other.srcs)
        else:
            return MixSignal(self, ConstantSignal.wrap(other))

class InvertSignal(Signal):
    def __init__(self, src):
        self.src = src
        self.duration = src.duration
        self.pure = src.pure

    def amplitude(self, frame):
        return -self.src.amplitude(frame)

    def __neg__(self):
        return self.src

class ConstantSignal(Signal):
    def __init__(self, amplitude):
        self._amplitude = amplitude
        self.duration = 0 if amplitude == 0 else float('inf')
        self.pure = True

    def amplitude(self, frame):
        return self._amplitude

    @staticmethod
    def wrap(val):
        if type(val) in (int, long, float):
            return ConstantSignal(val)
        return val

class MixSignal(Signal):
    def __init__(self, *signals):
        if len(signals) == 1 and hasattr(signals[0], '__iter__'):
            signals = signals[0]
        self.signals = list(signals)
        self.pure = all(s.pure for s in self.signals)
        try:
            self.duration = max(s.duration for s in self.signals if s.duration != float('inf'))
        except ValueError:
            self.duration = float('inf')

    def amplitude(self, frame):
        return sum(s.amplitude(frame) for s in self.signals)

    def __add__(self, other):
        if type(other) is MixSignal:
            return MixSignal(self.signals + other.signals)
        return MixSignal(ConstantSignal.wrap(other), *self.signals)

class EnvelopeSignal(Signal):
    def __init__(self, src, envelope):
        self.src = src
        self.env = envelope
        self.duration = min(self.env.duration, self.src.duration)
        self.pure = self.src.pure and self.env.pure

    def amplitude(self, frame):
        return self.src.amplitude(frame)*self.env.amplitude(frame)

class Purifier(Signal):
    def __init__(self, src, length=None, preprocess=False):
        if length is None:
            if src.duration == float('inf'):
                raise ValueError("Cannot purify infinity")
            length = src.duration
        else:
            length = int(length * SAMPLE_RATE)
        self.nextf = 0
        self.duration = length
        self.storage = [None]*int(self.duration)
        self.pure = True
        self.src = src

        if preprocess:
            self.amplitude(self.duration - 1)

    def amplitude(self, frame):
        if frame < 0: return 0
        if frame >= self.duration: return 0
        while frame >= self.nextf:
            self.storage[self.nextf] = self.src.amplitude(self.nextf)
            self.nextf += 1
        return self.storage[frame]

class SigSlice(Signal):
    def __init__(self, src, from_time, to_time, relative=False):
        self.from_frame = int(from_time * SAMPLE_RATE)
        try:
            self.to_frame = int(to_time * SAMPLE_RATE)
        except OverflowError:
            self.to_frame = float('inf')

        if relative:
            self.to_frame += self.from_frame
        self.duration = self.to_frame - self.from_frame
        self.pure = src.pure
        self.src = src

    def amplitude(self, frame):
        if frame < 0: return 0
        if frame >= self.duration: return 0
        return self.src.amplitude(frame + self.from_frame)

class Reverse(Signal):
    def __init__(self, src):
        self.src = src
        self.duration = src.duration

    def amplitude(self, frame):
        return self.src.amplitude(self.duration - frame - 1)

