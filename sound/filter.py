from .signal import ConstantSignal, Signal
from .sample import SineWave

__all__ = ('LowPassFilter', 'BetterLowPassFilter', 'HighPassFilter', 'FakeFMFilter', 'FMFilter', 'ring_filter', 'bessel_wave', 'PitchShift')

try:
    numty = (int, float, long)
except NameError:
    numty = (int, float)

class LowPassFilter(Signal):
    """
    Filter the argument signal, cutting out higher-frequency components.

    The beta parameter controls the strength of the filter.
    """
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
    """
    This is a different implementation of the low pass filter.
    Pass it a signal to filter, and then a number of numerical parameters.
    Each frame of the output signal is the linear combination of the given
    parameters and the last n frames from the input signal.
    The last passes parameter corresponds with the most recent input frame.
    """
    def __init__(self, src, *params):
        self.params = list(params)
        eq = float(sum(self.params))
        self.params = [x / eq for x in self.params]
        self.cache = [0.]*len(self.params)
        self.pure = False
        self.duration = src.duration
        self.src = src

    def amplitude(self, frame):
        for i in range(len(self.cache) - 1):
            self.cache[i] = self.cache[i+1]
        self.cache[-1] = self.src.amplitude(frame)

        return sum(x * y for x, y in zip(self.params, self.cache))

class HighPassFilter(Signal):
    """
    Filter the input signal, cutting out low-frequency components.

    The beta parameter controls the strength of the filter.
    """
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

class FakeFMFilter(Signal):
    """
    Don't use this class please, I am so embarassed
    """
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
    """
    Modulate the frequency of the carrier signal with the modulator signal.
    The strength of the modulator may be adjusted by the mod_quantity parameter.
    """
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

def ring_filter(data):
    """
    Perform ring modulation on a given number of signals.

    :param data:    A list of signals to modulate together
    """
    out = 1
    for src in data:
        out *= src
    return out

def bessel_wave(freq, alpha, beta):
    """
    I literally don't care if this isn't technically a thing

    Outputs an FM-synthesized sample with carrier frequency freq, modulator frequency
    freq * alpha, and modulator intensity beta
    """
    return FMFilter(SineWave(freq), SineWave(alpha), beta)


class PitchShift(Signal):
    """
    Perform a pitch shift on the source signal by the shift signal.

    The value of the shift signal serves as a multiplier for the frequency of the source.
    Note that this works just by playing the source faster, so putting this on top of an
    enveloped sound is a bad idea, you need to put this under the envelope.
    """
    def __init__(self, src, shift):
        if isinstance(shift, numty):
            shift = ConstantSignal(shift)
        self.src = src
        self.shift = shift - 1
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
