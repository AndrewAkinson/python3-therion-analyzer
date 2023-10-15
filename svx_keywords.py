#!/usr/bin/env python3

"""svx_keywords.py
Python module and wrapper code for extracting survex keywords
from a source data file tree.

For usage see README.md.

Copyright (c) 2023 Patrick B Warren

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

import re, sys
import pandas as pd
from pathlib import Path

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
        self.pattern = None # set in simple grep mode
        self.keyword_char = '*'
        self.comment_char = ';'
        self.keywords = set(['INCLUDE', 'BEGIN', 'END', 'FIX', 'ENTRANCE', 'EQUATE', 'CS'])
        self.schema = {'file':str, 'encoding':str, 'line':int, 'keyword':str,
                       'argument':str, 'path':str, 'full':str}

    # Use a stack to keep track of the include files - items on the
    # stack are tuples of file information.  The initial entry (None,
    # None, ...) acts as a sentinel to stop the iteration.

    def keyword_table(self, trace=False, warn=False, directory_paths=False, preserve_case=False):
        '''Return a table of keywords in the survex tree, as a pandas dataframe'''
        keywords = self.keywords.copy() # make a copy, to modify as next
        keywords = keywords.union(set(['INCLUDE', 'BEGIN', 'END'])) # these should always be there
        stack = [(None, None, 0, '')] # initialise file stack with a sentinel
        records = [] # this will accumulate the results record by record
        svx_path = [] # will be a list of elements extracted from begin..end statements
        p = self.top_level.absolute() if directory_paths else self.top_level # use absolute paths if requested
        fp, line_number, encoding = svx_open(p, trace) # open the file and reset the line counter
        while fp: # will finish when the sentinel is popped off stack
            line, line_number = svx_readline(fp, line_number) # read line and increment the line number counter
            while line: # loop until we run out of lines
                line = line.strip() # remove leading and trailing whitespace then remove comments
                if self.pattern: # simple grep mode
                    match = self.pattern.search(line)
                    if match: # add a result into the table of results
                        record = (p, encoding.upper(), line_number, match.group(), '', '.'.join(svx_path), line.expandtabs()) # avoid tabs here (!!)
                        records.append(record) # add to the growing accumulated data
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
                        else:
                            if warn: # warn of empty BEGIN statement
                                print(f'WARNING: empty BEGIN statement at line {line_number} in {p}')
                    if uc_keyword == 'END': # process an END statement
                        if arguments:
                            end_path = arguments[0].lower() # again lower case
                            begin_path = svx_path.pop() # remove the most recent survey path element
                            if warn and (end_path != begin_path): # issue a warning if it is not actually the same
                                print('WARNING: mismatched BEGIN and END statements:')
                                print(f'BEGIN statement line {begin_line_number} in {p}: {begin_line}')
                                print(f'END statement line {line_number} in {p}: {line}')
                        else:
                            if warn: # warn of empty END statement
                                print(f'WARNING: empty END statement at line {line_number} in {p}')
                    if uc_keyword == 'INCLUDE': # process an INCLUDE statement
                        stack.append((p, fp, line_number, encoding)) # push the path, pointer, line number and encoding onto stack
                        filename = ' '.join(arguments).strip('"').replace('\\', '/') # remove any quotes and replace backslashes
                        p = Path(p.parent, filename).with_suffix('.svx') # the new path (add the suffix if not already present)
                        fp, line_number, encoding = svx_open(p, trace) # open the file and reset the line counter
                line, line_number = svx_readline(fp, line_number) # read next line and increment the line number counter
            fp.close() # we ran out of lines for the file being currently processed
            p, fp, line_number, encoding = stack.pop() # back to the including file (this pop always returns, because of the sentinel)

        return pd.DataFrame(records, columns=self.schema.keys()).astype(self.schema)

    
# The following are used in colorized strings below and draws on
# https://stackoverflow.com/questions/5947742/how-to-change-the-output-color-of-echo-in-linux

NC = '\033[0m'
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
BLUE = '\033[0;34m'
PURPLE = '\033[0;35m'
CYAN = '\033[0;36m'

# Note that colorization of keywords only works if the table has been
# constructed using the 'preserve_case' attribute above.  In
# colorizing the keywords, we first create a new column in the
# dataframe 'cfull' which colorizes the keyword or match in the line.

def stringify(df, color=False, paths=False, keyword_char='*', grep_mode=False):
    '''Return a pandas series of strings given the keyword table'''
    if color:
        df['cfull'] = df.apply(lambda r: r.full.replace(r.keyword, f'{RED}{r.keyword}{NC}'), axis='columns')
        if paths:
            ser = df.apply(lambda r: f'{PURPLE}{r.file}{CYAN}:{GREEN}{r.line}{CYAN}:{BLUE}{r.path}{CYAN}:{NC}{r.cfull}', axis='columns')
        else:
            ser = df.apply(lambda r: f'{PURPLE}{r.file}{CYAN}:{GREEN}{r.line}{CYAN}:{NC}{r.cfull}', axis='columns')
        if not grep_mode:
            ser = ser.apply(lambda el: el.replace(f'{RED}', '')) # remove the color change in front of the keyword
            ser = ser.apply(lambda el: el.replace(keyword_char, f'{RED}{keyword_char}')) # and reinsert before keyword character
            ser = ser.apply(lambda el: el.replace(f'{NC}{RED}', f'{RED}')) # simplify
        df.drop('cfull', axis='columns', inplace=True) # tidy up
    else:
        if paths:
            ser = df.apply(lambda r: f'{r.file}:{r.line}:{r.path}:{r.full}', axis='columns')
        else:
            ser = df.apply(lambda r: f'{r.file}:{r.line}:{r.full}', axis='columns')
    return ser

# Here we use the pandas value_counts function to count numbers of
# keywords.  This returns a series which is here converted to a
# dataframe with appropriately named columns.

def summarize(df, path, color=False):
    '''Return a pandas series of strings for a summary of the keyword table'''
    df_summary = df.keyword.value_counts().reset_index(name='total').rename(columns={'index': 'keyword'})
    if color:
        ser = df_summary.apply(lambda r: f'{PURPLE}{path}{CYAN}:{RED}{r.keyword}{CYAN}:{NC}{r.total}', axis='columns')
    else:
        ser = df_summary.apply(lambda r: f'{path}:{r.keyword}:{r.total}', axis=1)
    return ser

def summary(df, path, keywords, color=False, extra=None):
    '''Return a string summarizing the results'''
    keyword_list = '|'.join(sorted(keywords))
    if color:
        summary = f'{PURPLE}{path}{CYAN}:{RED}{keyword_list}{CYAN}:{NC} {len(df)} records found'
    else:
        summary = f'{path}:{keyword_list}: {len(df)} records found'
    if extra:
        if color:
            summary = summary + f'{YELLOW}{extra}'
        else:
            summary = summary + extra
    return summary

# Wrapper code below here

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description='Analyze a survex data source tree.')
    parser.add_argument('svx_file', help='top level survex file (.svx)')
    parser.add_argument('-v', '--verbose', action='store_true', help='be verbose about which files are visited')
    parser.add_argument('-w', '--warn', action='store_true', help='warn about oddities such as empty begin/end statements')
    parser.add_argument('-d', '--directories', action='store_true', help='record absolute directories instead of relative ones')
    parser.add_argument('-k', '--keywords', default=None, help='a set of keywords (comma-separated, case insensitive) to use instead of default')
    parser.add_argument('-a', '--additional-keywords', default=None, help='a set of keywords (--ditto--) to add to the default')
    parser.add_argument('-e', '--excluded-keywords', default=None, help='a set of keywords (--ditto--) to exclude from the default')
    parser.add_argument('-t', '--totals', action='store_true', help='print totals for each keyword')
    parser.add_argument('-s', '--summarize', action='store_true', help='print a one-line summary')
    parser.add_argument('-g', '--grep', default=None, help='pattern to match (switch to grep mode)')
    parser.add_argument('-i', '--ignore-case', action='store_true', help='ignore case (when in grep mode)')
    parser.add_argument('-p', '--paths', action='store_true', help='include survex path when printing to terminal')
    parser.add_argument('-c', '--color', action='store_true', help='colorize printed results')
    parser.add_argument('-q', '--quiet', action='store_true', help='only print warnings and errors (in case of -o only)')
    parser.add_argument('-o', '--output', help='(optional) output to spreadsheet (.ods, .xlsx)')
    args = parser.parse_args()

    # For the time being assume the comment character (;) and keyword
    # character (*) are the defaults.  This can be fixed if it ever
    # becomes an issue.

    analyzer = Analyzer(args.svx_file) # create a new instance

    if args.grep: # simple grep mode
        
        flags = re.IGNORECASE if args.ignore_case else 0
        analyzer.pattern = re.compile(args.grep, flags=flags)
        analyzer.keywords = set() # an empty set
        args.totals = args.summarize = False
        args.oputput = None

    else:

        if args.keywords:
            analyzer.keywords = set(args.keywords.upper().split(','))

        if args.additional_keywords:
            to_be_added = set(args.additional_keywords.upper().split(','))
            analyzer.keywords = analyzer.keywords.union(to_be_added)

        if args.excluded_keywords:
            to_be_removed = set(args.excluded_keywords.upper().split(','))
            analyzer.keywords = analyzer.keywords.difference(to_be_removed)

    preserve_case = (not args.output) and (not args.summarize) and (not args.totals)

    df = analyzer.keyword_table(trace=args.verbose, warn=args.warn,
                                directory_paths=args.directories, preserve_case=preserve_case)

    # The convoluted logic here hopefully does the expected thing if
    # the user selects multiple options.  In particular one can use -t
    # to report totals as well as -o to save to a spreadsheet.

    if len(df):
        if args.totals or args.summarize:
            if args.totals:
                for el in summarize(df, analyzer.top_level, color=args.color):
                    print(el)
            if args.summarize and not args.output:
                print(summary(df, analyzer.top_level, analyzer.keywords, color=args.color))
        if args.output:
            df.to_excel(args.output, index=False)
            if not args.quiet or args.summarize:
                print(summary(df, analyzer.top_level, analyzer.keywords, color=args.color, extra=f' > {args.output}'))
        else:
            if not args.totals and not args.summarize:
                for el in stringify(df, paths=args.paths, color=args.color, grep_mode=args.grep):
                    print(el)
    else:
        if not args.quiet and not args.grep:
            print(summary(df, analyzer.top_level, analyzer.keywords, color=args.color))
        if args.grep:
            sys.exit(1) # reproduce what grep returns if there are no matches
