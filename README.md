# jirareport
Creates better reports than JIRA.

### Installation
You should use [virtualenv](https://github.com/pypa/virtualenv).

Run ``pip install -r requirements.txt`` to install all dependencies.

### Usage
``jirareport.py [OPTIONS] COMMAND [ARGS]``

### Options
The script automatically prompts for omitted but required options (like password):

``-s, --server TEXT`` URL to JIRA server.  
``-u, --user TEXT`` Username to log into JIRA.  
``-p, --password TEXT`` Password to log into JIRA.  
``-c, --customfield TEXT`` JIRA internal field name for issue estimation.

### Commands
``burndown PATH`` ([example](https://github.com/dprokscha/jirareport/blob/master/examples/burndown.svg))  
Creates a burndown chart from the chosen sprint. The generated SVG file will be written to ``PATH``. The green line *Completed* shows all completed issues. Completed means the issue status is *Done* or the estimation of issues decreased while the issue status was not *Open*. The red line *Unplanned* shows all unplanned issues. The line increases if issues were added or the estimation of issues increased during a sprint. It decreases if issues were removed or the estimation decreased (only if issue status is *Open*). A sprint seems to be healthy, if the line never goes up or down. 

``dailybusiness``  
Analysis all comments of the chosen sprint for time tracks and sums them. The format of a valid time track is ``[..h..m]`` (e.g. ``[5h35m]``). This can be used by all developers who wants to track their "Hey Joe!" tasks in a single issue by time.

### Example
``jirareport.py -s https://localhost -u dprokscha -c customfield_10002 burndown output.svg``

### License
Copyright (c) 2015 Daniel Prokscha

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
