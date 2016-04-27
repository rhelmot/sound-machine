import numpy

from . import sd, SAMPLE_RATE
from .signal import Signal

class Sound(Signal):
    pass

def play(thing, ret=False, blocking=True):
    duration = thing.duration
    if duration == float('inf'):
        duration = 3*SAMPLE_RATE
    else:
        duration = int(duration)
    out = numpy.empty((duration, 1))
    for i in xrange(duration):
        out[i] = thing.amplitude(i)

    sd.play(out, blocking=blocking)
    if ret:
        return out

def play_async(thing):
    def cb(outdata, frames, time, status):
        startframe = stream.timer
        for i in xrange(frames):
            outdata[i] = thing.amplitude(i+startframe)
        stream.timer += frames
        if stream.timer >= thing.duration:
            raise sd.CallbackStop

    stream = sd.OutputStream(callback=cb)
    stream.timer = 0
    stream.start()
    return stream

def test_scale(instrument, delay=0.5):
    from .filter import SequencePure
    from .notes import note
    play(SequencePure((instrument(note(i)), i*delay) for i in xrange(8)))

def play_song(song, sample):
    """
    Play a song.

    A song is a list of tuples of (frequency, duration, active time ratio).
    """

    def frames(f):
        return int(f * SAMPLE_RATE)

    compiled = []
    duration = 0

    for freq, dur, active in song:
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

hot_cross_buns = [(Cs, .3, .8), (B, .3, 1), (A, .3, 1), (0, .3, 0),
    (Cs, .3, .8), (B, .3, 1), (A, .3, 1), (0, .3, 0),
    (A, .15, .8), (A, .15, .8), (A, .15, .8), (A, .15, .8),
    (B, .15, .8), (B, .15, .8), (B, .15, .8), (B, .15, .8),
    (Cs, .3, .8), (B, .3, 1), (A, .3, 1), (0, .3, 0)]

