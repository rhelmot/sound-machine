# sound-machine

This is a library to do audio synthesis and music composition.
Its goal is to make the interface as simple as possible to use with as short a learning curve as possible.

It is written in pure python, and supports both python 2 and 3.

## Installation

```bash
$ pip install sound-machine
```

You _probably_ want to use the PyPy interpreter, expecially if you expect to do any sort of real-time synthesis.
Here are some instructions on setting up a virtual environment with pypy.

First, install pypy and the pypy-dev package (or equivilant) from your OS's package manager.
Then, make sure you have `virtualenvwrapper` installed.
Finally:

```bash
mkvirtualenv --python=`which pypy` sound
pip install sound-machine
```

At time of writing, the python package index is suffering some pretty nasty technical difficulties, so if the above install commands don't work for you, the `pip install sound-machine` line can be replaced with `pip install git+https://github.com/rhelmot/sound-machine.git`.

## Usage

This is a python module.
To use it, launch a python shell, then type `import sound`.
It would be a good idea to do this in the IPython shell so you can use tab-autocomplete to browse the module contents.

## Documentation

Read it [here](https://cs.ucsb.edu/~dutcher/sound-machine/)!
