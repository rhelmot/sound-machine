from . import SAMPLE_RATE, signal
from .sound import Signal
from .sample import SineWave as _SineWave

class LowPassFilter(Signal):
    def __init__(self, src, beta=0.5, pure=False, iir=True):
        self.src = src
        self.beta = beta
        self.pure_param = pure
        self.pure = src.pure and pure
        self.iir = iir
        self.duration = src.duration
        if pure and iir:
            raise Exception("Can't be both pure and infinite")

        self.last_sample = 0
        self.last_frame = -1

    def amplitude(self, frame):
        self.last_frame += 1
        if self.last_frame != frame:
            if self.pure:
                self.last_frame = frame
                self.last_sample = self.src.amplitude(frame-1)
            else:
                raise Exception("Can't access pure samples out of order")

        cur_sample = self.src.amplitude(frame)
        out = cur_sample * self.beta + self.last_sample * (1-self.beta)
        self.last_sample = out if self.iir else cur_sample
        return out

class BetterLowPassFilter(Signal):
    def __init__(self, src, *params):
        self.params = list(params)
        eq = float(sum(self.params))
        self.params = [x / eq for x in self.params]
        self.cache = [0.]*len(self.params)
        self.pure = False
        self.duration = src.duration
        self.src = src

    def amplitude(self, frame):
        for i in xrange(len(self.cache) - 1):
            self.cache[i] = self.cache[i+1]
        self.cache[-1] = self.src.amplitude(frame)

        return sum(x * y for x, y in zip(self.params, self.cache))

class HighPassFilter(Signal):
    def __init__(self, src, beta=0.5):
        self.src = src
        self.beta = beta
        self.pure = False
        self.last_sample = 0
        self.last_out = 0
        self.last_frame = -1
        self.duration = src.duration

    def amplitude(self, frame):
        self.last_frame += 1
        if self.last_frame != frame:
            raise Exception("Out of order access on impure sample: HighPassFilter")

        cur_sample = self.src.amplitude(frame)
        out = self.beta * (self.last_out + cur_sample - self.last_sample)
        self.last_sample = cur_sample
        self.last_out = out
        return out

class SequencePure(Signal):
    def __init__(self, srcs):
        """
        srcs is a sequence of tuples of (Sound, starttime)

        starttime is in seconds
        """
        self.srcs = []
        self.duration = 0
        self.pure = True
        for sound, time in srcs:
            timef = int(time * SAMPLE_RATE)
            self.srcs.append((sound, timef))
            self.duration = max(self.duration, timef + sound.duration)
            self.pure &= sound.pure

    def amplitude(self, frame):
        out = 0.
        for src, start in self.srcs:
            if frame < start or frame >= start + src.duration:
                continue
            out += src.amplitude(frame - start)
        return out

class Sequence(Signal):
    def __init__(self, srcs):
        """
        srcs is a sequence of tuples of (Sound, starttime)

        starttime is in seconds
        """
        srcs = list(srcs)
        self.srcs = sorted(((sound, int(time * SAMPLE_RATE), int(time * SAMPLE_RATE + sound.duration)) for sound, time in srcs), key=lambda x: x[1], reverse=True)
        self.duration = max(endf for _, _, endf in self.srcs)
        self.lastframe = -1
        self.active = []
        self.pure = False

    def amplitude(self, frame):
        self.lastframe += 1
        if self.lastframe != frame:
            raise Exception("you're like. literally not allowed do that. use PureSequence if you want to access samples out of order.")

        while len(self.srcs) != 0 and self.srcs[-1][1] == frame:
            self.active.append(self.srcs.pop())

        i = 0
        out = 0.
        while i < len(self.active):
            if frame >= self.active[i][2]:
                self.active.pop(i)
            else:
                out += self.active[i][0].amplitude(frame - self.active[i][1])
                i += 1

        return out

class LoopImpure(Signal):
    def __init__(self, soundfunc, length):
        """
        soundfunc is a function that when called with 0 args returns the sample we want to loop
        """
        self.duration = float('inf')
        self.soundfunc = soundfunc
        self.length = int(length * SAMPLE_RATE)
        self.active = []
        self.lastframe = -1
        self.pure = False

    def amplitude(self, frame):
        if frame < 0: return 0

        self.lastframe += 1
        if self.lastframe != frame:
            if frame < self.lastframe:
                #print 'warning: rewinding LoopImpure'
                self.lastframe = 0
                self.active = []

            if frame - self.lastframe > 50:
                print 'warning: seeking LoopImpure %d frames' % (frame - self.lastframe)
            self.lastframe -= 1
            while self.lastframe + 1 < frame:
                self.amplitude(self.lastframe + 1)
            self.lastframe += 1

        if frame % self.length == 0:
            sound = self.soundfunc()
            self.active.append((sound, frame, frame + sound.duration))

        if len(self.active) > 0 and frame >= self.active[0][2]:
            self.active.pop(0)

        out = 0.
        for sound, startf, _ in self.active:
            out += sound.amplitude(frame - startf)

        return out

class Loop(Signal):
    def __init__(self, sound, length):
        if not sound.pure:
            raise Exception("Use LoopImpure to loop an impure sound")
        self.duration = float('inf')
        self.sound = sound
        self.length = int(length * SAMPLE_RATE)
        self.overlap = sound.duration / self.length + 1
        self.pure = True

    def amplitude(self, frame):
        out = 0.
        dframe = frame % self.length
        while dframe < self.sound.duration:
            out += self.sound.amplitude(dframe)
            dframe += self.length

        return out

class AMFilter(Signal):
    def __init__(self, carrier, modulator, mod_quantity=0.2):
        self.carrier = carrier
        self.modulator = modulator
        self.mod_quantity = mod_quantity
        self.pure = carrier.pure and modulator.pure
        self.duration = min(carrier.duration, modulator.duration)

    def amplitude(self, frame):
        return (1 + self.mod_quantity * self.modulator.amplitude(frame))*self.carrier.amplitude(frame)

class FakeFMFilter(Signal):
    def __init__(self, carrier_class, modulator, carrier_freq=440, mod_quantity=300):
        self.carrier_class = carrier_class
        self.modulator = modulator
        self.carrier_freq = carrier_freq
        self.mod_quantity = mod_quantity

        sample_carrier = carrier_class(carrier_freq)
        if not sample_carrier.pure:
            raise Exception("Can't use an impure carrier for a FM filter")
        self.duration = min(sample_carrier.duration, modulator.duration)
        self.trigger = 0
        self.trigger_state = True
        self.pure = False # :/

    def _amplitude(self, frame, tframe):
        return self.carrier_class(
                self.carrier_freq + self.mod_quantity * self.modulator.amplitude(frame)
            ).amplitude(tframe)

    def amplitude(self, frame):
        out = self._amplitude(frame, frame - self.trigger)
        if out > 0 and not self.trigger_state:
            if self._amplitude(frame - 1, frame - 1 - self.trigger) <= 0:
                self.trigger = frame
                self.trigger_state = True
        elif out < 0 and self.trigger_state:
            if self._amplitude(frame - 1, frame - 1 - self.trigger) >= 0:
                self.trigger_state = False

        return out

class FMFilter(Signal):
    def __init__(self, carrier, modulator, mod_quantity=300):
        if not carrier.pure:
            raise Exception("Can't use an impure carrier for a FM filter")
        self.carrier = carrier
        self.modulator = modulator
        self.mod_quantity = mod_quantity
        self.duration = carrier.duration
        self.pure = modulator.pure

    def amplitude(self, frame):
        return self.carrier.amplitude(frame + self.mod_quantity * self.modulator.amplitude(frame))

def RingFilter(data):
    out = 1
    for src in data:
        out *= src
    return out

def bessel_wave(freq, alpha, beta):
    '''
    I literally don't care if this isn't technically a thing
    '''
    return FMFilter(_SineWave(freq), _SineWave(alpha), beta)

class PitchShift(Signal):
    def __init__(self, src, shift):
        if isinstance(shift, (int, float, long)):
            shift = signal.ConstantSignal(shift)
        self.src = src
        self.shift = shift
        self.phase = 0

        self.pure = False
        self.duration = src.duration

        self.done = False

    def amplitude(self, frame):
        self.phase += self.shift.amplitude(frame)
        intpart = int(self.phase)
        fracpart = self.phase - intpart
        f1 = frame + intpart
        f2 = f1 + 1
        if f2 >= self.duration:
            self.done = True

        s1 = self.src.amplitude(f1)
        s2 = self.src.amplitude(f2)
        return s1 * (1-fracpart) + s2 * fracpart
