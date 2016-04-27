# pylint: disable=unused-argument
from .filter import HighPassFilter, FakeFMFilter, LowPassFilter, FMFilter, RingFilter
from .envelope import Decay, envelope, Envelope
from .sample import SineWave as Sine, harmonics, Noise, Digitar
from .sound import play as _play, SAMPLE_RATE
from .note import Note

class Instrument(object):
    def __init__(self, tempo=120):
        self.tempo = tempo
        self.articulation = 0.8
        self.volume = 1

    @property
    def beat(self):
        # convert from beats/minute to seconds/beat
        # b/m * m/s = b/s
        return 60. / self.tempo

    def rest(self, beats=1):
        return Note(0, beats, self.beat * SAMPLE_RATE)

    def note(self, freq, beats=1, articulation=None):
        if articulation is None: articulation = self.articulation
        filling = min(1, articulation / 0.8)
        legato = max(0, (articulation - 0.8) / 0.2)
        return Note(self._note(freq, beats, filling, legato), beats, self.beat * SAMPLE_RATE) * self.volume

    def _note(self, freq, beats, filling, legato):
        raise NotImplementedError

    def play(self, *args):
        _play(self.note(*args))

class SineSustain(Instrument):
    def _note(self, freq, beats, filling, legato):
        env = Envelope(beats * self.beat * filling)
        avgenvelope = 0.5*legato*env + (1-legato)*env.adsr(0.01,0.05,0.1, sustain_level=0.5)
        return Sine(freq) * avgenvelope

class SineHit(Instrument):
    def _note(self, freq, beats, filling, legato):
        env = Envelope(beats * self.beat * filling)
        env2 = env.decay(0.095*filling**4 + 0.005).adsr(0, 0, 0.1 - 0.1*legato, sustain_level=1)
        return Sine(freq) * env2

#def xylophone(freq):
#    return Sine(freq/4)    * Decay(0.1, 2, 0.01, 0.3)   * 0.5  + \
#           Sine(freq*8)    * Decay(0.01, 2, 0.01, 0.1)  * 0.15 + \
#           Sine(freq*8*3)  * Decay(0.01, 2, 0.01, 0.2)  * 0.05 + \
#           Sine(50)        * Decay(0.0, 0.2, 0)         * 0.05 + \
#           Sine(60)        * Decay(0.0, 0.2, 0)         * 0.05 + \
#           Sine(70)        * Decay(0.0, 0.2, 0)         * 0.05 + \
#           Sine(80)        * Decay(0.0, 0.2, 0)         * 0.05 + \
#           Sine(90)        * Decay(0.0, 0.2, 0)         * 0.05 + \
#           Sine(100)       * Decay(0.0, 0.1, 0.1)       * 0.05

class KickDrum(Instrument):
    def _note(self, *args):
        return Sine(110) * Decay(0, 0.4, 0, 0.0000001)

class Shaker(Instrument):
    def _note(self, *args):
        return HighPassFilter(Noise(), 0.1) * envelope(decay=0.0001)

class SquareViolin(Instrument):
    def _note(self, freq, beats, filling, legato):
        #attack = min(0.5, sustain/10.)
        #env = envelope(attack=attack,
        #               decay=0,
        #               sustain=sustain-attack*1.5,
        #               attack_level=attack/2,
        #               sustain_level=1,
        #               decaying_sustain=False)
        env = Envelope(beats * self.beat * filling)
        argenvelope = 0.5*legato*env + (1-legato)*env.adsr(0.01,0.05,0.1, sustain_level=0.5)
        return sum(Sine(freq*i) * 0.5/14 * 1./i for i in xrange(1, 15)) * argenvelope

class Bell(Instrument):
    def _note(self, freq, *args):
        return envelope(decay=0.1, attack=0.001, attack_level=0.4) * RingFilter(harmonics(freq, (2,3,4)))

class Bell2(Instrument):
    def _note(self, freq, *args):
        return LowPassFilter(
                envelope(decay=0.3) * FakeFMFilter(Sine, Sine(100. * freq / 220), carrier_freq=freq*2, mod_quantity=50),
                0.1
            )

class ElectricBass(Instrument):
    def _note(self, freq, beats, filling, legato):
        sineA = Sine(freq)
        sustain = beats * self.beat * filling
        return FMFilter(sineA, Sine(freq/2) * envelope(200)) * envelope(decay=0.1, sustain=sustain)

class Guitar(Instrument):
    def _note(self, freq, beats, filling, legato):
        digibase = Digitar(freq)
        return digibase * Envelope(beats * self.beat * filling)
