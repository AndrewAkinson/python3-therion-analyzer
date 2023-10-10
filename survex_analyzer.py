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

def open_with_character_encoding(p, trace=False):
    '''Return a file pointer after figuring out the character encoding for a file'''
    for encoding in ['UTF-8', 'iso-8859-1', 'ascii']: # list of options to try
        with p.open('r', encoding=encoding) as fp:
            try:
                lines = fp.readlines()
            except UnicodeDecodeError:
                pass
            else: # if we didn't fail, we found a possible encoding
                break
    if trace:
        print(f'Analyzing {p} ({encoding})')
    return p.open('r', encoding=encoding), encoding # return the file pointer AND the encoding

def extract_star_command(clean, star_commands):
    '''Extract a star command from a cleaned up line, returning None if not present'''
    commands = [star_command for star_command in star_commands if clean.lower().startswith(star_command)]
    return clean.split()[0] if commands else None # this preserves case

class Analyzer:

    # The idea is that we may wish to trim or augment the possible
    # star commands.  The schema should be left alone unless matching
    # changes are made to the 'row =' line below.
    
    def __init__(self,
                 star_commands=['*include', '*begin', '*end', '*fix', '*equate', '*cs', '*cs out', '*export', '*date', '*flags'],
                 # schema={'directory':str, 'file':str, 'line':int, 'survex_path':str, 'COMMAND':str, 'argument':str, 'full':str},
                 schema={'file':str, 'line':int, 'survex_path':str, 'COMMAND':str, 'argument':str, 'full':str},
                 comment_char=';'):
        self.star_commands = star_commands
        self.comment_char = comment_char
        self.schema = schema

    # Use a stack to keep track of the include files - items on the
    # stack are tuples of file paths and open file pointers.  The
    # initial entry (None, None) is used as a sentinel to stop the
    # iteration.

    def analyze(self, svx_file, trace=False, absolute_paths=False):
        stack = [(None, None)] # initialised with the sentinel
        rows = [] # accumulate the results row by row
        svx_path = [] # list of elements extracted from begin...end statements
        p = Path(svx_file).with_suffix('.svx') # add the suffix if not already present and work with absolute paths
        if absolute_paths:
            p = p.absolute()
        wd = p.parent # the working directory as an absolute path
        fp, encoding = open_with_character_encoding(p, trace=trace)
        while fp: # will finish when the sentinel is encountered
            line = fp.readline() # read the first line
            line_number = 1
            while line:
                line = line.strip() # remove leading and trailing whitespace then remove comments
                clean = line.split(self.comment_char)[0].strip() if self.comment_char in line else line
                star_command = extract_star_command(clean, self.star_commands)
                if star_command: # rejected if the none found
                    argument = clean.removeprefix(star_command).strip() # again strip whitespace
                    row = (p, line_number, '.'.join(svx_path), star_command.removeprefix('*').upper(), argument, line.expandtabs())
                    if line.lower().startswith('*begin'): # process a begin statement (use lower case)
                        print('>> BEGIN encountered', p, line_number, '.'.join(svx_path), line)
                        svx_path.append(argument.lower()) # use lower case here
                        begin_line_number, begin_line = line_number, line # keep a copy for debugging errors
                    if line.lower().startswith('*end'): # process an end statement
                        print('>> END encountered', p, line_number, '.'.join(svx_path), line)
                        previous_argument = svx_path.pop()
                        if previous_argument != argument.lower():
                            print(f'BEGIN statement line {begin_line_number} in {p}: {begin_line}')
                            print(f'END statement line {line_number} in {p}: {line}')
                            raise Exception('mismatched begin...end statements')
                    rows.append(row) # add to the growing accumulated data, then ..
                    if line.lower().startswith('*include'): # .. process an include statement
                        stack.append((p, fp)) # push the current file path and pointer onto stack
                        filename = argument.strip('"').replace('\\', '/') # remove quotes and replace backslashes
                        wd = p.parent # the new working directory
                        p = Path(wd, filename).with_suffix('.svx') # add the suffix if not already present
                        fp, encoding = open_with_character_encoding(p, trace=trace)
                line = fp.readline() # read the next line if there is one
                line_number = line_number + 1 # and increment the line counter
            fp.close() # we ran out of lines for the file being currently processed
            p, fp = stack.pop() # return to the including file (this always works, because of the sentinel)

        return pd.DataFrame(rows, columns=self.schema.keys()).astype(self.schema)

