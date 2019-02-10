import bisect

from .signal import Signal
from .notes import notename

class AsyncPlayer(Signal):
    """
    An object useful for asynchronous play.

    The idea is that you call `.play_async()` on it, then you can call `.play()` and `.mute()`
    on different sound objects to play or stop them in real time.
    """
    def __init__(self):
        self.frame = 0
        self.pure = False
        self.duration = float('inf')
        self.playing = []
        self.infinite = []
        self.callbacks = []
        self.to_play = []

    def amplitude(self, frame):
        for n in self.to_play:
            self._play(n)
        self.to_play = []

        out = 0.
        self.frame = frame
        while len(self.callbacks) != 0 and frame >= -self.callbacks[-1][0]:
            _, callback = self.callbacks.pop()
            if callable(callback):
                callback()
            elif type(callback) is tuple:
                if len(callback) == 2 and callable(callback[0]):
                    callback[0](*callback[1])
                else:
                    self.play(*callback)
            else:
                self.play(callback)

        while len(self.playing) != 0 and frame >= -self.playing[-1][0]:
            self.playing.pop()

        for _, start, note in self.playing:
            out += note.amplitude(frame - start)
        for start, note in self.infinite:
            out += note.amplitude(frame - start)

        return out

    def _play(self, note):
        if note.duration == float('inf'):
            self.infinite.append((self.frame, note))
        else:
            end = self.frame + int(note.duration)
            bisect.insort(self.playing, (-end, self.frame, note))

    def play(self, note):
        """
        :param note:    A Signal object to play, starting now.
        """
        self.to_play.append(note)

    def mute(self, note):
        """
        :param note:    The sound object to mute. Works based on object identity.
        """
        i = 0
        while i < len(self.playing):
            if self.playing[i][2] == note:
                self.playing.pop(i)
            else:
                i += 1
        i = 0
        while i < len(self.infinite):
            if self.infinite[i][1] == note:
                self.infinite.pop(i)
            else:
                i += 1

    def queue(self, when, func, relative=True):
        """
        Queue an event some number of frames in the future.

        :param when:        The number of frames in the future to perform the event
        :param func:        The thing to do in the future
        :param relative:    Optional. If set to false, `when` serves as an absolute timestamp since
                            play started instead of a relative count.

        If func is a callable object, it will be called.
        If func is a tuple, `self.play()` will be called with the tuple contents as args
        Other wise, `self.play()` will be called with func as an argument.
        """
        if relative: when += self.frame
        bisect.insort(self.callbacks, (-when, func))

class KeyedAsyncPlayer(AsyncPlayer):
    """
    An adaptation of AsyncPlayer to associate sounds with keys.
    This way, when you play another note under the same key, the first note that was played
    will be muted.
    """
    def __init__(self):
        super(KeyedAsyncPlayer, self).__init__()
        self.active = {}

    def play(self, note, name=None):    # pylint: disable=arguments-differ
        """
        :param note:    The sound to play
        :param name:    The key to play the sound under
        """
        self.mute(name)
        self.active[name] = note
        super(KeyedAsyncPlayer, self).play(note)

    def mute(self, note):
        """
        :param note:    The key of the sound to mute
        """
        if note not in self.active:
            return
        super(KeyedAsyncPlayer, self).mute(self.active.pop(note))

class InstrumentPlayer(KeyedAsyncPlayer):
    """
    An extension of KeyedAsyncPlayer where the keys are the frequencies of the notes being played,
    and `.play()` accepts arguments to an `Instrument.note()` call.

    The idea is that this simulates an instrument where when you play two of the same note,
    the second note reuses the physical resource producing the sound for that note.
    """
    def __init__(self, instrument):
        """
        :param instrument:  The instrument to play with
        """
        super(InstrumentPlayer, self).__init__()
        self.instrument = instrument

    def play(self, note, *args, **kwargs):
        """
        All parameters are passed directly through to `instrument.note()`
        """
        sig = self.instrument(note, *args, **kwargs)
        super(InstrumentPlayer, self).play(note, sig)

class GuitarStrummer(KeyedAsyncPlayer):
    """
    A guitar that you can strum in various chords!
    """
    def __init__(self, sample):
        super(GuitarStrummer, self).__init__()
        self.sample = sample

    chords = {
        'C': [0, 3, 2, 0, 1, 0],
        'Cm': [0, 0, 5, 5, 4, 3],
        'D': [None, 0, 0, 2, 3, 2],
        'Dm': [0, 0, 0, 2, 3, 2],
        'E': [0, 2, 2, 1, 0, 0],
        'Em': [0, 2, 2, 0, 0, 0],
        'F': [1, 3, 3, 2, 1, 1],
        'Fm': [0, 0, 3, 1, 1, 1],
        'G': [3, 2, 0, 0, 0, 3],
        'Gm': [0, 0, 5, 3, 3, 3],
        'A': [0, 0, 2, 2, 2, 0],
        'Am': [0, 0, 2, 2, 1, 0],
        'A7': [0, 0, 2, 0, 2, 0],
        'Am7': [0, 0, 2, 0, 1, 0],
        'B': [0, 0, 4, 4, 4, 2]
    }

    base_frequencies = list(map(notename, ['E2', 'A2', 'D3', 'G3', 'B3', 'E4']))

    def strum_down(self, chord, delay=200):
        """
        Strum the guitar in the given chord from top to bottom

        :param chord:   The chord to play, as a string. Look at the source for this class
                        for a list of supported chords.
        :param delay:   The time inbetween chord plucks, in frames. Optional.
        """
        freqs = [None if n is None else 2**(n/12.)*b for n, b in zip(self.chords[chord], self.base_frequencies)]
        delays = [n * delay for n in range(6)]
        for i, (f, d) in enumerate(zip(freqs, delays)):
            if f is not None:
                self.queue(d, (self.sample(f), i))

    def strum_up(self, chord, delay=200):
        """
        Strum the guitar in the given chord from bottom to top

        :param chord:   The chord to play, as a string. Look at the source for this class
                        for a list of supported chords.
        :param delay:   The time inbetween chord plucks, in frames. Optional.
        """
        freqs = [None if n is None else 2**(n/12.)*b for n, b in zip(self.chords[chord], self.base_frequencies)]
        delays = [n * delay for n in reversed(range(6))]
        for i, (f, d) in enumerate(zip(freqs, delays)):
            if f is not None:
                self.queue(d, (self.sample(f), i))
            else:
                self.queue(d, (self.mute, (i,)))
