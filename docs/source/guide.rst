How Do I Use This Library
=========================

Good question!

.. code-block:: python

   import sound
   from sound.notes import *
   inst = sound.instrument.ElectricBass()
   inst.tempo = 120
   tune = inst.note(C3) & inst.note(D3) & inst.note(E3) & inst.note(F3) & inst.note(G3)
   tune.play()

The desirable result here is that the electric bass play a short ascending scale in C major at 120 beats per minute, one beat per note.
That's a pretty flashy example, though, so let's start from first principles.

Samples
-------

All sounds that can be played by this framework are ultimately a series of samples (in the sense of that by default we output sound at 44100 samples per second).
A Sample object, in this framework, is an infinitely long tone at maximum intensity generated from a very simple algorithm.
Sample objects are found in the ``sound.samples`` submodule.
For example:

.. code-block:: python

   sound.sample.SineWave(440).play()

(An infinitely long sound will be cut off at three seconds by default)

This plays a sine wave of frequency 440Hz!
Pretty cool. Other samples you can draw upon from this module are ``SquareWave``, ``SawtoothWave``, ``TriangleWave``, ``Noise``, ``BrownNoise``, and ``Digitar``.
(``Digitar`` implements the Karplus-Strong plucked string synthesis algorithm)

The noise samples do not have a frequency parameter, because noise is untuned.
The brown noise and digitar samples are what we call "impure" samples - instances of these classes keep state, and usually cannot access sound data out of order.
If you ever run into an angry error or performance slows to a crawl, it might be because you're taking an impure signal and trying to access its samples out or order.
A quick fix for this is to simply call ``.purify()`` on the resulting object - note that this returns a new "purified" object, leaving the original unchanged.

Interlude - ASTs, Lazy Evaluation, and State
--------------------------------------------

This is a good opportunity to talk about what's under the hood and how you should think about class instances from this library!

Every sound and signal object is lazily evaluated - when you say ``sin = sound.sample.SineWave(440)``, no sine waves have been calculated.
Instead, the ``sin`` variable now knows how to calculate the amplitude of the output signal at any given point in time.
The interface for this is ``.amplitude(x)``, which is present on any subclass of the ``Signal`` class.
``x`` is in frames, a unit of time bound to the sample rate (default: 44100 frames/sec).

Now, you can use most common binary operators to combine sounds from this library.
If you were to create a triangle wave ``tri = sound.sample.TriangleWave(660)`` and mix the two sounds together ``result = (sin + tri) / 2``, result is now the sound made by mixing together a 440Hz sine wave and a 660Hz triangle wave, equalized to not exceed the maximum intensity allowable.
Still no sound data has been calculated.
You can think of ``result`` as a node in an AST (abstract syntax tree)::


            divide
           /      \
         sum       2
        /   \
       sin  tri

When you go to calculate the actual sound data for this signal by calling ``result.amplitude(x)`` (this is what sound.play does), the divide node asks for the amplitude at that frame from the sum, and the sum asks for the amplitude at that frame from the sine and triangle waves.
The relevant code for this process is in ``sound/sample.py`` and ``sound/signal.py``.

This allows us to understand what happens when you call ``.purify()``::

          purify
            |
            |
          signal

The purifier is just another AST node with a signal as its source, but it additionally acts as a caching layer.
It ensures that the signal is only ever asked for frame amplitudes in order, and that never asks the signal for the same frame twice.

Now, imagine that we have a digitar instance, which is impure. ``pluck = sound.sample.Digitar(440)``.
If we attempt to reuse this sample, for example to compose a sound which is two plucks one after the other (``twoplucks = pluck + (pluck >> 0.5)`` (note that the shift operators take a sound and delay it in time by the given number of seconds)), we might run into some problems with the impurity of this sound::

          sum
         /   \
      pluck  delay
            /     \
         pluck    0.5

When we attempt to play this sound, it takes an absurd amount of time to render, and then the resulting noise is not at all what we wanted.
This is because of the internal state of the pluck object!
Rendering proceeds as normal for the first 0.5 seconds, then slows to a crawl when we start to render the second pluck.
This is because we are using the same impure object twice.
When we ask for a given frame from the sum node, it asks for the corresponding frame from pluck and delay.
Then, delay asks for a different frame from pluck.
The result is that the requests to pluck alternate back and forth in time, and when an impure sound is asked for a frame that is before the frame it is expecting to render next, it must rewind to the beginning and render each frame from the start to the requested frame.
This means that the time complexity of this render operation has gone from linear to quadratic.

The two solutions to this are to use two different Digitar instances for the two plucks, or to use the purified pluck.
This way, the pluck object never has to rewind, since the earlier frames have been cached.

Back to business - Envelopes
----------------------------

So we can now generate tones in various wave types, and because I showed you how we overloaded the + and / binary operators, you can do additive synthesis.
But these sounds are still infintely long and at constant volume.
To make interesting sounds, we need envelopes.

Envelopes (``sound.envelope``) implement the same Signal interface as Samples.
The main envelopes provided are ADSR, Decay, and Line.
They do pretty much what they sound like!
If you want to know how to use them precisely, look at their docstrings - you can do this by typing in the python interpreter ``help(sound.envelope.Line)``, or in the IPython interpreter, typing ``sound.envelope.Line?``::

   In [1]: import sound

   In [2]: sound.envelope.Line?
   Init signature: sound.envelope.Line(self, start, end, duration)
   Docstring:
   A linear line running from start[1] to end[2] in a given time[3] in seconds.

   *--__                   [1]
        *--__
             *--__
                  *--__    [2]
          [3]
   File:           ~/proj/cs/cs130g/sound-machine/sound/envelope.py
   Type:           type

   In [3]:

So if we wanted a really basic envelope for a sound lasting half a second that decays linearly, we'd say ``line = sound.envelope.Line(1, 0, 0.3)``.

Now that we have the envelope, let's use it!
We want to envelope this sound: ``sin = sound.sample.SineWave(440)``
So we just multiply the sound by the envelope: ``result = sin * line``.

That sounds pretty good!

Filters
-------

This library has a lot of room to grow in the filters department.
The currently implemented filters are high pass, low pass (both with very primitive algorithms), FM synth, ring modulator (AM synth), and pitch shift.
If you've been following along with this guide, it shouldn't be too hard to figure out how to use these filters - each of them acts as an AST node over other signals.

For a full list of the filters and how to use each of them, look at the API docs.

Abstract harder - Instruments and Notes
---------------------------------------

So now that we can make interesting sounds, we want to assemble them into music - that's kind of hard right now, since it's super awkward to do these AST constructions by hand.
This library comes with several predefined instruments in the ``sound.instrument`` module.
Each instrument is a class whose instances may be used to produce notes.

Let's use an electric bass as an example. ``bass = sound.instrument.ElectricBass()``.
Now we can play a note! ``bass.note(220).play()``

However, if we actually look at what ``bass.note()`` returns, we can see that it's an instance of a special class called ``Note``.
This class implements the ``Signal`` interface and adds timing information to the sound.

To illustrate this, let's look at a new binary operator that is overloaded on ``Signal`` objets, ``&``, the and operator.
This is a concatenation operator, taking two signals and putting them end-to-end.
It will fail entirely on infinite-length signals.

.. code-block:: python

   note = sound.sample.SineWave(440) * sound.envelope.Line(1, 0, 0.3)
   (note & note & note & note).play()

This works, but if you wanted to make music with it, you'd be in for a hard time.
Now, with the note abstraction:

.. code-block:: python

   # The arguments to note are source, note value in beats, and length of a beat in samples
   # 120 bpm = 2 beats/sec, sample rate = 44100 frames/sec
   note2 = sound.note.Note(note, 1, 44100/2)
   (note2 & note2 & note2 & note2).play()

Now the notes are played to a beat!
This is what the Note abstraction does - it changes the binary operator overloads to work in terms of beats, not in terms of seconds or samples.
As another example, we used the ``>>`` operator earlier to shift a sound by a number of seconds, when you shift a Note object, it instead shifts it by a number of beats.

The tempo of notes produced by an instrument can be set by passing it as an argument to the instrument constructor, in beats per minute.
When the instrument produces notes, they have a value of one beat by default, but you can pass the number of beats at which you want the note to be valued as a second parameter to ``.note()``.

Finally, ``sound.notes`` is a helper module that provides the values of all the notes from C0 to B9 as their frequencies, so you can type ``from sound.notes import *`` and then you can just use the names of notes in place of passing in frequencies to notes, like ``bass.note(A3)``.
You can get sharps and flats by putting 's' or 'b', respectively, after the note letter, like ``Cs3``.

That's it!
----------

You now know how to synthesize interesting sounds and string them together in ways that are useful for writing music.
Go forth and compose!
