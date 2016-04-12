import math as _math
from . import envelope as _envelope, SAMPLE_RATE
from .sound import Sound

class Volume(Sound):
    def __init__(self, src, vol):
        self.src = src
        self.vol = vol
        self.pure = self.src.pure

    def amplitude(self, frame):
        return self.src.amplitude(frame)*self.vol

class RingFilter(Sound):
    def __init__(self, srcs):
        """
        srcs is a sequence of Sounds
        """
        self.srcs = list(srcs)
        self.duration = min(x.duration for x in self.srcs)
        self.pure = all(map(lambda x: x.pure, self.srcs))

    def amplitude(self, frame):
        return reduce(lambda x, y: x * y.amplitude(frame), self.srcs, 1)

class LowPassFilter(Sound):
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

class HighPassFilter(Sound):
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

class Envelope(Sound):
    def __init__(self, src, env):
        self.src = src
        self.env = env
        self.duration = min(self.env.duration, self.src.duration)
        self.pure = self.src.pure and self.env.pure

    def amplitude(self, frame):
        return self.src.amplitude(frame)*self.env.amplitude(frame)

def envelope(sound, sustain=None,
                    attack=0.01,
                    decay=None,
                    release=None,
                    attack_level=1,
                    sustain_level=0.7,
                    decaying_sustain=True):
    if decaying_sustain:
        if decay is None: decay = 0.5
        if release is None: release = 0.1
        if sustain is None: sustain = _math.log(0.001, decay)
        return Envelope(sound, _envelope.DecayEnvelope(attack, sustain, release, decay, attack_level=attack_level))
    else:
        if decay is None: decay = 0.1
        if release is None: release = 0.3
        if sustain is None: sustain = 1
        return Envelope(sound, _envelope.ADSREnvelope(attack, decay, sustain, release, attack_level, sustain_level))

class Mix(Sound):
    def __init__(self, srcs):
        """
        srcs is a sequence of tuples of (Sound, level)

        level can be any numerical value, the sum will be normalized to 1
        """
        total = float(sum(y for x, y in srcs))
        self.srcs = [(x, y/total) for x, y in srcs]
        self.duration = max(src.duration for src,_ in self.srcs)
        self.pure = all(map(lambda x: x[0].pure, self.srcs))

    def amplitude(self, frame):
        out = 0.
        for src, vol in self.srcs:
            out += src.amplitude(frame) * vol
        return out

class SequencePure(Sound):
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

class Sequence(Sound):
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

class LoopImpure(Sound):
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
        self.lastframe += 1
        if self.lastframe != frame:
            raise Exception("you're like. literally not allowed do that. use Loop if you want to access samples out of order.")

        if frame % self.length == 0:
            sound = self.soundfunc()
            self.active.append((sound, frame, frame + sound.duration))

        if frame >= self.active[0][2]:
            self.active.pop(0)

        out = 0.
        for sound, startf, _ in self.active:
            out += sound.amplitude(frame - startf)

        return out

class Loop(Sound):
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

class AMFilter(Sound):
    def __init__(self, carrier, modulator, mod_quantity=0.2):
        self.carrier = carrier
        self.modulator = modulator
        self.mod_quantity = mod_quantity
        self.pure = carrier.pure and modulator.pure
        self.duration = min(carrier.duration, modulator.duration)

    def amplitude(self, frame):
        return (1 + self.mod_quantity * self.modulator.amplitude(frame))*self.carrier.amplitude(frame)

class FMFilter(Sound):
    def __init__(self, carrier_class, modulator, carrier_freq=440, mod_quantity=300):
        self.carrier_class = carrier_class
        self.modulator = modulator
        self.carrier_freq = carrier_freq
        self.mod_quantity = mod_quantity

        sample_carrier = carrier_class(carrier_freq)
        self.duration = min(sample_carrier.duration, modulator.duration)
        self.pure = sample_carrier.pure and modulator.pure
        self.period = int(sample_carrier.period)
        self.trigger = 0
        self.pure = False # :/

    def _amplitude(self, frame, tframe):
        return self.carrier_class(
                self.carrier_freq + self.mod_quantity * self.modulator.amplitude(frame)
            ).amplitude(tframe)

    def amplitude(self, frame):
        out = self._amplitude(frame, frame - self.trigger)
        #if out > 0:
        #    if self._amplitude(frame - 1, frame - 1 - self.trigger) <= 0:
        #        self.trigger = frame - 1

        return out
