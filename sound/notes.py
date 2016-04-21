import re

scales = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'chromatic': [0,1,2,3,4,5,6,7,8,9,10,11]
}

def note(degree, octave=3, key='C', scale='major', accidental=''):
    pianokey = (octave + degree / len(scales[scale])) * 12 + scales[scale][degree % len(scales[scale])]
    if accidental.lower() in ('sharp', '#', 's'):
        pianokey += 1
    elif accidental.lower() in ('flat', 'b', 'f'):
        pianokey -= 1

    # TODO: handle other keys, OOPS
    assert key=='C'
    return 2 ** (pianokey/12.) * 27.5 * 2**(3./12)

def notename(name):
    m = re.search('([A-G])(|b|#)([0-9])', name)
    notestr, accidental, octave = m.group(1), m.group(2), m.group(3)
    degree = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}[notestr]
    octavenum = int(octave) - 1
    return note(degree, octavenum, accidental=accidental, key='C')
