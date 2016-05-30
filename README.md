# sound-machine

Python library for musical audio synthesis

## Requirements

The [sounddevice](http://python-sounddevice.readthedocs.org/) python module, which in turn requires NumPy.

If you're doing real-time synthesis with this library, you will probably want to use PyPy, a jitting interpreter for python.

## Usage

This is a python module. To use it you should put your shell in the root directory of this repository, then launch a python shell, then type `import sound`. It would be a good idea to do this in the IPython shell so you can use tab-autocomplete to browse the module contents.

## Examples

```python
import sound
from sound.notes import *

sound.play(sound.instrument.KickDrum().note(0))
sound.play(sound.instrument.Xylophone().note(A4))
sound.play(sound.instrument.SquareViolin().note(A3, 4))
sound.play(sound.instrument.Bell().note(A3))
sound.play(sound.instrument.Bell2().note(A3))
sound.test_scale(sound.instrument.sine_hit)

d = sound.instrument.KickDrum().note
t = sound.instrument.Shaker().note
sound.play(sound.filter.LoopImpure(lambda: (d(0) & d(0) & d(0) & d(0)) + ((t(0) >> 1) & (t(0) >> 1)), 2))
```

Take a look at the content of `instrument.py` to see how these things happen.

Additionally, a few examples can be found in the `examples` directory.

## Purity

The idea behind some things being pure and others being impure has to do with whether you're allowed to access samples out-of-order. If a sound, for example an infinite-impulse-response filter, needs to keep state about what it's output previously, you may not ask about its samples out-of-order.

Some filters have two versions, designed to work with pure or impure sounds. The Sequence and Loop filters are good examples of this.
