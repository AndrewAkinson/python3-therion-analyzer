#!/usr/bin/env python3

"""analyze_svx.py
Wrapper for extracting survex keywords from a source data file tree.

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

import argparse
import pandas as pd
import survex_analyzer as sa

parser = argparse.ArgumentParser(description='Analyze a survex data source tree.')
parser.add_argument('svx_file', help='top level survex file (.svx)')
parser.add_argument('-t', '--trace', action='store_true', help='be verbose about which files are visited')
parser.add_argument('-d', '--directory-paths', action='store_true', help='use absolute directory paths in dataframe')
parser.add_argument('-k', '--keywords', default=None, help='a set of keywords (comma-separated, case insensitive) to use instead of default')
parser.add_argument('-a', '--additional-keywords', default=None, help='a set of keywords (--ditto--) to add to the default')
parser.add_argument('-e', '--excluded-keywords', default=None, help='a set of keywords (--ditto--) to exclude from the default')
parser.add_argument('-q', '--quiet', action='store_true', help='only report warnings and errors')
parser.add_argument('-p', '--paths', action='store_true', help='include survex path when output directly')
parser.add_argument('-c', '--color', action='store_true', help='colorize when output directly')
parser.add_argument('-o', '--output', help='(optional) output to spreadsheet (.ods, .xlsx)')
args = parser.parse_args()

preserve_case = (not args.output) # used for colorizing output below
    
# For the time being assume the comment character (;) and keyword
# character (*) are the defaults.  This can be fixed if it ever
# becomes an issue.

analyzer = sa.Analyzer(args.svx_file) # create a new instance

if args.keywords:
    analyzer.keywords = set(args.keywords.upper().split(','))

if args.additional_keywords:
    to_be_added = set(args.additional_keywords.upper().split(','))
    analyzer.keywords = analyzer.keywords.union(to_be_added)

if args.excluded_keywords:
    to_be_removed = set(args.excluded_keywords.upper().split(','))
    analyzer.keywords = analyzer.keywords.difference(to_be_removed)

df = analyzer.keyword_table(trace=args.trace, directory_paths=args.directory_paths, preserve_case=preserve_case)

keywords = ','.join(sorted(analyzer.keywords))

if  len(df):

    if args.output:

        df.to_excel(args.output, index=False)
        if not args.quiet:
            print(f'{analyzer.top_level}: {keywords}: extracted to {args.output} ({len(df)} records)')

    else:
        
        for el in sa.stringify(df, paths=args.paths, color=args.color):
            print(el)

else:

    if not args.quiet:
        print(f'{analyzer.top_level}: {keywords}: no records found')
