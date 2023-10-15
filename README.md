## Python code to analyze survex data source files

_Current version:_

v1.0 - initial working version

### Summary

The python script `svx_keywords.py` in this repository analyzes survex
data source file trees (`.svx` files).  It can be used to search for
keywords such as file includes, begin and end statements, station fixes, entrance
tags, co-ordinate system declarations, and others as desired.  A
'grep-like' regular expression pattern matching mode is also
available.

The key feature that distinguishes this bespoke utility from generic file
system tools such as `find` and `grep` is that the code parses the
survex source file and follows the file inclusion statements,
reporting results in logical order, and additionally keeping track of
the survex station naming hierarchy of begin/end statements.

For example, to extract fixed points and co-ordinate system
definitions for the Dow-Prov system from the sample survex data source
file tree given in the `DowProv` directory, use
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

* Either clone or download the repository, or just download the 
key python script `svx_keywords.py`;

* put this script somewhere where it can be found,
for instance in the top level working directory for a survey project.

### Usage

#### As a command line tool

For keyword selection, `svx_keywords.py` provides a convenient
interface to the underlying functionality which is based around
building a pandas dataframe containing the requested information.
Alternatively, one can search for a generic regular expression similar
to the unix `grep` command line tool.

The full usage is

```
usage: svx_keywords.py [-h] [-v] [-w] [-d] [-k KEYWORDS] [-a KEYWORDS]
            [-e KEYWORDS] [-t] [-s] [-g GREP]
	    [-i] [-p] [-c] [-q] [-o OUTPUT] svx_file

Analyze a survex data source tree.

positional arguments:
  svx_file                   top level survex file (.svx)

options:
  -h, --help                 show this help message and exit
  -v, --verbose              be verbose about which files are visited
  -w, --warn                 warn about oddities such as empty begin/end statements
  -d, --directories          record absolute directories instead of relative ones
  -k, --keywords             a set of keywords to use instead of default
  -a, --additional-keywords  a set of keywords to add to the default
  -e, --excluded-keywords    a set of keywords to exclude from the default
  -t, --totals               print totals for each keyword
  -s, --summarize            print a one-line summary
  -g GREP, --grep GREP       pattern to match (grep mode)
  -i, --ignore-case          ignore case (grep mode)
  -p, --paths                include survex path when printing to terminal
  -c, --color                colorize printed results
  -q, --quiet                only print warnings and errors (in case of -o only)
  -o, --output               (optional) output to spreadsheet (.ods, .xlsx)
```
The file extension (`.svx`) is supplied automatically if missing, as
in the initial example.

The default action is to search and report all results for keywords
from the following set: `INCLUDE`, `BEGIN`, `END`, `FIX`, `ENTRANCE`,
`EQUATE`, and `CS` (which includes `CS OUT`).

The keyword set can be modified by using the `-k`, `-a` and `-e`
options as follows.  The `-k` option is used to specify an alternative
set of keywords to search for.  The argument should be a
comma-separated list of keywords (case insensitive) with no
additional spaces, for example `-k cs,fix` used in the introductory
example.  The `-a` and `-e` options work similarly, but _modify_ the
default keyword set rather than replacing it.

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

For example, to save this dataframe as a spreadsheet for the Dow-Prov
case, use
```bash
./svx_keywords.py DowProv/DowProv -o dp.ods
```
The resulting spreadsheet, here in open document format (`.ods`), can be
loaded into Excel or libreoffice.

If `-o` is not specified the command writes the extracted information
as a list of file names and line numbers, with the associated lines,
to terminal output.  With the `-p` option, additional survey path
information is included.  Summary information can be obtained with the
`-t` and `-s` options.  These can be combined with each other (and
also with `-o`, which always prints a summary unless `-q` is
specified).  If the `-c` option is present for any of these, the
terminal output is colorized like `grep -n`, with the path information
(if present) and keywords additionally highlighted.

The special 'grep' mode is accessed by specifying `-g`, with a regular
expression, or just a simple string.  In this case, the set of
keywords is ignored, as are the `-s`, `-t` and `-o` options, and all
lines which contain a match are reported to the terminal window, with
the match highlighted. Setting `-i` ignores case in the pattern
matching.  The output is very similar to the standard `grep -n`
alluded to above, with the exception that path information can be
additionally included (`-p` option).  Also, unlike for keywords, if
there are no pattern matches in 'grep' mode, the script returns with
exit code 1 but no lines of output (modeled on the behavior of `grep`
itself).

#### In a python script or jupyter notebook

The script `svx_keywords.py` can also be loaded as a python module in
a python script or jupyter notebook, and run from there to give
direct access to the underlying pandas dataframe which is used to
create the spreadsheet with the `-o` option.  The basic usage is

```python
from svx_keywords import Analyzer
...
df = Analyzer('DowProv/DowProv').keyword_table()
...
```
This employs the default set of keywords listed above, but fine
control can be achieved by modifying the `keywords` property of the
instantiated object before running the analysis.  For example to look
for just `BEGIN` and `END` statements use
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

More details of the constructor and function calls, can be found
inside the script itself.

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
