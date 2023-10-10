#!/usr/bin/env python3

"""analyze_svx.py
Wrapper code for python module for analyzing survex source data file tree.

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

parser = argparse.ArgumentParser(description='Analyze a survex data source.')
parser.add_argument('svx_file', help='starting survex file (.svx)')
parser.add_argument('-t', '--trace', action='store_true', help='report which files are visited')
parser.add_argument('-a', '--absolute-paths', action='store_true', help='report absolute paths')
parser.add_argument('-s', '--silent', action='store_true', help='run silently')
parser.add_argument('-o', '--output', help='optionally, output to spreadsheet (.ods, .xlsx)')
args = parser.parse_args()

analyzer = sa.Analyzer() # create a new instance
df = analyzer.analyze(args.svx_file, trace=args.trace, absolute_paths=args.absolute_paths)

if args.output:
    df.to_excel(args.output, index=False)
    if not args.silent:
        print(f'Written summary to {args.output}')
else:
    print(df)
