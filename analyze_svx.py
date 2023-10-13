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
parser.add_argument('-v', '--verbose', action='store_true', help='be verbose about which files are visited')
parser.add_argument('-d', '--directories', action='store_true', help='record absolute directories instead of relative ones')
parser.add_argument('-k', '--keywords', default=None, help='a set of keywords (comma-separated, case insensitive) to use instead of default')
parser.add_argument('-a', '--additional-keywords', default=None, help='a set of keywords (--ditto--) to add to the default')
parser.add_argument('-e', '--excluded-keywords', default=None, help='a set of keywords (--ditto--) to exclude from the default')
parser.add_argument('-t', '--totals', action='store_true', help='print totals for each keyword')
parser.add_argument('-s', '--summarize', action='store_true', help='print a one-line summary')
parser.add_argument('-q', '--quiet', action='store_true', help='only print warnings and errors (in case of -o only)')
parser.add_argument('-p', '--paths', action='store_true', help='include survex path in output')
parser.add_argument('-c', '--color', action='store_true', help='colorize printed results')
parser.add_argument('-o', '--output', help='(optional) output to spreadsheet (.ods, .xlsx)')
args = parser.parse_args()

# cases when results are written directly to terminal

preserve_case = (not args.output) and (not args.summarize) and (not args.totals)

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

df = analyzer.keyword_table(trace=args.verbose, directory_paths=args.directories, preserve_case=preserve_case)

# The convoluted logic here hopefully does the expected thing if the
# user selects multiple options.  In particular one can use -t to
# report totals as well as -o to save to a spreadsheet.

if len(df):
    if args.totals or args.summarize:
        if args.totals:
            for el in sa.summarize(df, analyzer.top_level, color=args.color):
                print(el)
        if args.summarize and not args.output:
            print(sa.summary(df, analyzer.top_level, analyzer.keywords, color=args.color))
    if args.output:
        df.to_excel(args.output, index=False)
        if not args.quiet or args.summarize:
            print(sa.summary(df, analyzer.top_level, analyzer.keywords, color=args.color, extra=f' > {args.output}'))
    else:
        if not args.totals and not args.summarize:
            for el in sa.stringify(df, paths=args.paths, color=args.color):
                print(el)
else:
    if not args.quiet:
        print(sa.summary(df, analyzer.top_level, analyzer.keywords, color=args.color))
