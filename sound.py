#!/usr/bin/env python

import math
import numpy

import sounddevice as sd

SAMPLE_RATE = 44100
sd.default.samplerate = SAMPLE_RATE
sd.default.channels = 1

class Sample(object):
    def __init__(self, frequency):
        self.frequency = float(frequency)

    @property
    def period(self):
        return 1/self.frequency

    def amplitude(self, frame):
        return 0

class SineWave(Sample):
    def amplitude(self, frame):
        return math.sin(frame * 2 * math.pi * self.frequency / SAMPLE_RATE)

def play_song(song, sample=SineWave):
    """
    Play a song.

    A song is a list of tuples of (frequency, duration, active time ratio).
    """

    def frames(f):
        return int(f * SAMPLE_RATE)

    compiled = []
    duration = 0

    for freq, dur, active in song:
        thissample = sample if freq else Sample
        compiled.append((sample(freq), frames(dur), frames(dur*active)))
        duration += frames(dur)

    out = numpy.empty((duration, 1))
    count = 0
    for sample, dur, active in compiled:
        for i in xrange(dur):
            if i < active:
                out[count + i] = sample.amplitude(i) * 0.8
            else:
                out[count + i] = 0
        count += dur

    print 'playing!'
    sd.play(out, blocking=True)

HALF_STEP = 2**(1/12.)
WHOLE_STEP = HALF_STEP**2
A = 440
B = A*WHOLE_STEP
Cs = B*WHOLE_STEP

if __name__ == '__main__':
    play_song([(Cs, .3, .8), (B, .3, 1), (A, .3, 1), (0, .3, 0),
               (Cs, .3, .8), (B, .3, 1), (A, .3, 1), (0, .3, 0),
               (A, .15, .8), (A, .15, .8), (A, .15, .8), (A, .15, .8), 
               (B, .15, .8), (B, .15, .8), (B, .15, .8), (B, .15, .8), 
               (Cs, .3, .8), (B, .3, 1), (A, .3, 1), (0, .3, 0)])
