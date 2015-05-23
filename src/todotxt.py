#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Example `todo.txt` file structure:

    (A) 2015-05-30 Flieger nach Sardinien #urlaub

"""

from __future__ import print_function, unicode_literals

import re
import sys

if str == bytes:
    import io
    open = io.open

from dateutil.parser import parse as parsedate


CONTEXT_RE = re.compile(r'(^|\s)@(?P<context>\w+)')
DATE_RE = re.compile(r'^(?P<date>\d{2}(\d{2})?-\d{1,2}-\d{1,2})'
                     r'([_T ](?P<time>\d{1,2}:\d{2}(:\d{2})?))?\s+', re.I)
METADATA_RE = re.compile(r'(^|\s)(?P<key>\w+):(?P<value>\S+)')
PRIORITY_RE = re.compile(r'^\((?P<priority>\w)\)\s+')
TAG_RE  = re.compile(r'(^|\s)#(?P<tag>\w+)')


class TodoItem(object):
    """Represents a line in a todo.txt, i.e. an item on the todo list."""
    _attrs = ('priority', 'task', 'done', 'contexts', 'tags', 'metadata',
              'due', 'completed')

    def __init__(self, *args, **kwargs):
        for name in self._attrs:
            setattr(self, name, kwargs.get(name))

        for i, arg in enumerate(args):
            setattr(self, self._attrs[i], arg)

    def __str__(self):
        """Return string representation of instance."""
        return '<TodoItem(\n' + ''.join('    %s=%r\n' % (
            attr, getattr(self, attr)) for attr in self._attrs) + ')>'


class TodoList(list):
    """Parser/Emitter for a todo.txt file and container for TodoItems."""

    def __init__(self, *args, **kw):
        super(TodoList, self).__init__(*args, **kw)

    def _xform_key(self, key):
        """Transform metadata key name.

        May be overwritten by a sub-class. The default implementation returns
        a lowercase version of the key, making metadata keys case-insensitive.

        """
        return key.lower()

    @classmethod
    def fromfile(cls, filename="todo.txt", encoding="utf-8"):
        """Create instance by parsing todo.txt file.

        @param filename: input file name/path (default: 'todo.txt')
        @param encoding: input file encoding (default: 'utf-8')

        @return TodoTxt: new TodoTxt instance

        """
        with open(filename, encoding=encoding) as infile:
            todotxt = cls()
            todotxt.parse(infile)
            return todotxt

    def parse(self, stream):
        """Parse input stream and set instance elements to list of TodoItems.

        @param stream: file-like object to read todo lines from

        @return None

        """
        for line in stream:
            line = line.strip()
            item = TodoItem()

            # parse 'done' status
            if line.startswith('x '):
                item.done = True
                line = line[2:].strip()
            else:
                item.done = False

            # parse priority
            m = PRIORITY_RE.search(line)
            if m:
                item.priority = m.group('priority')
                line = line[m.end():]

            # parse optional completion date
            if item.done:
                m = DATE_RE.search(line)
                if m:
                    item.completed = parsedate(m.group('date') + ' ' +
                                               (m.group('time') or ''))
                    line = line[m.end():]

            # parse optional due date
            m = DATE_RE.search(line)
            if m:
                item.due = parsedate(m.group('date') + ' ' +
                                     (m.group('time') or ''))
                line = line[m.end():]
            else:
                # if there is only one date, it is the due date,
                # not the completion date
                item.due = item.completed
                item.completed = None

            # extract all contexts
            item.contexts = set()
            def collect(match):
                item.contexts.add(match.group('context'))

            line = CONTEXT_RE.sub(collect, line).strip()

            # extract all tags
            item.tags = set()
            def collect(match):
                item.tags.add(match.group('tag'))

            line = TAG_RE.sub(collect, line).strip()

            # extract all metadata key:value pairs
            item.metadata = {}
            def collect(match):
                key = self._xform_key(match.group('key'))
                item.metadata[key] = match.group('value')

            line = METADATA_RE.sub(collect, line).strip()

            # The remainder of the line is the task text
            item.task = line
            self.append(item)


def main(args=None):
    """Main program entry point."""
    t = TodoList.fromfile('todo.txt')
    for ti in t:
        print(ti)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
