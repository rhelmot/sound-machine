#!/usr/bin/env python

from setuptools import setup
import platform
import os

# If we're in pypy, make sure to install the version of numpy that actually works!!!!
# I tried for like an hour and could figure out a clean way to make setuptools do this :|
if platform.python_implementation() == 'PyPy':
     try:
          import numpy  # pylint: disable=unused-import
     except ImportError:
          os.system('pip install "git+https://bitbucket.org/pypy/numpy.git#egg=numpy"')

setup(name='sound-machine',
      version='1.0',
      description='Sound and music synthesis library in pure python',
      author='Andrew Dutcher',
      author_email='andrew@andrewdutcher.com',
      url='https://github.com/rhelmot/sound-machine',
      license='MIT',
      packages=['sound'],
      install_requires=['sounddevice', 'numpy', 'progressbar']
     )
