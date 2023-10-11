## Python code to analyze survex data source files

_Current version:_

v1.0 - initial working version

### Summary

This repository contains a python package and wrapper code to analyze
survex data source file trees (`.svx` files), following the
`*include` statements and extracting star commands such as
`*begin`...`*end` statements, station fixes, entrance tags, and co-ordinate
system declarations.  The extracted data is returned as a pandas
dataframe which can be exported to a spreadsheet (see wrapper code).

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

The dataframe has one row for each command and contains columns for:

* the file name;
* the detected character encoding of the file (UTF-8, ISO-8859-1, ASCII);
* the line number in the file;
* the current survex path;
* the actual command (`INCLUDE`, `BEGIN`, `END`, etc);
* the argument of the command;
* the original line in the survex file.

The default is to report details only for the following subset of
possible survex commands: `*include`, `*begin`, `*end`, `*fix`, `*entrance`,
`*equate`, `*cs out`, and `*cs`.  If instantiated with the option
`use_extra=True` then the command set is extended to include
`*export`, `*date`, and `*flags`.

Finer control can be achieved by modifying the `star_commands`
property of the instantiated object, before running the analysis.  For
example to look for just `*begin` and `*end` statements use
```python
import survex_analyzer as sa
...
analyzer = sa.Analyzer() # create an instance
analyzer.star_commands = ['*begin', '*end']
df = analyzer.analyze(top_level_svx_file)
...
```
Note that `*include` gets added to the list of commands if it is not
present already.  Usually though it will be better to stick with the
default list of star commands and filter the resulting dataframe, using
for example
```python
df[(df['COMMAND'] == 'BEGIN') | (df['COMMAND'] == 'END')]
```

The full specification of the relevant module functions is as follows.  To instantiate use

```python
Analyzer(use_extra=False, comment_char=';')
```
Here, `use_extra` as already indicated adds some extra star commands,
and `comment_char` allows the character used to separate comments in
survex files to be specified if different from the default.

To analyse a file use
```python
df = analyze(top_level_svx_file, trace=False, absolute_paths=False)
```
Here, setting `trace=True` makes the function call be verbose about
which files it is visitng, and `absolute_paths=True` reports absolute
rather paths as file names, otherwise they are relative to the
directory containing the top level survex file.

#### With the command line tool

The command line tool `analyze_svx.py` provides a convenient interface
to the underlying module.  For example to analyze the Dow-Prov example
run
```bash
./analyze_svx.py example/DowProv -o dp.ods
```
This saves the dataframe to a spreadsheet (`dp.ods`) in open document format
(`.ods`); it can then be loaded into excel or libreoffice.

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
  -e, --extra           include extra star commands
  -s, --silent          run silently
  -o OUTPUT, --output OUTPUT
                        optionally, output to spreadsheet (.ods, .xlsx)
```
Actually, it is not necessary to include the file extension when
specifying the top level survex file; this is added automatically if
missing as in the above example.

### Technical notes

Some complications arise because survex is quite liberal about what
input it can take.

One of these concerns the character encoding for the data files.  In
some cases these can contain characters which are not recognised as
UTF-8 or ASCII, but are in the extended ASCII character set, such as
the degree &deg; symbol.  To handle this the module attempts to
determine the character encoding for each file it is asked to read
from, before parsing the file.

Another issue concerns the use of capitalisation for star commands
(ignored by survex) versus file names (required on unix systems at
least) and survex path itself (forced to lower case by survex).  Thus
`*Begin` is equally valid as `*begin`.  The parsing algorithm is
designed to work around these issues.

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
