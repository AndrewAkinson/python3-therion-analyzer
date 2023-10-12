#!/usr/bin/env python3

"""svx_analyzer.py
Python module for extracting survex keywords from a source data file tree.

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
    success = False
    for encoding in ['utf-8', 'iso-8859-1', 'ascii']: # list of options to try
        with p.open('r', encoding=encoding) as fp:
            try:
                fp.readlines() # we don't need to capture the output here
            except UnicodeDecodeError:
                pass
            else: # if we didn't fail, we found something that works
                success = True
                break
    if not success:
        raise UnicodeDecodeError(f'Couldnt determine the character encoding for {p}')
    return encoding

def extract_keyword_arguments(clean, keywords, keyword_char):
    '''Extract a keyword and arguments from a cleaned up line, returning None if not present'''
    if clean and clean[0] == keyword_char: # detect keyword by presence of keyword character
        clean_list = clean[1:].split() # drop the keyword char and split on white space
        if clean_list[0].lower() == 'cs' and clean_list[1].lower() == 'out': # special treatment for 'cs out'
            keyword = ' '.join(clean_list[:2]) # join the first two entries with a space (preserve case)
            arguments = clean_list[2:] # the remainder is the argument
        else:
            for keyword in keywords: # identify the keyword from the list of possible ones
                if clean_list[0].lower() == keyword:
                    keyword = clean_list[0] # the first entry, preserving case
                    arguments = clean_list[1:] # the rest is the argument
                    break
            else: # terminal clause of for loop -- the keyword is not in the provided list
                keyword, arguments = None, []
    else: # the cleaned up line did not start with a keyword character
        keyword, arguments = None, []
    return keyword, arguments

class Analyzer:

    # The idea is that we may wish to trim or augment the possible
    # keywords being tracked.  The schema is used to set the column
    # titles and data types in the dataframe.  If it is changed,
    # matching changes should be made to the 'row =' line below.
    
    def __init__(self, use_extra=False, comment_char=';', keyword_char='*',
                 keywords=['include', 'begin', 'end',
                           'fix', 'entrance', 'equate', 'cs out', 'cs'],
                 extra_keywords=['export', 'date', 'flags']):
        self.keywords = (keywords + extra_keywords) if use_extra else keywords
        self.comment_char = comment_char
        self.keyword_char = keyword_char
        self.schema = {'file':str, 'encoding':str, 'line':int, 'keyword':str,
                       'argument(s)':str, 'path':str, 'full':str}

    # Use a stack to keep track of the include files - items on the
    # stack are tuples of file information.  The initial entry (None,
    # None, ...) acts as a sentinel to stop the iteration.

    def analyze(self, svx_file, trace=False, absolute_paths=False):
        if 'include' not in self.keywords: # this should always be present
            self.keywords.insert(0, 'include') # as the first element
        stack = [(None, None, 0, '')] # initialised with a sentinel
        rows = [] # accumulate the results row by row
        svx_path = [] # list of elements extracted from begin...end statements
        p = Path(svx_file).with_suffix('.svx') # add the suffix if not already present and work with absolute paths
        if absolute_paths:
            p = p.absolute()
        wd = p.parent # the working directory
        encoding = character_encoding(p) # figure out the character encoding for the top level file
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
                keyword, arguments = extract_keyword_arguments(clean, self.keywords, self.keyword_char) # preserving case
                if keyword: # rejected if none found
                    row = (p, encoding.upper(), line_number, keyword.upper(),
                           ' '.join(arguments), '.'.join(svx_path), line.expandtabs())# for sanity, avoid tabs in the dataframe entries (!!)
                    if keyword.lower() == 'begin' and arguments: # process a begin statement (force lower case)
                        svx_path.append(arguments[0].lower()) # force lower case here (may be fixed in subsequent versions)
                        begin_line_number, begin_line = line_number, line # keep a copy for debugging errors
                    if keyword.lower() == 'end' and arguments: # process an end statement
                        previous_argument = svx_path.pop()
                        if previous_argument != arguments[0].lower():
                            print(f'BEGIN statement line {begin_line_number} in {p}: {begin_line}')
                            print(f'END statement line {line_number} in {p}: {line}')
                            raise Exception('mismatched begin...end statements')
                    rows.append(row) # add to the growing accumulated data
                    if keyword.lower() == 'include': # process an include statement
                        stack.append((p, fp, line_number,encoding)) # push the current path, pointer, line number and encoding onto stack
                        filename = ' '.join(arguments).strip('"').replace('\\', '/') # remove quotes and replace backslashes
                        wd = p.parent # the new working directory
                        p = Path(wd, filename).with_suffix('.svx') # the new path (add the suffix if not already present)
                        encoding = character_encoding(p)
                        fp = p.open('r', encoding=encoding)
                        if trace:
                            print(f'Visiting {p} ({encoding})')
                        line_number = 0 # reset the line number counter
                line = fp.readline() # read the next line if there is one
                line_number = line_number + 1 # and increment the line counter
            fp.close() # we ran out of lines for the file being currently processed
            p, fp, line_number, encoding = stack.pop() # back to the including file (this pop always returns, because of the sentinel)

        return pd.DataFrame(rows, columns=self.schema.keys()).astype(self.schema)
