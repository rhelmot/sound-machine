import re

__all__ = ['note', 'notename', 'scales', 'A0', 'Ab0', 'As0', 'B0', 'Bb0', 'Bs0', 'C0', 'Cb0', 'Cs0', 'D0', 'Db0', 'Ds0', 'E0', 'Eb0', 'Es0', 'F0', 'Fb0', 'Fs0', 'G0', 'Gb0', 'Gs0', 'A1', 'Ab1', 'As1', 'B1', 'Bb1', 'Bs1', 'C1', 'Cb1', 'Cs1', 'D1', 'Db1', 'Ds1', 'E1', 'Eb1', 'Es1', 'F1', 'Fb1', 'Fs1', 'G1', 'Gb1', 'Gs1', 'A2', 'Ab2', 'As2', 'B2', 'Bb2', 'Bs2', 'C2', 'Cb2', 'Cs2', 'D2', 'Db2', 'Ds2', 'E2', 'Eb2', 'Es2', 'F2', 'Fb2', 'Fs2', 'G2', 'Gb2', 'Gs2', 'A3', 'Ab3', 'As3', 'B3', 'Bb3', 'Bs3', 'C3', 'Cb3', 'Cs3', 'D3', 'Db3', 'Ds3', 'E3', 'Eb3', 'Es3', 'F3', 'Fb3', 'Fs3', 'G3', 'Gb3', 'Gs3', 'A4', 'Ab4', 'As4', 'B4', 'Bb4', 'Bs4', 'C4', 'Cb4', 'Cs4', 'D4', 'Db4', 'Ds4', 'E4', 'Eb4', 'Es4', 'F4', 'Fb4', 'Fs4', 'G4', 'Gb4', 'Gs4', 'A5', 'Ab5', 'As5', 'B5', 'Bb5', 'Bs5', 'C5', 'Cb5', 'Cs5', 'D5', 'Db5', 'Ds5', 'E5', 'Eb5', 'Es5', 'F5', 'Fb5', 'Fs5', 'G5', 'Gb5', 'Gs5', 'A6', 'Ab6', 'As6', 'B6', 'Bb6', 'Bs6', 'C6', 'Cb6', 'Cs6', 'D6', 'Db6', 'Ds6', 'E6', 'Eb6', 'Es6', 'F6', 'Fb6', 'Fs6', 'G6', 'Gb6', 'Gs6', 'A7', 'Ab7', 'As7', 'B7', 'Bb7', 'Bs7', 'C7', 'Cb7', 'Cs7', 'D7', 'Db7', 'Ds7', 'E7', 'Eb7', 'Es7', 'F7', 'Fb7', 'Fs7', 'G7', 'Gb7', 'Gs7', 'A8', 'Ab8', 'As8', 'B8', 'Bb8', 'Bs8', 'C8', 'Cb8', 'Cs8', 'D8', 'Db8', 'Ds8', 'E8', 'Eb8', 'Es8', 'F8', 'Fb8', 'Fs8', 'G8', 'Gb8', 'Gs8', 'A9', 'Ab9', 'As9', 'B9', 'Bb9', 'Bs9', 'C9', 'Cb9', 'Cs9', 'D9', 'Db9', 'Ds9', 'E9', 'Eb9', 'Es9', 'F9', 'Fb9', 'Fs9', 'G9', 'Gb9', 'Gs9'] # type: ignore[reportUnsupportedDunderAll]

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
    if m is None:
        raise ValueError(f"Invalid note {name}")
    notestr, accidental, octave = m.group(1), m.group(2), m.group(3)
    degree = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}[notestr]
    octavenum = int(octave)
    return note(degree, octavenum, accidental=accidental, key='C', scale='major')

for _octave in range(10):
    for _letter in 'ABCDEFG':
        for _accidental in ['', 'b', 's']:
            _name = _letter + _accidental + str(_octave)
            vars()[_name] = notename(_name)
