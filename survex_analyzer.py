#!/usr/bin/env python3

"""svx_analyzer.py
Python module for analyzing survex source data file tree.

Copyright (C) 2023 Patrick B Warren

Email: patrickbwarren@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see
<http://www.gnu.org/licenses/>.

"""

import pandas as pd
from pathlib import Path

class Analyzer:

    def __init__(self,
                 star_commands=['*include', '*begin', '*end', '*fix', '*equate', '*cs out', '*cs', '*export', '*date', '*flags'],
                 schema={'directory':str, 'file':str, 'line':int, 'command':str, 'argument':str, 'full':str},
                 comment_char=';'):
        self.star_commands = star_commands
        self.comment_char = comment_char
        self.schema = schema

    # Use a stack to keep track of the include files - items on the
    # stack are tuples of file paths and open file pointers.  The
    # initial entry (None, None) is used as a sentinel to stop the
    # iteration.

    def analyze(self, svx_file, trace=False):
        stack = [(None, None)] # initialised with the sentinel
        rows = [] # accumulate the results row by row
        p = Path(svx_file).with_suffix('.svx').absolute() # add the suffix if not already present and work with absolute paths
        wd = p.parent # the working directory as an absolute path
        fp = p.open('r')
        if trace:
            print('Analyzing', p)
        while fp: # will finish when the sentinel is encountered
            line = fp.readline() # read the first line
            line_number = 1
            while line:
                line = line.strip() # remove leading and trailing whitespace
                clean = line.split(self.comment_char)[0].strip() if self.comment_char in line else line # remove comments
                recognised_star_commands = list(filter(lambda s: clean.startswith(s), self.star_commands)) # as a list 
                if recognised_star_commands: # rejected if the list is empty
                    star_command = recognised_star_commands.pop() # there should be only one
                    argument = clean.removeprefix(star_command).strip() # again strip whitespace
                    row = (p.parent, p.name, line_number, star_command, argument, line)
                    rows.append(row)
                    if line.startswith('*include'):
                        stack.append((p, fp)) # push the current file path and pointer onto stack
                        filename = argument.strip('"').replace('\\', '/') # remove quotes and replace backslashes
                        wd = p.parent # the new working directory
                        p = Path(wd, filename).with_suffix('.svx') # add the suffix if not already present
                        fp = p.open('r')
                        if trace:
                            print('Analyzing', p)
                line = fp.readline() # read the next line if there is one
                line_number = line_number + 1 # and increment the line counter
            fp.close() # we ran out of lines for the file being currently processed
            p, fp = stack.pop() # return to the including file (this always works, because of the sentinel)

        return pd.DataFrame(rows, columns=self.schema.keys()).astype(self.schema)

