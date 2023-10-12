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

def svx_encoding(p):
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

def svx_open(p, trace):
    '''open a survex file and reset line counter'''
    encoding = svx_encoding(p)
    fp = p.open('r', encoding=encoding)
    if trace:
        print(f'Entering {p} ({encoding})')
    line_number = 0
    return fp, line_number, encoding

def svx_readline(fp, line_number):
    '''read a line from the survex file and increment line counter'''
    return fp.readline(), line_number+1

def extract_keyword_arguments(clean, keywords, keyword_char):
    '''Extract a keyword and arguments from a cleaned up line'''
    if clean and clean[0] == keyword_char: # detect keyword by presence of keyword character
        clean_list = clean[1:].split() # drop the keyword char and split on white space
        for keyword in keywords: # identify the keyword from the list of possible ones
            if clean_list[0].lower() == keyword:
                keyword = clean_list[0] # the first entry, preserving case
                arguments = clean_list[1:] # the rest is the argument
                break # break out of for loop at this point
        else: # terminal clause in for loop
            keyword, arguments = None, [] # the default position
    else: # line did not start with the keyword character
        keyword, arguments = None, [] # the default position
    return keyword, arguments

class Analyzer:

    # The idea is that we may wish to trim or augment the possible
    # keywords being tracked.  The schema is used to set the column
    # titles and data types in the dataframe.  If it is changed,
    # matching changes should be made to the 'row =' line below.
    
    def __init__(self, use_extra=False, comment_char=';', keyword_char='*'):
        keywords = set(['begin', 'end', 'fix', 'entrance', 'equate', 'cs'])
        extra_keywords = set(['export', 'date', 'flags']) # could be changed
        self.keywords = keywords.union(extra_keywords) if use_extra else keywords
        self.comment_char = comment_char
        self.keyword_char = keyword_char
        self.schema = {'file':str, 'encoding':str, 'line':int, 'keyword':str,
                       'argument(s)':str, 'path':str, 'full':str}

    # Use a stack to keep track of the include files - items on the
    # stack are tuples of file information.  The initial entry (None,
    # None, ...) acts as a sentinel to stop the iteration.

    def analyze(self, svx_file, trace=False, absolute_paths=False):
        self.keywords.add('include') # this should always be present
        stack = [(None, None, 0, '')] # initialised with a sentinel
        rows = [] # accumulate the results row by row
        svx_path = [] # list of elements extracted from begin...end statements
        p = Path(svx_file).with_suffix('.svx') # add the suffix if not already present 
        self.top_level = p # record this
        if absolute_paths: # use absolute path if requested
            p = p.absolute()
        fp, line_number, encoding = svx_open(p, trace) # open the file and reset the line counter
        while fp: # will finish when the sentinel is encountered
            line, line_number = svx_readline(fp, line_number) # read line and increment the line number counter
            while line: # loop until we run out of lines
                line = line.strip() # remove leading and trailing whitespace then remove comments
                clean = line.split(self.comment_char)[0].strip() if self.comment_char in line else line
                keyword, arguments = extract_keyword_arguments(clean, self.keywords, self.keyword_char) # preserving case
                if keyword: # rejected if none found
                    row = (p, encoding.upper(), line_number, keyword.upper(),
                           ' '.join(arguments), '.'.join(svx_path), line.expandtabs()) # for sanity, avoid tabs here (!!)
                    rows.append(row) # add to the growing accumulated data
                    if keyword.upper() == 'BEGIN': # process a BEGIN statement (force lower case)
                        if arguments:
                            begin_path = arguments[0].lower() # lower case here (may be fixed in subsequent versions)
                            svx_path.append(begin_path)
                        else: # empty BEGIN statement
                            print(f'WARNING: empty BEGIN statement at line {line_number} in {p}')
                        begin_line_number, begin_line = line_number, line # keep a copy for debugging errors
                    if keyword.upper() == 'END': # process an END statement
                        if arguments:
                            end_path = arguments[0].lower() # again lower case
                            begin_path = svx_path.pop()
                            if end_path != begin_path:
                                print('WARNING: mismatched BEGIN and END statements:')
                                print(f'BEGIN statement line {begin_line_number} in {p}: {begin_line}')
                                print(f'END statement line {line_number} in {p}: {line}')
                        else: # empty END statement
                            print(f'WARNING: empty END statement at line {line_number} in {p}')
                    if keyword.upper() == 'INCLUDE': # process an INCLUDE statement
                        stack.append((p, fp, line_number, encoding)) # push the current path, pointer, line number and encoding onto stack
                        filename = ' '.join(arguments).strip('"').replace('\\', '/') # remove any quotes and replace backslashes
                        wd = p.parent # the current working directory
                        p = Path(wd, filename).with_suffix('.svx') # the new path (add the suffix if not already present)
                        fp, line_number, encoding = svx_open(p, trace) # open the file and reset the line counter
                line, line_number = svx_readline(fp, line_number) # read line and increment the line number counter
            fp.close() # we ran out of lines for the file being currently processed
            p, fp, line_number, encoding = stack.pop() # back to the including file (this pop always returns, because of the sentinel)

        return pd.DataFrame(rows, columns=self.schema.keys()).astype(self.schema)
