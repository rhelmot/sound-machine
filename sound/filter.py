class Filter(object):
    def __init__(self, src):
        self.src = src

    def amplitude(self, frame):
        return self.src.amplitude(frame)

    @property
    def duration(self):
        return self.src.duration

class VolumeFilter(Filter):
    def __init__(self, src, vol):
        super(VolumeFilter, self).__init__(src)
        self.vol = vol

    def amplitude(self, frame):
        return self.src.amplitude(frame)*self.vol

class EnvelopeFilter(Filter):
    def __init__(self, src, env):
        super(EnvelopeFilter, self).__init__(src)
        self.env = env

    def amplitude(self, frame):
        return self.src.amplitude(frame)*self.env.amplitude(frame)

    @property
    def duration(self):
        return min(self.env.duration, self.src.duration)

class MixFilter(Filter):
    def __init__(self, srcs):   # pylint: disable=super-init-not-called
        self.srcs = srcs

    def amplitude(self, frame):
        out = 0.
        for src, vol in self.srcs:
            out += src.amplitude(frame) * vol
        return out

    @property
    def duration(self):
        return max(src.duration for src,_ in self.srcs)
