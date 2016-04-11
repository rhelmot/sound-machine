import math
import random

from . import SAMPLE_RATE
from .sound import Sound

class Sample(Sound):
    def __init__(self, frequency):
        self.frequency = float(frequency)
        self.duration = float('inf')

    @property
    def period(self):
        return 1/self.frequency * SAMPLE_RATE

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

class Noise(Sample):
    # I... guess this is technically pure?
    def __init__(self):
        super(Noise, self).__init__(0)

    def amplitude(self, frame):
        return random.random() * 2 - 1

class Digitar(Sample):
    def __init__(self, frequency):
        super(Digitar, self).__init__(frequency)
        self.buffersize = 256
        self.sample_window = None
        self.cur_frame = None
        self.new_buffer()

    pure = False

    def new_buffer(self):
        self.sample_window = [random.random() * 2 - 1 for _ in xrange(self.buffersize)]
        self.cur_frame = 0

    def get_buffer(self, frame):
        return self.sample_window[frame % self.buffersize]

    def set_buffer(self, frame, value):
        self.sample_window[frame % self.buffersize] = value

    def amplitude(self, frame):
        if frame < self.cur_frame:
            self.cur_frame = 0

        while self.cur_frame < frame:
            self.set_buffer(self.cur_frame + 1, self.get_buffer(self.cur_frame) * 0.3 + self.get_buffer(self.cur_frame + 1) * 0.7)
            self.cur_frame += 1

        return self.get_buffer(self.cur_frame)

def harmonics(freq, ns=(1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16), subsample=SineWave):
    return [subsample(freq*n) for n in ns]
