#!/usr/bin/env python
"""This is a shim to allow GitHub to detect the package.

Taken from https://github.com/Textualize/rich
Build is done with poetry.
"""

import setuptools

if __name__ == "__main__":
    setuptools.setup(name="aiovlc")
