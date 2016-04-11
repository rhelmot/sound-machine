from . import SAMPLE_RATE

class Envelope(object):
    def __init__(self, duration):
        self.duration = int(duration * SAMPLE_RATE)
        self.pure = True

    def amplitude(self, frame):
        if frame < self.duration:
            return 1
        return 0

class ADSREnvelope(Envelope):
    def __init__(self, attack, decay, sustain, release, attack_level=1, sustain_level=0.5):
        super(ADSREnvelope, self).__init__(attack + decay + sustain + release)
        self.attack = attack * SAMPLE_RATE
        self.decay = decay * SAMPLE_RATE
        self.sustain = sustain * SAMPLE_RATE
        self.release = release * SAMPLE_RATE
        self.attack_level = float(attack_level)
        self.sustain_level = float(sustain_level)

    def amplitude(self, frame):
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

class DecayEnvelope(Envelope):
    def __init__(self, attack, sustain, release, decay_param=0.5, attack_level=1.0):
        super(DecayEnvelope, self).__init__(attack + sustain + release)
        self.attack = attack * SAMPLE_RATE
        self.sustain = sustain * SAMPLE_RATE
        self.release = release * SAMPLE_RATE
        self.decay_param = float(decay_param)
        self.attack_level = float(attack_level)
        self.release_level = self.decay_param ** (float(self.attack + self.sustain) / SAMPLE_RATE) * self.attack_level

    def amplitude(self, frame):
        if frame < self.attack:
            return float(frame) / self.attack * self.attack_level
        frame -= self.attack
        if frame < self.sustain:
            return self.decay_param ** (float(frame) / SAMPLE_RATE) * self.attack_level
        frame -= self.sustain
        if frame < self.release:
            return float(frame) / self.release * -self.release_level + self.release_level
        return 0
