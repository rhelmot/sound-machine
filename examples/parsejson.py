# This is a parser for json files that describe melodies
# the provided format.json provides two sample melodies
# the format can define its own instruments

# pylint: disable=unnecessary-lambda,abstract-method

import sound
import sys
import json
import copy

try:
    num = (int, long, float)
except NameError:
    num = (int, float)
Sig = sound.signal.Signal
available_signals = [
        (lambda sine: sound.sample.SineWave(sine), (num,)),
        (lambda square: sound.sample.SquareWave(square), (num,)),
        (lambda triangle: sound.sample.TriangleWave(triangle), (num,)),
        (lambda sawtooth: sound.sample.SawtoothWave(sawtooth), (num,)),
        (lambda add_1, add_2: add_1 + add_2, (num, num)),
        (lambda sub_1, sub_2: sub_1 - sub_2, (num, num)),
        (lambda mul_1, mul_2: mul_1 * mul_2, (num, num)),
        (lambda div_1, div_2: div_1 / div_2, (num, num)),
        (lambda volume, source: volume * source, (num, Sig)),
        (lambda envelope, envelope_source: envelope * envelope_source, (Sig, Sig)),
        (lambda adsr_attack, adsr_decay, adsr_sustain, adsr_release, adsr_level: sound.envelope.ADSR(adsr_attack, adsr_decay, adsr_sustain, adsr_release, sustain_level=adsr_level), (num,)*5),
        (lambda decay_speed, decay_length: sound.envelope.Decay(0, decay_length, 0.01, 1./decay_speed), (num, num)),
        (lambda fm_carrier, fm_modulator, fm_quantity: sound.filter.FMFilter(fm_carrier, fm_modulator, fm_quantity), (Sig, Sig, num))
]

class UserInstrument(sound.instrument.Instrument):
    def __init__(self, name, ast, tempo=120):
        super(UserInstrument, self).__init__(tempo)
        self.name = name
        self.ast = ast

    def note(self, freq, beats=1, articulation=None):
        if articulation is None: articulation = self.articulation
        sig = self.parse_signal(self.name, self.ast, {'$FREQUENCY': freq, '$DURATION': beats * self.beat, '$ARTICULATION': articulation})
        if sig.duration == float('inf'):
            sig.duration = beats * self.beat * sound.SAMPLE_RATE
        return sound.note.Note(sig, beats, self.beat * sound.SAMPLE_RATE)

    @staticmethod
    def typecheck(name, signature, args):
        if len(signature) != len(args):
            raise TypeError("%s: need %d args, got %d" % (name, len(signature), len(args)))

        for i, (ty, arg) in enumerate(zip(signature, args)):
            if not isinstance(arg, ty):
                raise TypeError("%s, arg %d: expected %s, got %s" % (name, i, ty, type(arg)))

    @staticmethod
    def parse_helper(name, func, types, item, env):
        keys = func.func_code.co_varnames
        assert len(keys) == len(types)
        for key in keys:
            if key not in item:
                return None
        args = [UserInstrument.parse_signal(name + ' > ' + key, item[key], env) for key in keys]
        return func(*args)

    @staticmethod
    def parse_signal(name, signal, env):
        if type(signal) in num:
            return signal
        elif type(signal) in (str, unicode):
            if signal in env:
                return env[signal]
            else:
                raise ValueError("%s: Bad identifier: %s" % (name, signal))
        elif type(signal) is dict:
            for func, types in available_signals:
                val = UserInstrument.parse_helper(name, func, types, signal, env)
                if val is not None:
                    return val
            raise ValueError("%s: Unknown function!" % name)
        else:
            raise TypeError("%s: VERY bad type" % name)


class MusicData(object):
    def __init__(self, filename):
        try:
            self.json_info = json.load(open(filename))
        except:
            raise ValueError("file %s either does not exist or is not valid JSON" % filename)

        if not 'melodies' in self.json_info:
            raise ValueError("file must contain 'melodies' key at top level")

        self.default_instruments = self.json_info.get('default_instruments', {})
        self.default_instrument = 'sine'
        self.instruments = {key: UserInstrument(key, val) for key, val in self.json_info.get('instruments', {}).iteritems()}
        self.instruments['sine'] = UserInstrument("sine", { "sine": "$FREQUENCY" })

        self.tempo = self.json_info.get('tempo', 120)
        if type(self.tempo) not in (int, float):
            raise TypeError('%s is not a valid tempo' % repr(self.tempo))

    @property
    def melodies(self):
        return [self.melody(name) for name in self.json_info['melodies']]

    def melody(self, name, instrument=None):
        if not name in self.json_info['melodies']:
            raise KeyError(name)

        if instrument is None:
            instrument = self.default_instruments.get(name, self.default_instrument)
        if instrument in self.instruments:
            instrument = self.instruments[instrument]
        else:
            raise ValueError("No such instrument: %s" % instrument)
        instrument.tempo = self.tempo
        instrument.volume = 0.1

        melody = self.json_info['melodies'][name]
        if type(melody) is not list:
            raise TypeError('melody %s is not a list' % name)

        return self._parse_melody(melody, instrument)

    def _parse_melody(self, sequence, instrument):
        out = None

        for note in sequence:
            inst = copy.copy(instrument)
            p = None

            if "articulation" in note:
                inst.articulation = note['articulation']
            if "volume" in note:
                inst.volume = note['volume'] * 0.01
            if "tempo" in note:
                inst.tempo = note['tempo']

            if "name" in note and 'duration' in note:
                p = inst.note(sound.notes.notename(note['name']), note['duration'])
            elif "rest" in note:
                p = inst.rest(note['rest'])
            elif "chord" in note and "duration" in note:
                p = sum(inst.note(sound.notes.notename(x), note['duration']) for x in note['chord']) / len(note['chord'])
            elif "scope" in note:
                if note['scope'] == 'persist':
                    instrument = inst
                elif type(note['scope'] is list):
                    p = self._parse_melody(note['scope'], inst)
            else:
                raise TypeError('note %s is of no known form!' % note)

            if "loop" in note:
                if p.pure:
                    p = reduce(lambda x, y: x & y, [p]*note['loop'])
                else:
                    ct = note['loop'] - 1
                    cpy = copy.copy(note)
                    del cpy['loop']
                    p &= self._parse_melody([cpy]*ct, inst)

            if out is None:
                out = p
            else:
                out &= p

        return out


def main(filename, melodyname):
    music = MusicData(filename)
    melody = music.melody(melodyname)
    melody.play()
    #with sound.play_async(melody):
    #    time.sleep(melody.duration / sound.SAMPLE_RATE)

def usage(argv0):
    print 'Usage: %s filename melodyname' % argv0

if __name__ == '__main__':
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    else:
        usage(sys.argv[0])
