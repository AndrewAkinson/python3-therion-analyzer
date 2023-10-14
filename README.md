## Python code to extract keywords from survex data source files

_Current version:_

v1.0 - initial working version

### Summary

This repository contains a python package and wrapper code to extract
selected keywords and associated data from survex data source file
trees (`.svx` files), following the file inclusion statements.
Extracted keywords can include begin and end statements, station
fixes, entrance tags, co-ordinate system declarations, and others as
desired.  The extracted keywords and data are returned as a pandas
dataframe which can be exported to a spreadsheet (see wrapper code).
Alternatively, the wrapper can write file names, line numbers, and
actual lines, directly to terminal output for easy visual inspection.

A survex data source file tree for the Dow-Prov system is given in the
`DowProv` directory.  To show the fixed points and co-ordinate system
definitions for this system one would have, for example,
```
$ ./analyze_svx.py DowProv/DowProv -c -k cs,fix
DowProv/DowProv.svx:41:*cs OSGB:SD
DowProv/DowProv.svx:42:*cs out EPSG:7405
DowProv/DowCave/DowCave.svx:16:*fix entrance 98378 74300 334
DowProv/ProvidencePot/ProvidencePot.svx:13:*fix entrance 99213 72887 401
DowProv/HagDyke.svx:14:*fix W 98981 73327 459
```
On a terminal screen, this output would be colorized (`-c` option).

### Installation

Either clone or download the repository and put the python scripts
where they can be found, for instance in the top level working
directory for a survey project. The python scripts are:

* `survex_parser.py` : a python module implementing the main functionality;
* `analyze_svx.py` : a wrapper around the module implementing a command line utility.

### Usage

#### In a python script or jupyter notebook

Basic use (example):
```python
import survex_analyzer as sa
...
df = sa.Analyzer(top_level_svx_file).keyword_table()
...
```
The returned pandas dataframe `df` can be further analysed programatically,
or exported to a spreadsheet for inspection.

The dataframe has one record for each keyword that is tracked and contains fields for:

* the file name;
* the detected character encoding of the file (`UTF-8`, `ISO-8859-1`);
* the line number in the file;
* the actual keyword, capitalised (`INCLUDE`, `BEGIN`, `END`, etc);
* the argument(s) following the keyword, if any;
* the current survex path;
* the full original line in the survex file.

The default is to report details for the following set of
survex keywords: `INCLUDE`, `BEGIN`, `END`, `FIX`,
`ENTRANCE`, `EQUATE`, and `CS` (which includes `CS OUT`). 

Finer control can be achieved by modifying the `keywords`
property of the instantiated object before running the analysis.  For
example to look for just `BEGIN` and `END` statements use
```python
import survex_analyzer as sa
...
analyzer = sa.Analyzer(top_level_svx_file) # create a named instance
analyzer.keywords = set(['BEGIN', 'END']) # this must be a SET and UPPERCASE
df = analyzer.keyword_table()
...
```
The same result though can be obtained by sticking with the default
set of keywords and filtering the resulting dataframe, using
```python
df[(df['keyword'] == 'BEGIN') | (df['keyword'] == 'END')]
```
or more succinctly
```python
df[(df.keyword == 'BEGIN') | (df.keyword == 'END')]
```

The full specification of the relevant functions is as follows.  To
instantiate use

```python
analyzer = sa.Analyzer(top_level_svx_file)
```
where `top_level_svx_file` is the top level `.svx` file you want to
start the analysis with (the file extension is added if it is not
already there).

The object thus created has properties `keyword_char` and `comment_char`
which are initialised to `*` and `;` respectively, but can be changed
at this point.

To obtain the keyword table do
```python
df = analyzer.keyword_table(trace=False, directory_paths=False, preserve_case=False)
```
Here, setting `trace=True` makes the function call be verbose about
which files it is visiting; `directory_paths=True` reports absolute
directory paths in the table rather than file names relative to the
directory containing the top level survex file; and `preserve_case=True`
reports the actual keywords rather than the capitalised ones.  The
function returns a pandas dataframe as indicated above.  

Normally one would run this with `preserve_case=False` (the default)
since it means that the entries in the keyword field of the
dataframe are all capitalised and so can be filtered more efficiently.

#### With the command line tool

The command line tool `analyze_svx.py` provides a convenient interface
to the underlying module.  For example to generate a spreadsheet for
the Dow-Prov case
```bash
./analyze_svx.py DowProv/DowProv -o dp.ods
```
The dataframe is saved to `dp.ods` in open document format
(`.ods`); it can then be loaded into Excel or libreoffice.

The full usage is

```
usage: analyze_svx.py [-h] [-v] [-d] [-k KEYWORDS] [-a KEYWORDS]
            [-e KEYWORDS] [-t] [-s] [-q] [-p] [-c] [-o OUTPUT] svx_file

Analyze a survex data source tree.

positional arguments:
  svx_file                   top level survex file (.svx)

options:
  -h, --help                 show this help message and exit
  -v, --verbose              be verbose about which files are visited
  -d, --directories          record absolute directories instead of relative ones
  -k, --keywords             a set of keywords to use instead of default
  -a, --additional-keywords  a set of keywords to add to the default
  -e, --excluded-keywords    a set of keywords to exclude from the default
  -t, --totals               print totals for each keyword
  -s, --summarize            print a one-line summary
  -q, --quiet                only print warnings and errors (in case of -o only)
  -p, --paths                include survex path when in output
  -c, --color                colorize printed results
  -o, --output               (optional) output to spreadsheet (.ods, .xlsx)
```
The file extension (`.svx`) is supplied automatically if missing, as
in the initial example.

The sets of keywords should be comma-separated, with no additional
spaces.  Keywords are case-insensitive at this point, so that `-k
begin,end` is the same as `-k BEGIN,END`, and so on.  The `-a` and
`-e` options work similarly, but modify the default keyword set rather
than replacing it.  Thus to omit all the `EQUATE` commands from the
default set, for example, use `-e EQUATE` or `-e equate`, and so on.

If `-o` is not specified the command writes the table as a list of
file names and line numbers with the associated lines to terminal
output.  With the `-p` option, additional survey path information is
included.  If additionally `-c` option is present, this output is
colorized like `grep -n` with the path information (if present) and
keywords additionally highlighted.

Summary information can be obtained with the `-t` and `-s` options.
These can be combined with each other, and with `-o` (which always prints
a summary unless `-q` is specified), and colorized by `-c`.

### Technical notes

Some complications arise because survex is quite liberal about what
input it can take.

One of these concerns the character encoding for the data files.  In
some cases these can contain characters which are not recognised as
UTF-8 but are in the extended ASCII character set, such as
the degree &deg; symbol in ISO-8859-1.  To handle this the module
attempts to determine the character encoding for each file it is asked
to read from, before parsing the file.  This is done rather crudely by
slurping the entire contents of the file and looking for decoding
exceptions.  Currently the only encodings tested for are 'UTF-8' and
'ISO-8859-1' (aka Latin 1).

Another issue concerns the use of capitalisation for keywords, file
names, and the survex path itself.  The parsing algorithm is designed
to work around these issues BUT it is assumed that it is acceptable
for survey path names introduced by begin and end statements to be
forced to lower case.  For keywords, capitalisation is irrelevant, for
example `*BEGIN` and `*Begin` are equally valid as `*begin`.  Also,
there can be space between the keyword character and the keyword
itself so that `* begin` is the same as `*begin`.  Again the parser
should handle these cases transparently.  By default, the entries in
the keyword field of the dataframe are converted to upper case to
facilitate further processing, but the case can be preserved if
requested (`preserve_case=True`).  The keyword character (by
default `*`) is not included for the entries in this field.

Generally if a survex file can be successfully processed by `cavern`,
then it ought to be parsable by the present scripts.  The parser has
been checked against the Leck-Masongill data set and the
EaseGill-Pippikin data set, as well as the Dow-Prov case.

### Open issues

* Intercept `set` commands, to set comment and keyword characters.
* Intercept `case preserve|toupper|tolower` and interpret accordingly.

If there are issues parsing survex files with these scripts, please
let me know!  Also, feel free to request additional features.

### Copying

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

### Copyright

This program is copyright &copy; 2023 Patrick B Warren.  
