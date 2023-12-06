# This is a song I composed! It's very complex here in the file because it's a very complex tune.
# The song is produced by the function main_tune.

# pylint: disable=undefined-variable,wildcard-import,unused-wildcard-import,invalid-slice-index
import sys
import sound
from sound.notes import *
from sound.instrument import Instrument, Guitar
from sound.tone import Digitar, SquareWave, SAMPLE_RATE
from sound.signal import SliceSignal, Purifier, ReverseSignal, ConstantSignal

def strum_stuff(guitar, chord, length, bpm, basebeat=0):
    base = basebeat * SAMPLE_RATE * 60 / bpm
    L1 = length * 0.25 * SAMPLE_RATE * 60 / bpm
    L2 = length * 0.125 * SAMPLE_RATE * 60 / bpm
    guitar.queue(base, (guitar.strum_down, (chord,)))
    guitar.queue(base + L1, (guitar.strum_up, (chord,)))
    guitar.queue(base + L1 + L2, (guitar.strum_down, (chord,)))
    guitar.queue(base + L1 + L2 + L1, (guitar.strum_up, (chord,)))
    guitar.queue(base + L1 + L2 + L1 + L2, (guitar.strum_down, (chord,)))
    guitar.queue(base + L1 + L2 + L1 + L2 + L2, (guitar.strum_up, (chord,)))

def n_of_them(them, n):
    o = them
    for _ in range(n - 1):
        o &= them
    return o

def sampslice(src, start, length):
    return SliceSignal(src, float(start)/SAMPLE_RATE, float(length)/SAMPLE_RATE, True)

def pitch_right(src, shift):
    ps = sound.filter.PitchShift(src, shift + 1)
    dat = [None]*int(src.duration*10)
    i = 0
    while not ps.done:
        dat[i] = ps.amplitude(i)
        i += 1
    ob = Purifier(0, 0)
    ob.storage = dat[:i]
    ob.duration = i
    ob.src = src
    ob.nextf = i
    return ob

def glitchmobile(src, *args):
    cut = False
    src = Purifier(src)
    pieces = []
    current = 0
    for arg in args:
        if arg[0] == 'ok':
            _, length = arg
            length = int(length*SAMPLE_RATE)
            pieces.append(sampslice(src, current, length))
            current += length
        elif arg[0] == 'loop':
            _, length, times = arg
            length = length * SAMPLE_RATE
            piece = sampslice(src, current, length)
            for _ in range(times):
                pieces.append(piece)
            current += length
        elif arg[0] == 'skip':
            _, length = arg
            current += length * SAMPLE_RATE
        elif arg[0] == 'gap':
            _, length = arg
            piece = ConstantSignal(0)
            piece.duration = length * SAMPLE_RATE
            pieces.append(piece)
        elif arg[0] == 'from':
            _, length, where = arg
            length *= SAMPLE_RATE
            where = where*SAMPLE_RATE + current
            piece = sampslice(src, where, length)
            pieces.append(piece)
        elif arg[0] == 'pitch':
            _, length, pitch = arg
            length *= SAMPLE_RATE
            piece = sampslice(src, current, length)
            pieces.append(pitch_right(piece, pitch))
            current += piece.duration
        elif arg[0] == 'pitchfrom':
            _, length, pitch, where = arg
            length *= SAMPLE_RATE
            where = where*SAMPLE_RATE + current
            piece = sampslice(src, where, length)
            pieces.append(pitch_right(piece, pitch))
        elif arg[0] == 'reversefrom':
            _, length, where = arg
            length *= SAMPLE_RATE
            where = where*SAMPLE_RATE + current
            piece = sampslice(src, where, length)
            pieces.append(ReverseSignal(piece))
        elif arg[0] == 'cut':
            cut = True
            break

    if current < src.duration and not cut:
        pieces.append(sampslice(src, current, src.duration - current))
    o = pieces[0]
    for p in pieces[1:]:
        o &= p
    return o

class Guitar2(Instrument):
    def __init__(self, sample):
        self.sample = sample
        super(Guitar2, self).__init__()

    def _note(self, freq, beats, filling, legato):
        digibase = self.sample(freq)
        return digibase * sound.envelope.Envelope(beats * self.beat * filling)

def make_digi(f, bufs, length):
    return Digitar(f, buffersize=bufs)[:length]

def main_tune():
    guitar = sound.asyncplayer.GuitarStrummer(Digitar)
    strum_stuff(guitar, 'C', 2, 140)
    strum_stuff(guitar, 'G', 2, 140, 2)
    strum_stuff(guitar, 'Am', 2, 140, 4)
    strum_stuff(guitar, 'F', 2, 140, 6)
    strum_stuff(guitar, 'C', 2, 140, 8)
    strum_stuff(guitar, 'G', 2, 140, 10)
    strum_stuff(guitar, 'Am', 2, 140, 12)
    strum_stuff(guitar, 'F', 2, 140, 14)

    buf = guitar[: 60./140*8].purify()
    buf2 = guitar[60./140*8 : 60./140*16].purify()
    p1 = buf[: 60./140*6]
    p2 = buf[60./140*6 : 60./140*6 + 0.1]
    p3 = p2[:0.2]
    p4 = p1 + (p3 >> 60./140*4.4)*2
    p5 = n_of_them(p3, 21)
    p6 = sound.tone.BrownNoise() * sound.envelope.Line(0, 3, 3)
    p7 = p5 + (p6 >> 1.2)
    p8 = (p4 & p7) / 8

    gi = Guitar()
    gi.tempo = 140
    gn = gi.note
    m1 = gn(C4) & gn(G3, 0.75) & gn(G3, 0.25) & gn(A3, 0.5) & gn(G3, 0.5) & gn(F3, 0.5) & gn(E3, 0.5) & gn(E3, 0.25) & gn(F3, 0.25) & gn(G3, 1) & gn(C3, 0.5) & gn(D3, 1.5) & gn(C3, 0.5)
    m2 = gn(C4) & gn(G3, 0.75) & gn(G3, 0.25) & gn(A3, 0.5) & gn(G3, 0.5) & gn(F3, 0.5) & gn(E3, 0.5) & gn(C4) & gn(B3) & gn(C4, 2)

    m3 = ((buf&buf2) / 8 + (m1&m2) / 2)
    m4 = glitchmobile(m3, ('ok', 2.2), ('loop', 0.01, 40), ('gap', 0.1), ('ok', 0.9), ('gap', 0.1), ('ok', 0.5), ('loop', 0.5, 3), ('reversefrom', 1, 0), ('ok', 1.1), ('gap', 0.3), ('ok', 0.5), ('pitch', 0.5, sound.envelope.Line(0, 3, 1)))

    m5 = gn(C4) & gn(E4, 0.75) & gn(C4, 0.25) & gn(F4, 0.5) & gn(E4, 0.5) & gn(D4, 0.5) & gn(C4, 0.5) & gn(D4, 0.25) & gn(E4, 0.25) & gn(D4, 0.25) & gn(E4, 0.25)  & gn(D4, 0.25) & gn(E4, 0.25) & gn(D4, 0.25) & gn(E4, 0.25) & gn(D4, 1)
    bm5 = Purifier(buf2/8 + m5 / 2)
    line = sound.envelope.Line(0, 5, 60./140*8)
    square = SquareWave(50)*sound.envelope.Envelope(0.5)
    m6 = pitch_right(bm5, sound.tone.Noise() * line * line * line) & square

    md = make_digi
    n1 = md(C4 - 10, 50, 1)
    for i in range(30):
        n1 &= md(C4 - 10 + i/2., 50 + i*19, (2**-(i/7.)))

    guitar = sound.asyncplayer.GuitarStrummer(lambda f: Digitar(f, buffersize=350))
    guitar.strum_down('C', 23000)
    guitar.queue(23000*6.5, (guitar.strum_down, ('F',400)))
    buf = guitar[:float(n1.duration)/SAMPLE_RATE - 6].purify(True)
    n2 = (buf/3 >> 6) + n1 / 2
    n3 = n2 >> 1.5

    startf = guitar.frame
    strum_stuff(guitar, 'C', 2, 140, 0)
    strum_stuff(guitar, 'G', 2, 140, 2)
    strum_stuff(guitar, 'Am', 2, 140, 4)
    strum_stuff(guitar, 'F', 2, 140, 6)
    buf2 = SliceSignal(guitar, float(startf)/SAMPLE_RATE, 60./140*8, True).purify(True)

    gi = Guitar2(lambda f: Digitar(f, buffersize=350))
    gi.tempo = 140
    gn = gi.note
    q1 = gn(C4) & gn(G3, 0.75) & gn(G3, 0.25) & gn(A3, 0.5) & gn(G3, 0.5) & gn(F3, 0.5) & gn(E3, 0.5) & gn(E3, 0.25) & gn(F3, 0.25) & gn(G3, 1) & gn(C3, 0.5) & gn(D3, 1.5) & gn(C3, 0.5)
    q2 = gn(C4) & gn(G3, 0.75) & gn(G3, 0.25) & gn(A3, 0.5) & gn(G3, 0.5) & gn(F3, 0.5) & gn(E3, 0.5) & gn(C4) & gn(B3) & gn(C4, 2)
    q3 = ((buf2&buf2) / 6 + (q1&q2) / 2)
    q4 = glitchmobile(q3, ('ok', 0.5), ('loop', 0.1, 3), ('ok', 0.5), ('loop', 0.1, 5), ('ok', 0.5), ('loop', 0.2, 4), ('ok', 0.3), ('pitch', 0.3, -0.5), ('pitch', 0.5, -0.2), ('ok', 0.5), ('gap', 0.1), ('ok', 0.1), ('gap', 0.1), ('pitchfrom', 3, 2, 0), ('ok', 1), ('loop', 0.1, 7), ('pitch', 0.5, -0.2), ('pitch', 0.5, -0.4), ('pitch', 0.25, -0.6), ('pitch', 0.25, -0.8), ('cut',))
    q4_5 = Purifier(Digitar(C4, buffersize=350), 6)
    q5 = sound.filter.PitchShift(q4_5, 0.1) * sound.envelope.ADSR(0, 0, 4, 2, sustain_level=1)
    q6 = q4 & q5

    e1 = pitch_right(Purifier(gi.note(C3, 5)), sound.tone.Noise()*1) >> 1
    e2 = pitch_right(Purifier(gi.note(D3, 10)), sound.tone.Noise()*2)
    e3 = q5[:3.5]
    e4 = (e1 & e2) + (e3/2 >> 4)
    e5 = e4 >> 0.5

    f1 = pitch_right(Purifier(Digitar(C3, buffersize=400), 1), sound.tone.Noise()*2)
    f2 = pitch_right(Purifier(Digitar(C3, buffersize=600), 1), sound.tone.Noise()*1.2)
    f3 = pitch_right(Purifier(Digitar(C3, buffersize=800), 0.8), sound.tone.Noise()*1)
    f4 = pitch_right(Purifier(Digitar(C3, buffersize=1200), 0.5), sound.tone.Noise()*0.5)
    f5 = pitch_right(Purifier(Digitar(C3, buffersize=1400), 0.5), sound.tone.Noise()*0.3)
    f6 = pitch_right(Purifier(Digitar(C3, buffersize=1600), 0.5), sound.tone.Noise()*0.1)
    f7 = Purifier(Digitar(C3, buffersize=2000), 2)
    f8 = f1 & f2 & f3 & f4 & f5 & f6 & f7

    guitar = sound.asyncplayer.GuitarStrummer(lambda f: sound.tone.SawtoothWave(f) * sound.envelope.envelope(decay=0.01))
    strum_stuff(guitar, 'C', 2, 160)
    strum_stuff(guitar, 'G', 2, 160, 2)
    strum_stuff(guitar, 'Am', 2, 160, 4)
    strum_stuff(guitar, 'F', 2, 160, 6)
    strum_stuff(guitar, 'C', 2, 160, 8)
    strum_stuff(guitar, 'G', 2, 160, 10)
    strum_stuff(guitar, 'Am', 2, 160, 12)
    strum_stuff(guitar, 'F', 2, 160, 14)
    strum_stuff(guitar, 'C', 2, 160, 16)
    strum_stuff(guitar, 'G', 2, 160, 18)
    strum_stuff(guitar, 'Am', 2, 160, 20)
    guitar.queue(60./160*22*SAMPLE_RATE, (guitar.strum_up, ('C')))
    guitar.queue(60./160*22.5*SAMPLE_RATE, (guitar.strum_up, ('C')))
    guitar.queue(60./160*23*SAMPLE_RATE, (guitar.strum_down, ('C')))
    buf = guitar[: 60. / 160 * 8].purify()
    buf2 = guitar[60./160*8 : 60./160*16].purify()
    buf3 = guitar[60./160*16 : 60./160*24].purify()

    di = sound.instrument.HardDisk()
    di.tempo = 140
    dn = di.note
    h1 = dn(C3, 2) & dn(D3, 2) & dn(E3) & dn(D3) & dn(C3, 2)
    h2 = h1.src

    si = sound.instrument.Shaker()
    si.tempo = 160
    bi = sound.instrument.BassDrum()
    bi.tempo = 160
    ii = lambda: si.note(0)*10 & si.note(0)*10 & si.note(0)*10 & si.note(0)*10
    pc = lambda: bi.note(40) & si.note(0)*10 & bi.note(40) & si.note(0)*10
    fc = si.note(0)*10 & si.note(0)*10 & si.note(0)*10
    hl = (ii() >> 1)[:60./160*5]

    di.tempo = 160
    h3 = dn(C4) & dn(G3, 0.75) & dn(G3, 0.25) & dn(A3, 0.5) & dn(G3, 0.5) & dn(F3, 0.5) & dn(E3, 0.5) & dn(E3, 0.25) & dn(F3, 0.25) & dn(G3, 1) & dn(C3, 0.5) & dn(D3, 1.5) & dn(C3, 0.5)
    h4 = dn(C4) & dn(G3, 0.75) & dn(G3, 0.25) & dn(A3, 0.5) & dn(G3, 0.5) & dn(F3, 0.5) & dn(E3, 0.5) & dn(C4) & dn(B3) & dn(C4, 2)
    h5 = dn(C4) & dn(E4, 0.75) & dn(C4, 0.25) & dn(F4, 0.5) & dn(E4, 0.5) & dn(D4, 0.5) & dn(C4, 0.5) & dn(D4, 0.25) & dn(E4, 0.25) & dn(D4, 0.25) & dn(E4, 0.25)  & dn(D4, 0.25) & dn(E4, 0.25) & dn(D4, 0.25) & dn(E4, 0.25) & dn(D4, 1.5) & dn(G3, 0.5)
    h6 = dn(C4, 0.5) & dn(B3, 0.5) & dn(A3, 0.5) & dn(G3, 0.5) & dn(F3, 0.5) & dn(E3, 0.5) & dn(D3, 0.5) & dn(C3, 0.5) & dn(C4) & dn(G3) & dn(C4, 2)
    h7 = (buf&buf2&buf2&buf3) / 10 + (h3&h4&h5&h6)*0.8 + (pc()&pc()&pc()&pc()&pc()&pc()&pc()&fc)*0.5
    h8 = h2 & hl & h7

    return p8 & m4 & m6 & n3 & q6 & e5 & f8 & h8

if __name__ == '__main__':
    tune = main_tune()
    if len(sys.argv) > 1:
        tune.write(sys.argv[1])
    else:
        tune.play(progress=True)

