# -*- coding:utf-8 -*-
#
# release.py - release information for the PyDoDo distribution
#
"""Python client for todo list organization using todo.txt format.

This is currently pre-alpha code but the parser in the `todotxt` module is
already able to parse `todo.txt`_ files.

.. _todo.txt: https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format

"""

name = 'PyDoDo'
version = '0.1a1'
description = __doc__.splitlines()
keywords = 'todo,gtd'
author = 'Christopher Arndt'
author_email = 'chris@chrisarndt.de'
url = 'http://chrisarndt.de/projects/%s/' % name
repository = 'https://github.com/SpotlightKid/%s.git' % name.lower()
download_url = url + 'download/'
license = 'MIT License'
platforms = 'POSIX, Windows, MacOS X'
long_description = "\n".join(description[2:]) % locals()
description = description[0]
classifiers = """\
Development Status :: 2 - Pre-alpha
Environment :: MacOS X
Environment :: Win32 (MS Windows)
Intended Audience :: Developers
Intended Audience :: End users
License :: OSI Approved :: MIT License
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: MacOS :: MacOS X
Programming Language :: Python
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Topic :: Multimedia :: Sound/Audio :: MIDI
Topic :: Software Development :: Libraries :: Python Modules
"""
classifiers = [c.strip() for c in classifiers.splitlines()
    if c.strip() and not c.startswith('#')]
try: # Python 2.x
    del c
except: pass
