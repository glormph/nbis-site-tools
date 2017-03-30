# NBIS site tools

This repo contains YML files that are to be displayed on the NBIS website.
The website runs Jekyll and the tool YMLs are stored in a collection.
The YML files are generated by running a script locally on a tool stub
JSON file, which is also stored here. This can be run on every tool update
and downloads the tool from [bio.tools](http://bio.tools), adding some
extra information. In most cases only the bio.tools ID is needed for this
but sometimes a tool will not get fetched if you do not also give the 
biotools version.

The script `tool_validator.py` is dependent on the PyYAML 
library, which can be installed by issueing `pip install PyYAML`, preferably
in a virtual environment. The script uses `urllib2` which is a python2 module
and will not work with python3.

To create a JSON file for the script one can use the `toolstub.json` file as
an example. Then run:
`python tool_validator.py your_tool.json`
And copy the resulting `your_tool.yml` to the NBIS tool site folder.
