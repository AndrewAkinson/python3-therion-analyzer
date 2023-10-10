## Python code to analyze survex data source file(s)

_Current version:_

v0.1 - pre-release development

### Summary

This repository contains a python package and wrapper code to analyze
survex data source files (`.svx` file trees), walking through the
include statements and extracting all the starred commands such as
begin...end statements, station fixes, entrance tags, and co-ordinate
system declarations.  The extracted data is returned as a pandas
dataframe which can be exported to a spreadsheet (wrapper code).

An example survex data source file tree for the Dow-Prov system can be
found in the example directory of companion repository
qgis3-survex-import.

### Usage

To be written...

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
