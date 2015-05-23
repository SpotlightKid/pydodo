#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup file for the PyDoDo distribution."""

import sys

from os.path import exists, join

from setuptools import setup
from distutils.dist import DistributionMetadata

SRC_DIR = "src"

# Add custom distribution meta-data, avoids warning when running setup
DistributionMetadata.repository = None

# read meta-data from release.py
setup_opts = {}
release_info = join(SRC_DIR, 'release.py')
exec(compile(open(release_info).read(), release_info, 'exec'), {}, setup_opts)

setup(
    py_modules = ['todotxt', 'dropbox_client'],
    package_dir = {'': 'src'},
    # On systems without a RTC (e.g. Raspberry Pi), system time will be the
    # Unix epoch when booted without network connection, which makes zip fail,
    # because it does not support dates < 1980-01-01.
    zip_safe=True,
    **setup_opts
)
