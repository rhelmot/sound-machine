from .filter import MixFilter, EnvelopeFilter
from .envelope import DecayEnvelope, ADSREnvelope
from .sample import SineWave

def xyl_1(freq):
    return MixFilter([
            (
                EnvelopeFilter(
                    SineWave(freq/6*i),
                    DecayEnvelope(0, 1, 0.05, 0.01)
                ),
                (i**4)*0.0005
            ) for i in xrange(1,7)
        ])

def sine_hit(freq):
    return EnvelopeFilter(
                SineWave(freq),
                DecayEnvelope(0, 1, 0.1, 0.00001)
            )

def xylophone(freq):
    return MixFilter([
            (EnvelopeFilter(SineWave(freq/4), DecayEnvelope(0.1, 2, 0.01, 0.3)), 0.5),
            (EnvelopeFilter(SineWave(freq*8), DecayEnvelope(0.01, 2, 0.01, 0.1)), 0.15),
            (EnvelopeFilter(SineWave(freq*8*3), DecayEnvelope(0.01, 2, 0.01, 0.2)), 0.05),
            (EnvelopeFilter(SineWave(50), DecayEnvelope(0.0, 0.2, 0)), 0.05),
            (EnvelopeFilter(SineWave(60), DecayEnvelope(0.0, 0.2, 0)), 0.05),
            (EnvelopeFilter(SineWave(70), DecayEnvelope(0.0, 0.2, 0)), 0.05),
            (EnvelopeFilter(SineWave(80), DecayEnvelope(0.0, 0.2, 0)), 0.05),
            (EnvelopeFilter(SineWave(90), DecayEnvelope(0.0, 0.2, 0)), 0.05),
            (EnvelopeFilter(SineWave(100), DecayEnvelope(0.0, 0.1, 0.1)), 0.05),
        ])

def kickdrum():
    return EnvelopeFilter(
                SineWave(110),
                DecayEnvelope(0, 0.4, 0, 0.0000001)
            )

def square_violin(freq, sustain):
    attack = min(0.5, sustain/10.)
    return EnvelopeFilter(
                MixFilter(
                    [(SineWave(freq*i), 0.5/14 * 1./i) for i in xrange(1, 15)]
                ),
                ADSREnvelope(attack, 0, sustain-attack*1.5, attack/2, sustain_level=1)
            )
