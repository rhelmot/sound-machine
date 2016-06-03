# pylint: disable=unused-argument
from .import SAMPLE_RATE
from .filter import HighPassFilter, FakeFMFilter, LowPassFilter, FMFilter, ring_filter, PitchShift
from .envelope import Decay, envelope, Envelope, ADSR
from .sample import SineWave as Sine, harmonics, Noise, Digitar
from .note import Note

__all__ = ('Instrument', 'SineSustain', 'SineHit', 'KickDrum', 'Shaker', 'BassDrum', 'SquareViolin', 'HardDisk', 'ElectricHorn', 'Bell', 'Bell2', 'ElectricBass', 'Guitar')

class Instrument(object):
    """
    A base class for instruments.
    An instrument is an object that can produce notes to a certain specification.
    """
    def __init__(self, tempo=120):
        """
        :param tempo:   The tempo to produce notes at, in bpm. Optional, defaults to 120.
        """
        self.tempo = tempo
        self.articulation = 0.8
        self.volume = 1

    @property
    def beat(self):
        # convert from beats/minute to seconds/beat
        # b/m * m/s = b/s
        return 60. / self.tempo

    def rest(self, beats=1):
        """
        Return a rest for the given number of beats.
        """
        return Note(0, beats, self.beat * SAMPLE_RATE)

    def note(self, freq, beats=1, articulation=None):
        """
        Return a note to the given specification.

        :param freq:            The frequency of the note to produce
        :param beats:           The number of beats to produce a note for, default 1
        :param articulation:    An optional number describing how legato or staccato notes should
                                be produced, between 0 and 1. Larger values are more legato, smaller
                                values are more staccato. Doesn't work correctly for precussion or
                                string instruments.
        """
        if articulation is None: articulation = self.articulation
        filling = min(1, articulation / 0.8)
        legato = max(0, (articulation - 0.8) / 0.2)
        n = Note(self._note(freq, beats, filling, legato), beats, self.beat * SAMPLE_RATE) * self.volume
        n.author = self
        return n

    def _note(self, freq, beats, filling, legato):
        raise NotImplementedError

    def play(self, *args):
        """
        Play a note to the given specification.
        Parameters are the same as those to `note`.
        """
        self.note(*args).play()


class SineSustain(Instrument):
    """
    A sustained sine tone.
    """
    def _note(self, freq, beats, filling, legato):
        env = Envelope(beats * self.beat * filling)
        avgenvelope = 0.5*legato*env + (1-legato)*env.adsr(0.01,0.05,0.1, sustain_level=0.5)
        return Sine(freq) * avgenvelope

class SineHit(Instrument):
    """
    A plucked sine tone. Sounds sort of xylophonish.
    """
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
    """
    A basic kick drum that's just a low-frequency decaying sine wave.
    Frequency parameters are ignored.
    """
    def _note(self, *args):
        return Sine(110) * Decay(0, 0.4, 0, 0.0000001)

class Shaker(Instrument):
    """
    A basic shaker precussion instrument that's just decaying noise.
    Frequency parameters are ignored.
    """
    def _note(self, *args):
        return (HighPassFilter(Noise(), 0.1) * envelope(decay=0.0001)).purify()

class BassDrum(Instrument):
    """
    A tuned bass drum, works by pitch-shifting a sine wave by a decaying value.
    """
    def _note(self, freq, *args):
        basesound = Sine(freq)
        pitchdecay = envelope(1, decay=0.0001) + 1
        ampdecay = envelope(1, decay=0.0000001)
        return PitchShift(basesound, pitchdecay) * ampdecay

class SquareViolin(Instrument):
    """
    A violin made from a square wave.
    """
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
        return sum(Sine(freq*i) * 0.5 * 1./i for i in range(1, 5)) * argenvelope

class HardDisk(Instrument):
    """
    An instrument that sounds sort of like when people make music out of hard disks
    """
    def _note(self, freq, beats, filling, legato):
        sample = Digitar(freq, buffersize=2000) << 0.1
        env = Envelope(beats * self.beat * filling)
        return sample * env

class ElectricHorn(Instrument):
    """
    A horn-like sound made with FM synthesis
    """
    def _note(self, freq, beats, filling, legato):
        env = ADSR(0.05, 0.05, beats * self.beat * filling - 0.15, 0.15)
        src = FMFilter(Sine(freq), Sine(freq + 0.5), 30)
        return env * src

class Bell(Instrument):
    """
    A bell sound made from ring modulation. Doesn't sound good at all frequencies.
    """
    def _note(self, freq, *args):
        return envelope(decay=0.1, attack=0.001, attack_level=0.4) * ring_filter(harmonics(freq, (2,3,4)))

class Bell2(Instrument):
    """
    Another bell, sounding more metallic, made from my horrible failed first attempt at FM synthesis.
    Doesn't sound good at all frequenies.
    """
    def _note(self, freq, *args):
        return LowPassFilter(
                envelope(decay=0.3) * FakeFMFilter(Sine, Sine(100. * freq / 220), carrier_freq=freq*2, mod_quantity=50),
                0.1
            )

class ElectricBass(Instrument):
    """
    An electric bass guitar, made with FM synthesis
    I think this one is my favorite.
    """
    def _note(self, freq, beats, filling, legato):
        sineA = Sine(freq)
        sustain = beats * self.beat * filling
        return FMFilter(sineA, Sine(freq/2) * envelope(200)) * envelope(decay=0.1, sustain=sustain)

class Guitar(Instrument):
    """
    A simple guitar made from Karplus-Strong plucked string synthesis
    """
    def _note(self, freq, beats, filling, legato):
        digibase = Digitar(freq)
        return digibase * Envelope(beats * self.beat * filling)
