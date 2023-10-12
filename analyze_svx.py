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
parser.add_argument('-a', '--absolute-paths', action='store_true', help='request absolute paths in dataframe')
parser.add_argument('-e', '--extra', action='store_true', help='include extra keywords')
parser.add_argument('-q', '--quiet', action='store_true', help='only report warnings and errors')
parser.add_argument('-o', '--output', help='optionally, output to spreadsheet (.ods, .xlsx)')
args = parser.parse_args()

analyzer = sa.Analyzer(use_extra=args.extra) # create a new instance
df = analyzer.analyze(args.svx_file, trace=args.trace, absolute_paths=args.absolute_paths)

if args.output:
    df.to_excel(args.output, index=False)
    if not args.quiet:
        keywords = ','.join(analyzer.keywords).upper()
        print(f'Keywords {keywords} in {analyzer.top_level} extracted to {args.output} ({len(df)} rows)')
else:
    print(df)
