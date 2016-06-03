import re

__all__ = ['note', 'notename', 'scales']

scales = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor': [0, 2, 3, 5, 7, 9, 10],
    'chromatic': [0,1,2,3,4,5,6,7,8,9,10,11]
}

def note(degree, octave=3, key='C', scale='major', accidental=''):
    """
    Return the frequency of the note with the given characteristics

    :param degree:      The scale degree of the note, zero-based
    :param octave:      The octave of the note
    :param key:         The key of the scale
    :param scale:       The name of the scale as a string.
                        Options are "major", "minor", and "chromatic".
    :param accidental:  The accidental for this note as a string.
                        Options are "sharp", "#", or "s" for sharp,
                        "flat", "b", or "f" for flat.

    Note that accidentals do not respect the key - if you are in G major
    and you ask for the sixth degree (ti) sharpened, you will get back G,
    not F# like you would play if you were reading sheet music.
    Consequentially, there is no natural accidental.
    """
    pianokey = (octave*12 + scales[scale][degree % len(scales[scale])])

    if accidental.lower() in ('sharp', '#', 's'):
        pianokey += 1
    elif accidental.lower() in ('flat', 'b', 'f'):
        pianokey -= 1
    elif accidental.lower() in ('doublesharp', '##', 'ss'):
        pianokey += 2
    elif accidental.lower() in ('doubleflat', 'bb', 'ff'):
        pianokey -= 2

    return 2**(pianokey/12.) * notename(key + '0')

def notename(name):
    """
    Translate the name of a note, like "A4", into its frequency in hertz.
    """
    if name == 'C0':
        return 27.5 * 2**(-9./12)
    m = re.search('([A-G])(|b|#|s|f)([0-9])', name)
    notestr, accidental, octave = m.group(1), m.group(2), m.group(3)
    degree = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}[notestr]
    octavenum = int(octave)
    return note(degree, octavenum, accidental=accidental, key='C', scale='major')

for _octave in range(10):
    for _letter in 'ABCDEFG':
        for _accidental in ['', 'b', 's']:
            _name = _letter + _accidental + str(_octave)
            vars()[_name] = notename(_name)
            __all__.append(_name)
