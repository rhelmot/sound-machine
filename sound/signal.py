import numpy
import struct
import wave

try:
    import progressbar
except ImportError:
    progressbar = None

from . import SAMPLE_RATE, sd

try:
    numty = (int, float, long)
except NameError:
    numty = (int, float)

__all__ = ('Signal', 'LoopSignal', 'DelaySignal', 'SequenceSignal', 'InvertSignal', 'ConstantSignal', 'MixSignal', 'EnvelopeSignal', 'Purifier', 'SliceSignal', 'ReverseSignal')

class Signal(object):
    """
    The base class for all signal objects. Represents the abstract concept of a signal over time,
    sampled at the given sample rate.

    :ivar pure:     A bool describing whether this signal is pure or not - a pure signal carries
                    no internal state and any frame of it may be accessed in O(1) time.
    :ivar duration: The length of this signal, in frames.

    Several binary operators are overloaded so you may use them on Signal objects.
    A listing that ends with "Constants ok" means that you can use a contant integer or float
    where a signal is expected and it will be converted automatically to an infinitely long
    constant signal of that value.

    * ``+``: You may add signals together to mix them together. Constants ok.
    * ``-``: You may subtract signals and it's like adding one to the inverse of the other.
             You may also negate a signal. Constants ok.
    * ``*``: You may multiply two signals together to perform enveloping or amplitude modulation.
             Constants ok.
    * ``/``: You may divide a signal by a number to reduce its amplitude by that factor.
    * ``>>``: You may right-shift a signal by a number to delay it by that number of seconds.
    * ``<<``: You may left-shift a signal by a number to move it back in time by that number of seconds.
    * ``&``: You may and two signals together to concatenate them.
    * ``%``: You may modulate a signal by a number to loop the first n seconds of it.

    Additionally, you may use array slice notation to extract slices of sample data.
    The slice bounds are in seconds. Normal array indexing does not do anything.
    """
    # pylint: disable=unused-argument,no-self-use

    def play(self, length=None, progress=False):
        """
        Play this signal. Block until playback is complete.
        If the given signal is infinitely long, default to three seconds of playback.

        :param length:      The length to play, in seconds. Optional.
        :param progress:    Whether to show a progress bar for rendering
        """
        data = self.render(length, progress)
        sd.play(data, blocking=True)

    def play_async(self):
        """
        Play this signal asynchronously. Return the `sounddevice` stream object for this playback.
        The only way you should ever really have to interact with the return value of this function is
        to call `.stop()` on it.

        :param thing:       The signal to play
        """
        def cb(outdata, frames, time, status):  # pylint: disable=unused-argument
            startframe = stream.timer
            for i in range(frames):
                outdata[i] = self.amplitude(i+startframe)
            stream.timer += frames
            if stream.timer >= self.duration:
                raise sd.CallbackStop

        stream = sd.OutputStream(callback=cb)
        stream.timer = 0
        stream.start()
        return stream

    def write(self, filename, length=None, progress=True):
        """
        Write this signal to a .wav file.

        :param filename:    The filename to write to. Regardless of its extension, the output filetype
                            will be uncompressed .wav
        :param thing:       The signal to write
        """
        data = self.render(length, progress)
        mm = 2**15 - 1
        fp = wave.open(filename, 'w')
        fp.setparams((1, 2, 44100, 63822, 'NONE', 'not compressed'))
        fp.writeframes(''.join(struct.pack('h', int(max(min(dat, 1), -1)*mm)) for dat in data))
        fp.close()

    def render(self, length=None, progress=False):
        """
        Render this signal into an numpy array of floats. Return the array.

        :param length:      The length to render, in seconds. Optional.
        :param progress:    Whether to show a progress bar for rendering
        """
        if progress and not progressbar:
            print('Install the progressbar module to see a progress bar for rendering')
            progress = False

        duration = self.duration if length is None else length * SAMPLE_RATE
        if duration == float('inf'):
            duration = 3*SAMPLE_RATE
        else:
            duration = int(duration)
        out = numpy.empty((duration, 1))

        pbar = progressbar.ProgressBar(widgets=['Rendering: ', progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()], maxval=duration-1).start() if progress else None

        for i in range(duration):
            out[i] = self.amplitude(i)
            if pbar: pbar.update(i)
        if pbar: pbar.finish()
        return out

    def amplitude(self, frame):
        """
        The main interface for accessing sample data. This is the primary method that should
        be overridden by subclasses.

        :param frame:       The frame whose amplitude should be returned.
        """
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
        if type(other) not in numty:
            raise TypeError("Can't divide by %s" % repr(other))
        return self * (1./other)

    __floordiv__ = __div__
    __truediv__ = __div__

    def __rdiv__(self, other):
        raise TypeError("Can't divide by %s" % repr(self))

    def __neg__(self):
        return InvertSignal(self)

    def __rshift__(self, other):
        if type(other) not in numty:
            raise TypeError("Can't shift by %s" % repr(other))
        return DelaySignal(self, int(other*SAMPLE_RATE))

    def __lshift__(self, other):
        return self >> -other

    def __and__(self, other):
        return self + (other >> (float(self.duration) / SAMPLE_RATE))

    def __mod__(self, other):
        if type(other) not in numty:
            raise TypeError("Can't loop by %s" % repr(other))
        return LoopSignal(self, other)

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step is not None:
                raise KeyError(key)
            start = 0 if key.start is None else key.start
            stop = float(self.duration)/SAMPLE_RATE if key.stop is None else key.stop
            return SliceSignal(self, start, stop)
        else:
            raise KeyError(key)

    def purify(self, preprocess=False):
        """
        Return a pure version of this signal. This is a no-op for pure signals, but for
        impure signals it installs a caching layer on top of the signal.

        :param preprocess:      Whether the cache should preload the sample data at initialize-time.
                                Optional.
        """
        if not preprocess and self.pure:
            return self
        return Purifier(self, preprocess=preprocess)

    def reverse(self):
        """
        Return a reversed version of this signal.
        """
        return ReverseSignal(self)

class LoopSignal(Signal):
    """
    A signal that loops the first n seconds of its child
    """
    def __init__(self, src, length):
        self.src = src.purify()     # lmao
        self.length = int(length * SAMPLE_RATE)
        self.duration = float('inf')
        self.pure = True

    def amplitude(self, frame):
        cur_frame = frame % self.length
        out = 0.

        while frame >= 0 and cur_frame < self.src.duration:
            out += self.src.amplitude(cur_frame)
            frame -= self.length
            cur_frame += self.length

        return out

class DelaySignal(Signal):
    """
    A signal that delays its child by n samples
    """
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
        if type(other) not in numty:
            raise TypeError("Can't shift by %s" % repr(other))
        return DelaySignal(self.src, self.delay + int(other*SAMPLE_RATE))

    def __add__(self, other):
        if type(other) is DelaySignal:
            return SequenceSignal((self.src, self.delay), (other.src, other.delay))
        else:
            return super(DelaySignal, self).__add__(other)

class SequenceSignal(Signal):
    """
    A sequence of signals starting at specific points in time.
    Ultimately used as an optimization for combinations of the `>>`, `&`, and `+` operators.
    """
    def __init__(self, *data):
        """
        data is a sequence of tuples of (Signal, starttime)
        starttime is in samples
        """
        if len(data) == 1 and hasattr(data[0], '__iter__'):
            data = data[0]
        data = list(data)
        assert all(type(x[1]) in numty for x in data)
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
        if type(other) not in numty:
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
    """
    A signal that inverts its child
    """
    def __init__(self, src):
        self.src = src
        self.duration = src.duration
        self.pure = src.pure

    def amplitude(self, frame):
        return -self.src.amplitude(frame)

    def __neg__(self):
        return self.src

class ConstantSignal(Signal):
    """
    A signal that is a constant value
    """
    def __init__(self, amplitude):
        self._amplitude = amplitude
        self.duration = 0 if amplitude == 0 else float('inf')
        self.pure = True

    def amplitude(self, frame):
        return self._amplitude

    @staticmethod
    def wrap(val):
        if type(val) in numty:
            return ConstantSignal(val)
        return val

class MixSignal(Signal):
    """
    A signal that mixes all its children together
    """
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
    """
    A signal that implements enveloping and amplitude modulation
    """
    def __init__(self, src, envelope):
        self.src = src
        self.env = envelope
        self.duration = min(self.env.duration, self.src.duration)
        self.pure = self.src.pure and self.env.pure

    def amplitude(self, frame):
        return self.src.amplitude(frame)*self.env.amplitude(frame)

class Purifier(Signal):
    """
    A signal that caches its child's amplitude data
    """
    def __init__(self, src, length=None, preprocess=False):
        if length is None:
            if src.duration == float('inf') and preprocess:
                raise ValueError("Cannot purify an infinite number of samples")
            length = src.duration
        else:
            length = int(length * SAMPLE_RATE)
        self.nextf = 0
        self.duration = length
        self.storage = [None]*(100000 if self.duration == float('inf') else int(self.duration))
        self.pure = True
        self.src = src

        if preprocess:
            self.amplitude(self.duration - 1)

    def amplitude(self, frame):
        if frame < 0: return 0
        if frame >= self.duration: return 0
        while frame >= self.nextf:
            if self.nextf >= len(self.storage):
                self.storage += [None]*100000
            self.storage[self.nextf] = self.src.amplitude(self.nextf)
            self.nextf += 1
        return self.storage[frame]

class SliceSignal(Signal):
    """
    A signal that extracts a slice of its child
    """
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

class ReverseSignal(Signal):
    """
    A signal that reverses its child
    """
    def __init__(self, src):
        self.src = src
        self.duration = src.duration

    def amplitude(self, frame):
        return self.src.amplitude(self.duration - frame - 1)

    def reverse(self):
        return self.src

