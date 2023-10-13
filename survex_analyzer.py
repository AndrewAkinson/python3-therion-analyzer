#!/usr/bin/env python3

"""survex_parser.py
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

# The following are used in colorized strings below and draws on
# https://stackoverflow.com/questions/5947742/how-to-change-the-output-color-of-echo-in-linux

NC = '\033[0m'
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
BLUE = '\033[0;34m'
PURPLE = '\033[0;35m'
CYAN = '\033[0;36m'

def svx_encoding(p):
    '''Try to figure out the character encoding that works for a file'''
    success = False
    for encoding in ['utf-8', 'iso-8859-1']: # list of options to try
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
            if clean_list[0].upper() == keyword:
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
    # matching changes should be made to the 'record =' line below.
    
    def __init__(self, svx_file):
        '''Instantiate with default properties, given a survex top level file'''
        self.top_level = Path(svx_file).with_suffix('.svx') # add the suffix if not already present
        if not self.top_level.exists():
            raise FileNotFoundError(self.top_level)
        self.keyword_char = '*'
        self.comment_char = ';'
        self.keywords = set(['INCLUDE', 'BEGIN', 'END', 'FIX', 'ENTRANCE', 'EQUATE', 'CS'])
        self.schema = {'file':str, 'encoding':str, 'line':int, 'keyword':str,
                       'argument':str, 'path':str, 'full':str}

    # Use a stack to keep track of the include files - items on the
    # stack are tuples of file information.  The initial entry (None,
    # None, ...) acts as a sentinel to stop the iteration.

    def keyword_table(self, trace=False, directory_paths=False, preserve_case=False):
        '''Return a table of keywords in the survex tree, as a pandas dataframe'''
        keywords = self.keywords.copy() # make a copy, to modify as next
        for keyword in ['INCLUDE', 'BEGIN', 'END']: # these ones should always be there
            keywords.add(keyword) 
        stack = [(None, None, 0, '')] # initialise file stack with a sentinel
        records = [] # this will accumulate the results record by record
        svx_path = [] # will be a list of elements extracted from begin..end statements
        p = self.top_level.absolute() if directory_paths else self.top_level # use absolute paths if requested
        fp, line_number, encoding = svx_open(p, trace) # open the file and reset the line counter
        while fp: # will finish when the sentinel is popped off stack
            line, line_number = svx_readline(fp, line_number) # read line and increment the line number counter
            while line: # loop until we run out of lines
                line = line.strip() # remove leading and trailing whitespace then remove comments
                clean = line.split(self.comment_char)[0].strip() if self.comment_char in line else line
                keyword, arguments = extract_keyword_arguments(clean, keywords, self.keyword_char) # preserving case
                if keyword: # rejected if none found
                    uc_keyword = keyword.upper() # upper case
                    if uc_keyword in self.keywords: # for inclusion in the output, test against the *original* set of keywords
                        record = (p, encoding.upper(), line_number, keyword if preserve_case else uc_keyword,
                               ' '.join(arguments), '.'.join(svx_path), line.expandtabs()) # for sanity, avoid tabs here (!!)
                        records.append(record) # add to the growing accumulated data
                    if uc_keyword == 'BEGIN': # process a BEGIN statement
                        if arguments:
                            begin_path = arguments[0].lower() # lower case here (may be fixed in subsequent versions)
                            svx_path.append(begin_path) # add to the list of survey path elements
                            begin_line_number, begin_line = line_number, line # keep a copy for debugging purposes
                        else: # warn of empty BEGIN statement
                            print(f'WARNING: empty BEGIN statement at line {line_number} in {p}')
                    if uc_keyword == 'END': # process an END statement
                        if arguments:
                            end_path = arguments[0].lower() # again lower case
                            begin_path = svx_path.pop() # remove the most recent survey path element
                            if end_path != begin_path: # issue a warning if it is not actually the same
                                print('WARNING: mismatched BEGIN and END statements:')
                                print(f'BEGIN statement line {begin_line_number} in {p}: {begin_line}')
                                print(f'END statement line {line_number} in {p}: {line}')
                        else: # warn of empty END statement
                            print(f'WARNING: empty END statement at line {line_number} in {p}')
                    if uc_keyword == 'INCLUDE': # process an INCLUDE statement
                        stack.append((p, fp, line_number, encoding)) # push the current path, pointer, line number and encoding onto stack
                        filename = ' '.join(arguments).strip('"').replace('\\', '/') # remove any quotes and replace backslashes
                        p = Path(p.parent, filename).with_suffix('.svx') # the new path (add the suffix if not already present)
                        fp, line_number, encoding = svx_open(p, trace) # open the file and reset the line counter
                line, line_number = svx_readline(fp, line_number) # read next line and increment the line number counter
            fp.close() # we ran out of lines for the file being currently processed
            p, fp, line_number, encoding = stack.pop() # back to the including file (this pop always returns, because of the sentinel)

        return pd.DataFrame(records, columns=self.schema.keys()).astype(self.schema)

        # The following draws on
    # https://stackoverflow.com/questions/5947742/how-to-change-the-output-color-of-echo-in-linux

# Note that colorization of keywords only works if the table has been constructed using the 'preserve_case' attribute above.

def stringify(df, color=False, paths=False, keyword_char='*'):
    '''Return a pandas series of strings given the keyword table'''
    if color:
        df['cfull'] = df.apply(lambda r: r.full.replace(r.keyword, f'{RED}{r.keyword}{NC}'), axis=1)
        if paths:
            ser = df.apply(lambda r: f'{PURPLE}{r.file}{CYAN}:{GREEN}{r.line}{CYAN}:{BLUE}{r.path}{CYAN}:{r.cfull}', axis=1)
        else:
            ser = df.apply(lambda r: f'{PURPLE}{r.file}{CYAN}:{GREEN}{r.line}{CYAN}:{r.cfull}', axis=1)
        ser = ser.apply(lambda el: el.replace('*', f'{RED}{keyword_char}')) # highlight the keyword character
        df.drop('cfull', axis=1, inplace=True) # tidy up
    else:
        if paths:
            ser = df.apply(lambda r: f'{r.file}:{r.line}:{r.path}:{r.full}', axis=1)
        else:
            ser = df.apply(lambda r: f'{r.file}:{r.line}:{r.full}', axis=1)
    return ser

# below here, for testing

if __name__ == "__main__":

    dow_prov = Analyzer('sample/DowProv')
    dow_prov.keywords = set(['CS', 'FIX'])
    df = dow_prov.keyword_table(preserve_case=True)
    for el in stringify(df, color=True):
        print(el)
