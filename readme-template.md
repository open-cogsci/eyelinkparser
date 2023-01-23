# Python EyeLinkParser

Sebastiaan Mathôt and contributors <br />
Copyright 2016-2023  <br />
http://www.cogsci.nl/smathot

## About

The `python-eyelinkparser` module provides a framework to parse EyeLink data files in `.asc` format, that is, the format that you get after converting an `.edf` file with `edf2asc`. This module is mostly for personal use, and is not very well documented.

## Installation

```
pip install eyelinkparser
```

## Expected format

The parser assumes monocular recording.


## Expected messages

By default, the parser assumes that particular messages are sent to the logfile. If you use different messages, you need to override functions in `_eyelinkparser.EyeLinkParser`. This is not explained here, but you can look in the source code to see how it works.

Trial start:

	start_trial [trialid]
	
Trial end:

	end_trial
	stop_trial
	
Variables:

	var [name] [value]
	
Start of a period of continuous data:
	
	start_phase [name]
	phase [name]
	
End of a period of continuous data:

	end_phase [name]
	stop_phase [name]
	
	

## Function reference

[API]


## Tutorial

For a tutorial about using EyeLinkParser, see:

- <https://pydatamatrix.eu/eyelinkparser/>

## License

`python-eyelinkparser` is licensed under the [GNU General Public License
v3](http://www.gnu.org/licenses/gpl-3.0.en.html).
