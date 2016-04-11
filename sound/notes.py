scales = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'chromatic': [0,1,2,3,4,5,6,7,8,9,10,11]
}

def note(degree, octave=3, key='A', scale='major', accidental=''):
    pianokey = (octave + degree / len(scales[scale])) * 12 + scales[scale][degree % len(scales[scale])]
    if accidental.lower() in ('sharp', '#', 's'):
        pianokey += 1
    elif accidental.lower() in ('flat', 'b', 'f'):
        pianokey -= 1

    # TODO: handle other keys, OOPS
    return 2 ** (pianokey/12.) * 27.5
