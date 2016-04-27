import sound
import time
import sys
import json
import copy

class MusicData(object):
    def __init__(self, filename):
        try:
            self.json_info = json.load(open(filename))
        except:
            raise ValueError("file %s either does not exist or is not valid JSON" % filename)

        if not 'melodies' in self.json_info:
            raise ValueError("file must contain 'melodies' key at top level")

        if not 'default_instruments' in self.json_info:
            self.json_info['default_instruments'] = {}

        self.default_instrument = sound.instrument.SineSustain()
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
            instrument = self.json_info['default_instruments'].get(name, self.default_instrument)
        instrument.tempo = self.tempo

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
                inst.volume = note['volume']
            if "tempo" in note:
                inst.tempo = note['tempo']

            if "name" in note and 'duration' in note:
                p = inst.note(sound.notes.notename(note['name']), note['duration'])
            elif "rest" in note:
                p = inst.rest(note['rest'])
            elif "chord" in note and "duration" in note:
                p = sum(inst.note(sound.notes.notename(x), note['duration']) for x in note['chord'])
            elif "scope" in note:
                if note['scope'] == 'persist':
                    instrument = inst
                elif type(note['scope'] is list):
                    p = self._parse_melody(inst, note['scope'])
            else:
                raise TypeError('note %s is of no known form!' % note)

            if "loop" in note:
                if p.pure:
                    p = reduce(lambda x, y: x & y, [p]*note['loop'])
                else:
                    ct = note['loop'] - 1
                    cpy = copy.copy(note)
                    del cpy['loop']
                    p &= self._parse_melody([cpy]*ct)

            if out is None:
                out = p
            else:
                out &= p

        return out


def main(filename, melodyname):
    music = MusicData(filename)
    melody = music.melody(melodyname)
    with sound.play_async(melody):
        time.sleep(melody.duration / sound.SAMPLE_RATE)

def usage(argv0):
    print 'Usage: %s filename melodyname' % argv0

if __name__ == '__main__':
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    else:
        usage(sys.argv[0])
