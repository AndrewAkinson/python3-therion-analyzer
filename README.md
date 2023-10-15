## Python code to analyze survex data source files

_Current version:_

v1.0 - initial working version

### Summary

This repository contains python code to analyze survex data source
file trees (`.svx` files):

* `svx_keywords.py` extracts selected keywords and associated data;
* `svx_grep.py` is a generic search tool along the lines of the unix `grep` utility.

Both parse the source file and follow file inclusion statements.  For
the first, extracted keywords can include begin and end statements,
station fixes, entrance tags, co-ordinate system declarations, and
others as desired. 

A survex data source file tree for the Dow-Prov system is given in the
`DowProv` directory.

For example, to extract fixed points and co-ordinate system
definitions use
```
$ ./svx_keywords.py DowProv/DowProv -c -k cs,fix
DowProv/DowProv.svx:41:*cs OSGB:SD
DowProv/DowProv.svx:42:*cs out EPSG:7405
DowProv/DowCave/DowCave.svx:16:*fix entrance 98378 74300 334
DowProv/ProvidencePot/ProvidencePot.svx:13:*fix entrance 99213 72887 401
DowProv/HagDyke.svx:14:*fix W 98981 73327 459
```
On a terminal screen, this output would be colorized (`-c` option).

### Installation

* Either clone or download the repository, or just download the two
key python scripts `svx_keywords.py` and `svx_grep.py`;

* Put these somewhere where they can be found, for instance in the top
level working directory for a survey project.

### Usage

#### As command line tools

Used as a command line tool, `svx_keywords.py` provides a convenient
interface to the underlying functionality which is based around
building a pandas dataframe containing the requested information.  For
example, to save this dataframe as a spreadsheet for the Dow-Prov case, use
```bash
./svx_keywords.py DowProv/DowProv -o dp.ods
```
The resulting spreadsheet, here in open document format (`.ods`), can be
loaded into Excel or libreoffice.

The full usage is

```
usage: svx_keywords.py [-h] [-v] [-d] [-k KEYWORDS] [-a KEYWORDS]
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
If keywords are not explicitly specified, the default is to report
details for the following set: `INCLUDE`, `BEGIN`, `END`, `FIX`,
`ENTRANCE`, `EQUATE`, and `CS` (which includes `CS OUT`).

If `-o` is not specified the command writes the extracted information
as a list of file names and line numbers with the associated lines to
terminal output.  With the `-p` option, additional survey path
information is included.  If additionally `-c` option is present, this
output is colorized like `grep -n` with the path information (if
present) and keywords additionally highlighted.

Summary information can be obtained with the `-t` and `-s` options.
These can be combined with each other, and with `-o` (which always prints
a summary unless `-q` is specified), and colorized by `-c`.

With the `-o` option, the internal pandas dataframe is saved to a
spreadsheet.  The top row is a header row, then there is one row for
each keyword instance, in the order in which they appeared when
parsing the sources.  The columns are

* the file name;
* the detected character encoding of the file (`UTF-8`, `ISO-8859-1`);
* the line number in the file;
* the actual keyword, capitalised (`INCLUDE`, `BEGIN`, `END`, etc);
* the argument(s) following the keyword, if any;
* the current survex path;
* the full original line in the survex file.

The second script `svx_grep.py` reproduces some of the functionality
of the unix `grep` utility in pattern-matching lines in survex source
files.  It differs from regular `grep` because it strictly follows the
include hierarchy, and because it additionally tracks begin and end
statements.  The usage is TO BE COMPLETED...

#### In a python script or jupyter notebook

The script `svx_keywords.py` can also be loaded as a python module in
a python script or jupyter notebook.  The basic usage is
```python
from svx_keywords import Analyzer
...
df = Analyzer('DowProv/DowProv').keyword_table()
...
```
The returned pandas dataframe `df` is stuctured the same way as the
spreadsheet (in fact, it is exported as such in the command line
version).

Here, finer control can be achieved by modifying the `keywords`
property of the instantiated object before running the analysis.  For
example to look for just `BEGIN` and `END` statements use
```python
from svx_keywords import Analyzer
...
analyzer = Analyzer('DowProv/DowProv') # create a named instance
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
In addition to the keywords, the `Analyzer` object has properties
`keyword_char` and `comment_char` which are initialised to `*` and `;`
respectively, but can be changed before calling `keyword_table`.

The function `keyword_table` has some additional boolean flags as
parameters: `trace=True` makes the function call be verbose about
which files it is visiting; `directory_paths=True` reports absolute
directory paths in the table rather than file names relative to the
directory containing the top level survex file; and
`preserve_case=True` reports the actual keywords rather than the
capitalised ones.

Normally one would use `preserve_case=False` (the default) since it
means that the entries in the keyword column of the dataframe are
capitalised and so can be processed without worrying about case
sensitivity.

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
itself so that `* begin` is the same as `*begin`.  Again the code
should handle these cases transparently.  By default, the entries in
the keyword field of the dataframe are converted to upper case to
facilitate further processing, but the case can be preserved if
requested (`preserve_case=True`).  The keyword character (by
default `*`) is not included for the entries in this field.

Generally if a survex file can be successfully processed by `cavern`,
then it ought to be parsable by the present scripts.  The code has
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
