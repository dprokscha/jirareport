# jirareport
Creates better reports than JIRA.

### Installation
You should use [virtualenv](https://github.com/pypa/virtualenv).

Run ``pip install -r requirements.txt`` to install all dependencies.

### Usage
``jirareport.py [OPTIONS] COMMAND [ARGS]``

### Options
* ``-s, --server TEXT`` URL to JIRA server.
* ``-u, --user TEXT`` Username to log into JIRA.
* ``-p, --password TEXT`` Password to log into JIRA.

### Commands
``burndown PATH``  
Creates a burndown chart from the chosen sprint. The generated SVG file will be written to ``PATH``.

### License
Copyright (c) 2015 Daniel Prokscha

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
