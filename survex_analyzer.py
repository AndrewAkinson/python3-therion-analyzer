#!/usr/bin/env python3

"""svx_analyzer.py
Python module for analyzing survex source data file tree.

For usage see README.md.

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

def character_encoding(p):
    '''Try to figure out the character encoding that works for a file'''
    for encoding in ['utf-8', 'iso-8859-1', 'ascii']: # list of options to try
        with p.open('r', encoding=encoding) as fp:
            try:
                fp.readlines() # we don't need to capture the output here
            except UnicodeDecodeError:
                pass
            else: # if we didn't fail, we found something that works
                break
    return encoding

def extract_star_command(clean, star_commands):
    '''Extract a star command from a cleaned up line, returning None if not present'''
    commands = [star_command for star_command in star_commands if clean.lower().startswith(star_command)]
    if '*cs out' in commands: # special treatment because of the space
        return ' '.join(clean.split()[:2]) # join the first two entries with a space (preserve case)
    elif commands:
        return clean.split()[0] # this preserves case
    else:
        return None

class Analyzer:

    # The idea is that we may wish to trim or augment the possible
    # star commands.  The schema should be left alone unless matching
    # changes are made to the 'row =' line below.
    
    def __init__(self, use_extra=False, comment_char=';',
                 star_commands=['*include', '*begin', '*end', '*fix', '*entrance', '*equate', '*cs out', '*cs'],
                 extra_star_commands=['*export', '*date', '*flags']):
        self.star_commands = (star_commands + extra_star_commands) if use_extra else star_commands
        self.comment_char = comment_char
        self.schema = {'file':str, 'encoding':str, 'line':int, 'survex_path':str, 'COMMAND':str, 'argument':str, 'full':str}

    # Use a stack to keep track of the include files - items on the
    # stack are tuples of file paths and open file pointers.  The
    # initial entry (None, None, ...) is used as a sentinel to stop
    # the iteration.

    def analyze(self, svx_file, trace=False, absolute_paths=False):
        if '*include' not in self.star_commands: # this should always be present
            self.star_commands.insert(0, '*include') # as the first element
        stack = [(None, None, 0, '')] # initialised with the sentinel
        rows = [] # accumulate the results row by row
        svx_path = [] # list of elements extracted from begin...end statements
        p = Path(svx_file).with_suffix('.svx') # add the suffix if not already present and work with absolute paths
        if absolute_paths:
            p = p.absolute()
        wd = p.parent # the working directory as an absolute path
        encoding = character_encoding(p)
        fp = p.open('r', encoding=encoding)
        if trace:
            print(f'Entering {p} ({encoding})')
        line_number = 0 # keep track of the line numbers
        while fp: # will finish when the sentinel is encountered
            line = fp.readline() # read the next line
            line_number = line_number + 1 # increment the line number counter
            while line: # loop until we run out of lines
                line = line.strip() # remove leading and trailing whitespace then remove comments
                clean = line.split(self.comment_char)[0].strip() if self.comment_char in line else line
                star_command = extract_star_command(clean, self.star_commands)
                if star_command: # rejected if none found
                    argument = clean.removeprefix(star_command).strip() # again strip whitespace
                    row = (p, encoding.upper(), line_number, '.'.join(svx_path),
                           star_command.removeprefix('*').upper(), argument.expandtabs(), line.expandtabs())
                    if line.lower().startswith('*begin'): # process a begin statement (force lower case)
                        svx_path.append(argument.lower()) # force lower case here
                        begin_line_number, begin_line = line_number, line # keep a copy for debugging errors
                    if line.lower().startswith('*end'): # process an end statement
                        previous_argument = svx_path.pop()
                        if previous_argument != argument.lower():
                            print(f'BEGIN statement line {begin_line_number} in {p}: {begin_line}')
                            print(f'END statement line {line_number} in {p}: {line}')
                            raise Exception('mismatched begin...end statements')
                    rows.append(row) # add to the growing accumulated data
                    if line.lower().startswith('*include'): # process an include statement
                        stack.append((p, fp, line_number,encoding)) # push the current path, pointer, line number and encoding onto stack
                        filename = argument.strip('"').replace('\\', '/') # remove quotes and replace backslashes
                        wd = p.parent # the new working directory
                        p = Path(wd, filename).with_suffix('.svx') # the new path (add the suffix if not already present)
                        encoding = character_encoding(p)
                        fp = p.open('r', encoding=encoding)
                        if trace:
                            print(f'Entering {p} ({encoding})')
                        line_number = 0 # reset the line number counter
                line = fp.readline() # read the next line if there is one
                line_number = line_number + 1 # and increment the line counter
            fp.close() # we ran out of lines for the file being currently processed
            p, fp, line_number, encoding = stack.pop() # back to the including file (this pop always returns, because of the sentinel)

        return pd.DataFrame(rows, columns=self.schema.keys()).astype(self.schema)

