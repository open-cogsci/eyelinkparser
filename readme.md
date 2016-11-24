# Python EyeLinkParser

Sebastiaan Mathôt  <br />
Copyright 2016  <br />
http://www.cogsci.nl/smathot

## About

The `python-eyelinkparser` module provides a framework to parse EyeLink data files in `.asc` format, that is, the format that you get after converting an `.edf` file with `edf2asc`. This module is mostly for personal use, and is not very well documented.

## Expected messages

By default, the parser assumes that particular messages are sent to the logfile. If you use different messages, you need to override functions in
`_eyelinkparser.EyeLinkParser`. This is not explained here, but you can look n the source code to see how it works.

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
	
	
## Example

For an example analysis, see:

- [using-eyelinkparser.ipynb](using-eyelinkparser.ipynb)

## Dependencies

Requires `python-datamatrix`:

- <https://github.com/smathot/python-datamatrix>

## License

`python-eyelinkparser` is licensed under the [GNU General Public License
v3](http://www.gnu.org/licenses/gpl-3.0.en.html).
