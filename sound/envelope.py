import math as _math
from . import SAMPLE_RATE
from .sound import Signal

class Envelope(Signal):
    def __init__(self, duration):
        self.duration = duration * SAMPLE_RATE
        self.pure = True

    def amplitude(self, frame):
        if frame < self.duration:
            return 1
        return 0

    def adsr(self, attack, decay, release, attack_level=1, sustain_level=0.5):
        sub = 1 if type(self) is Envelope else self
        return sub * ADSR(attack, decay, self.duration / SAMPLE_RATE - attack - decay - release, release, attack_level, sustain_level)

    def decay(self, decay_param):
        sub = 1 if type(self) is Envelope else self
        return sub * Decay(0, self.duration / SAMPLE_RATE, 0, decay_param)
        

class ADSR(Envelope):
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
    if decaying_sustain:
        if decay is None: decay = 0.5
        if release is None: release = 0.1
        if sustain is None: sustain = _math.log(0.001, decay)
        return Decay(attack, sustain, release, decay, attack_level=attack_level)
    else:
        if decay is None: decay = 0.1
        if release is None: release = 0.3
        if sustain is None: sustain = 1
        return ADSR(attack, decay, sustain, release, attack_level, sustain_level)

