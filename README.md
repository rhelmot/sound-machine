# sound-machine

Python library for musical audio synthesis

## Requirements

The [sounddevice](http://python-sounddevice.readthedocs.org/) python module, which in turn requires NumPy.

## Usage

This is a python module. To use it you should put your shell in the root directory of this repository, then launch a python shell, then type `import sound`. It would be a good idea to do this in the IPython shell so you can use tab-autocomplete to browse the module contents.

## Examples

```python
import sound
sound.play(sound.instrument.kickdrum())
sound.play(sound.instrument.xylophone(440))
sound.play(sound.instrument.square_violin(220, 4))
sound.play(sound.instrument.bell(220))
sound.test_scale(sound.instrument.sine_hit)

d = sound.instrument.kickdrum
t = sound.instrument.shaker
sound.play(sound.filter.LoopImpure(lambda: sound.filter.Sequence(((d(), 0), (d(), 0.4), (d(), 0.8), (d(), 1.2), (t(), 0), (t(), 0.8))), 1.6))
```

Take a look at the content of `instrument.py` to see how these things happen.

## Purity

The idea behind some things being pure and others being impure has to do with whether you're allowed to access samples out-of-order. If a sound, for example an infinite-impulse-response filter, needs to keep state about what it's output previously, you may not ask about its samples out-of-order.

Some filters are designed to work with pure or impure sounds. The Sequence and Loop filters are good examples of this.
