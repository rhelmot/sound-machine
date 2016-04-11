from .filter import Mix, Envelope, RingFilter, envelope, HighPassFilter
from .envelope import DecayEnvelope, ADSREnvelope
from .sample import SineWave as Sine, harmonics, Noise

def xyl_1(freq):
    return Mix([
            (
                Envelope(
                    Sine(freq/6*i),
                    DecayEnvelope(0, 1, 0.05, 0.01)
                ),
                (i**4)*0.0005
            ) for i in xrange(1,7)
        ])

def sine_hit(freq):
    return Envelope(
                Sine(freq),
                DecayEnvelope(0, 1, 0.1, 0.00001)
            )

def xylophone(freq):
    return Mix([
            (Envelope(Sine(freq/4), DecayEnvelope(0.1, 2, 0.01, 0.3)), 0.5),
            (Envelope(Sine(freq*8), DecayEnvelope(0.01, 2, 0.01, 0.1)), 0.15),
            (Envelope(Sine(freq*8*3), DecayEnvelope(0.01, 2, 0.01, 0.2)), 0.05),
            (Envelope(Sine(50), DecayEnvelope(0.0, 0.2, 0)), 0.05),
            (Envelope(Sine(60), DecayEnvelope(0.0, 0.2, 0)), 0.05),
            (Envelope(Sine(70), DecayEnvelope(0.0, 0.2, 0)), 0.05),
            (Envelope(Sine(80), DecayEnvelope(0.0, 0.2, 0)), 0.05),
            (Envelope(Sine(90), DecayEnvelope(0.0, 0.2, 0)), 0.05),
            (Envelope(Sine(100), DecayEnvelope(0.0, 0.1, 0.1)), 0.05),
        ])

def kickdrum():
    return Envelope(
                Sine(110),
                DecayEnvelope(0, 0.4, 0, 0.0000001)
            )

def shaker():
    return envelope(HighPassFilter(Noise(), 0.1), decay=0.0001)

def square_violin(freq, sustain):
    attack = min(0.5, sustain/10.)
    return Envelope(
                Mix(
                    [(Sine(freq*i), 0.5/14 * 1./i) for i in xrange(1, 15)]
                ),
                ADSREnvelope(attack, 0, sustain-attack*1.5, attack/2, sustain_level=1)
            )

def bell(freq):
    return envelope(
            RingFilter(harmonics(freq, (1,2,1.5))),
            decay=0.1,
            attack=0.001,
            attack_level=0.4
        )

