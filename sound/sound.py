import numpy

from . import sd, SAMPLE_RATE
from .signal import Signal

class Sound(Signal):
    pass

def play(thing, ret=False, blocking=True, length=None):
    duration = thing.duration if length is None else length * SAMPLE_RATE
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
