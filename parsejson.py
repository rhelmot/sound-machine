import sound
import sys
import json

def main(filename, melodyname):
    jsoninfo = json.load(open(filename))
    try:
        melodies = jsoninfo["melodies"]
        melody = melodies[melodyname]

        play_melody(melody)
    except:
        print 'Something went wrong.'

def play_melody(melody):
    instrument = sound.instrument.SineSustain()
    output = [None]
    def add_note(note):
        if output[0] is None:
            output[0] = note
        else:
            output[0] &= note

    for note in melody:
        if "name" in note:
            add_note(instrument.note(sound.notes.notename(note['name']), note['duration']))
        elif "rest" in note:
            add_note(instrument.rest(note['rest']))
        else:
            print 'bad note:', note

    import ipdb; ipdb.set_trace()
    sound.play(output[0])


def usage():
    print 'use this program!'
    print 'please'

if __name__ == '__main__':
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    else:
        usage()
