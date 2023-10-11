## Python code to analyze survex data source files

_Current version:_

v1.0 - initial working version

### Summary

This repository contains a python package and wrapper code to analyze
survex data source file trees (`.svx` files), following the `*include`
statements and extracting keywords such as `*begin`...`*end`
statements, station fixes, entrance tags, and co-ordinate system
declarations.  The extracted data is returned as a pandas dataframe
which can be exported to a spreadsheet (see wrapper code).

An example survex data source file tree for the Dow-Prov system is
given in the `example` directory.

### Installation

Either clone or download the repository and put the python scripts
where they can be found, for instance in the top level working
directory for a survey project. The python scripts are:

* `survex_analyzer.py` : a python module implementing the main functionality;
* `analyze_svx.py` : a wrapper around the module implementing a command line utility.

### Usage

#### In a python script or jupyter notebook

Basic use:
```python
import survex_analyzer as sa
...
analyzer = sa.Analyzer() # create an instance
df = analyzer.analyze(top_level_svx_file)
...
```
The returned pandas dataframe can be further analysed programatically,
or exported to a spreadsheet for inspection.

The dataframe has one row for each keyword that is tracked and contains columns for:

* the file name;
* the detected character encoding of the file (UTF-8, ISO-8859-1, ASCII);
* the line number in the file;
* the current survex path;
* the actual keyword (`INCLUDE`, `BEGIN`, `END`, etc);
* the argument(s) following the keyword;
* the original line in the survex file.

The default is to report details only for the following subset of
possible survex keywords: `*include`, `*begin`, `*end`, `*fix`, `*entrance`,
`*equate`, `*cs`, and `*cs out`.  If instantiated with the option
`use_extra=True` then the keyword set is extended to include
`*export`, `*date`, and `*flags` (this may be changed at a later date).

Finer control can be achieved by modifying the `keywords`
property of the instantiated object before running the analysis.  For
example to look for just `*begin` and `*end` statements use
```python
import survex_analyzer as sa
...
analyzer = sa.Analyzer() # create an instance
analyzer.keywords = ['*begin', '*end']
df = analyzer.analyze(top_level_svx_file)
...
```
Note that `*include` gets added to the list of keywords if it is not
present already.  Usually though it will be better to stick with the
default list of keywords and filter the resulting dataframe, using
for example
```python
df[(df['keyword'] == 'BEGIN') | (df['keyword'] == 'END')]
```

The full specification of the relevant module functions is as follows.  To instantiate use

```python
Analyzer(use_extra=False, comment_char=';')
```
Here, `use_extra` as already indicated adds some extra keywords,
and `comment_char` allows the character used to separate comments in
survex files to be specified if different from the default.

To analyse a file use
```python
df = analyze(top_level_svx_file, trace=False, absolute_paths=False)
```
Here, setting `trace=True` makes the function call be verbose about
which files it is visitng, and `absolute_paths=True` reports absolute
paths as file names, otherwise they file names are relative to the
directory containing the top level survex file.

#### With the command line tool

The command line tool `analyze_svx.py` provides a convenient interface
to the underlying module.  For example to analyze the Dow-Prov example
run
```bash
./analyze_svx.py example/DowProv -o dp.ods
```
This saves the dataframe to a spreadsheet (`dp.ods`) in open document format
(`.ods`); it can then be loaded into Excel or libreoffice.

The full usage is

```
usage: analyze_svx.py [-h] [-t] [-a] [-e] [-s] [-o OUTPUT] svx_file

Analyze a survex data source tree.

positional arguments:
  svx_file              top level survex file (.svx)

options:
  -h, --help            show this help message and exit
  -t, --trace           be verbose about which files are visited
  -a, --absolute-paths  report absolute paths in spreadsheet
  -e, --extra           include extra keywords
  -s, --silent          run silently
  -o OUTPUT, --output OUTPUT
                        optionally, output to spreadsheet (.ods, .xlsx)
```
The file extension (`.svx`) is supplied automatically if missing, as
in the above example.

### Technical notes

Some complications arise because survex is quite liberal about what
input it can take.

One of these concerns the character encoding for the data files.  In
some cases these can contain characters which are not recognised as
UTF-8 or ASCII, but are in the extended ASCII character set, such as
the degree &deg; symbol in ISO-8859-1.  To handle this the module
attempts to determine the character encoding for each file it is asked
to read from, before parsing the file.  This is done rather crudely by
slurping the entire contents of the file and looking for decoding
exceptions.  Currently the only encodings tested for are 'UTF-8',
'ISO-8859-1' (aka Latin 1), and 'ASCII'.

Another issue concerns the use of capitalisation for star commands
(ignored by survex) versus file names (required on unix systems at
least) and survex path itself (by default, forced to lower case by
survex).  Thus `*Begin` is equally valid as `*begin`.  The parsing
algorithm is designed to work around these issues BUT it is assumed
that survey names are forced to lower case.

Generally if a survex file can be successfully processed by `cavern`,
then it ought to be parsable by the present scripts.  This has been
checked against the Leck-Masongill data set, and the EaseGill-Pippikin
data set, as well as the Dow-Prov example.  A final issue is that
there should be NO spaces between the `*` and the survex command.
Although this is something that seems to be tolerated by survex, it
has not been implemented here.

### Open issues

* Intercept `*case preserve|toupper|tolower` and interpret accordingly.
* Allow the keyword character to be specifiable, rather than assuming `*`.
* Intercept `*set` commands, such keywords are not introduced by `*`.

If there are issues parsing survex files with these scripts, please
let me know!  Also feel free to request additional features.

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
