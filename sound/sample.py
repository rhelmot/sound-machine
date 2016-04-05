import math

from . import SAMPLE_RATE

class Sample(object):
    def __init__(self, frequency):
        self.frequency = float(frequency)
        self.duration = float('inf')

    @property
    def period(self):
        return 1/self.frequency * SAMPLE_RATE

    def amplitude(self, frame): # pylint: disable=unused-argument,no-self-use
        return 0

    @staticmethod
    def mix(*args):
        out = 0.0
        for data, amp in args:
            out += data * amp
        return out

class SineWave(Sample):
    def amplitude(self, frame):
        return math.sin(frame * 2 * math.pi / self.period)

class SquareWave(Sample):
    def __init__(self, frequency, split=0.5):
        super(SquareWave, self).__init__(frequency)
        self.split = split

    def amplitude(self, frame):
        return 1 if frame % self.period < self.period*self.split else -1

class SawtoothWave(Sample):
    def amplitude(self, frame):
        return frame % self.period / self.period * 2 - 1

class TriangleWave(Sample):
    def amplitude(self, frame):
        pframe = frame % self.period
        hperiod = self.period/2
        qperiod = hperiod/2
        if pframe < qperiod:
            return pframe / qperiod
        pframe -= qperiod
        if pframe < hperiod:
            return pframe / -hperiod*2 + 1
        pframe -= hperiod
        return pframe / qperiod - 1

class Harmonics(Sample):
    def __init__(self,
                 frequency,
                 ns=(1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16),
                 mixing=None,
                 subsample=SineWave):
        super(Harmonics, self).__init__(frequency)
        self.ns = ns
        self.subsamples = [subsample(i*frequency) for i in ns]
        if mixing is None:
            mixing = [1./i for i in xrange(1, len(ns)+1)]
        mix_sum = float(sum(mixing))
        self.mixing = [x/mix_sum for x in mixing]

    def amplitude(self, frame):
        return sum(self.components(frame))

    def components(self, frame):
        return [samp.amplitude(frame)*mix for samp, mix in zip(self.subsamples, self.mixing)]
