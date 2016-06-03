import math

from . import SAMPLE_RATE
from .signal import Signal

__all__ = ('Envelope', 'ADSR', 'Decay', 'Line', 'envelope')

class Envelope(Signal):
    """
    An envelope. This signal should not be a periodic waveform, but rather a broad shape.

    You can use this base class to specify a square pulse for the given duration, in seconds.
    """
    def __init__(self, duration):
        self.duration = duration * SAMPLE_RATE
        self.pure = True

    def amplitude(self, frame):
        if frame < 0:
            return 0
        if frame < self.duration:
            return 1
        return 0

    def adsr(self, attack, decay, release, attack_level=1, sustain_level=0.5):
        """
        Return the current envelope with an additional ADSR component.
        Parameters are the same as for the ADSR class initializer.
        """
        sub = 1 if type(self) is Envelope else self
        return sub * ADSR(attack, decay, self.duration / SAMPLE_RATE - attack - decay - release, release, attack_level, sustain_level)

    def decay(self, decay_param):
        """
        Add an exponential decay to the current envelope.

        :param decay_param:     The speed of the decay, between 0 and 1. Lower values decay faster.
        """
        sub = 1 if type(self) is Envelope else self
        return sub * Decay(0, self.duration / SAMPLE_RATE, 0, decay_param)


class ADSR(Envelope):
    """
    An envelope with portions for Attack[1], Decay[2], Sustain[3], and Release[4].
    You can also specify the attack level[5] and the sustain level[6].
    Timing parameters are in seconds, level parameters are between 0 and 1.
    ::

           /\\                    [5]
          /  \\______________     [6]
         /                  \\
        /                    \\
         [1] [2]   [3]     [4]

    """
    def __init__(self, attack, decay, sustain, release, attack_level=1, sustain_level=0.5):
        super(ADSR, self).__init__(attack + decay + sustain + release)
        self.attack = attack * SAMPLE_RATE
        self.decay = decay * SAMPLE_RATE
        self.sustain = sustain * SAMPLE_RATE
        self.release = release * SAMPLE_RATE
        self.attack_level = float(attack_level)
        self.sustain_level = float(sustain_level)

    def amplitude(self, frame):
        if frame < 0:
            return 0
        if frame < self.attack:
            return float(frame) / self.attack * self.attack_level
        frame -= self.attack
        if frame < self.decay:
            return float(frame) / self.decay * -(self.attack_level - self.sustain_level) + self.attack_level
        frame -= self.decay
        if frame < self.sustain:
            return self.sustain_level
        frame -= self.sustain
        if frame < self.release:
            return float(frame) / self.release * -self.sustain_level + self.sustain_level
        return 0

class Decay(Envelope):
    """
    An enevelope with an attack[1], an exponential decay[2], and a release[3].
    You can specify the decay parameter[4] (between 0 and 1, smaller decays faster,
    and the height of the attack peak[5].
    Times are given in seconds.
    ::

           /*.                    [5]
          /   *._
         /       **-..___       f = [4]^x
        /                \\
         [1]       [2]   [3]
    """
    def __init__(self, attack, sustain, release, decay_param=0.5, attack_level=1.0):
        super(Decay, self).__init__(attack + sustain + release)
        self.attack = attack * SAMPLE_RATE
        self.sustain = sustain * SAMPLE_RATE
        self.release = release * SAMPLE_RATE
        self.decay_param = float(decay_param)
        self.attack_level = float(attack_level)
        self.release_level = self.decay_param ** (float(self.attack + self.sustain) / SAMPLE_RATE) * self.attack_level

    def amplitude(self, frame):
        if frame < 0:
            return 0
        if frame < self.attack:
            return float(frame) / self.attack * self.attack_level
        frame -= self.attack
        if frame < self.sustain:
            return self.decay_param ** (float(frame) / SAMPLE_RATE) * self.attack_level
        frame -= self.sustain
        if frame < self.release:
            return float(frame) / self.release * -self.release_level + self.release_level
        return 0

def envelope(sustain=None,
             attack=0.01,
             decay=None,
             release=None,
             attack_level=1,
             sustain_level=0.7,
             decaying_sustain=True):
    """
    A convenience method to produce an envelope for a musical instrument note.
    All parameters are optional and will pick sane defaults if not provided.

    :param sustain:         The length of the note (seconds)
    :param atack:           The length of the note's attack (seconds)
    :param decay:           if decaying_sustain:
                                the exponential decay parameter.
                            else:
                                the length of the note's decay (seconds)
    :param attack_level:    The intensity of the initial note attack
    :param sustain_level:   Only if not decaying_sustain, the intensity of the note's sustained body
    :param decaying_sustain: Whether the note's sustaining period should involve exponential decay
    """
    if decaying_sustain:
        if decay is None: decay = 0.5
        if release is None: release = 0.1
        if sustain is None: sustain = math.log(0.001, decay)
        return Decay(attack, sustain, release, decay, attack_level=attack_level)
    else:
        if decay is None: decay = 0.1
        if release is None: release = 0.3
        if sustain is None: sustain = 1
        return ADSR(attack, decay, sustain, release, attack_level, sustain_level)

class Line(Envelope):
    """
    A linear line running from start[1] to end[2] in a given time[3] in seconds.
    ::

        *--__                   [1]
             *--__
                  *--__
                       *--__    [2]
               [3]
    """
    def __init__(self, start, end, duration):
        super(Line, self).__init__(duration)
        self.start = start
        self.end = end

    def amplitude(self, frame):
        if frame < 0:
            return self.start
        if frame >= self.duration:
            return self.end
        return (float(frame) / self.duration) * (self.end - self.start) + self.start

