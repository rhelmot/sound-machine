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
```

Take a look at the content of `instrument.py` to see how these things happen.
