# Python EyeLinkParser

Sebastiaan Mathôt  <br />
Copyright 2016-2022  <br />
http://www.cogsci.nl/smathot

## About

The `python-eyelinkparser` module provides a framework to parse EyeLink data files in `.asc` format, that is, the format that you get after converting an `.edf` file with `edf2asc`. This module is mostly for personal use, and is not very well documented.

## Installation

```
pip install python-eyelinkparser
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

**<span style="color:purple">eyelinkparser.EyeLinkParser</span>_(folder='data', ext=('.asc', '.edf', '.tar.xz'), downsample=None, maxtracelen=None, traceprocessor=None, phasefilter=None, phasemap={}, trialphase=None, edf2asc_binary='edf2asc', multiprocess=False, asc_encoding=None, pupil_size=True, gaze_pos=True, time_trace=True)_**


The main parser class. This is generally not created directly, but
through the `eyelinkparser.parse()` function, which takes the same keywords
as the `EyeLinkParser` constructor (i.e. the keywords below).


#### Parameters
* folder: str, optional :  The folder that contains .edf or .asc data files, or files compressed
	as .tar.xz archives.
* ext: str or tuple, optional :  Allowed file extensions, or a tuple of extensions, for data files.
* downsample: int or None, optional :  Indicates whether traces (if any) should be downsampled. For example, a
	value of 10 means that the signal becomes 10 times shorter. Downsample
	creates a simple traceprocessor, and can therefore not be used in
	combination with the traceprocessor argument.
* maxtracelen: int or None, optional :  A maximum length for traces. Longer traces are truncated and a
	`UserWarning` is emitted. This length refers to the trace after
	downsampling/ processing.
* traceprocessor: callable or None, optional :  A function that is applied to each trace before the trace is written to
	the SeriesColumn. This can be used to apply a series of operations that
	are best done on the raw signal, such as first correcting blinks and
	then downsampling the signal.
	
	The function must accept two arguments: first a label for the trace,
	which is 'pupil', 'xcoor', 'ycoor', or 'time'. This allows the function
	to distinguish the different kinds of singals; second, the trace
	itself.
	
	See `eyelinkparser.defaulttraceprocessor` for a convenience function
	that applies blink correction and downsampling.
* trialphase: str or None, optional :  Indicates the name of a phase that should be automatically started when
	the trial starts, or `None` when no trial should be automatically
	started. This is mostly convenient for processing trials that consist
	of a single long epoch, or when no `start_phase` messages were written
	to the log file.
* phasefilter: callable or None, optional :  A function that receives a phase name as argument, and returns a bool
	indicating whether that phase should be retained.
* phasemap: dict, optional :  A dict in which keys are phase names that are renamed to the associated
	values. This is mostly useful to merge subsequent traces, in which
	case the key is the first trace and the value is the second trace.
* edf2asc_binary: str, optional :  The name of the edf2asc executable, which if available can be used to
	automatically convert .edf files to .asc. If not available, the parser
	can only parse .asc files.
* multiprocess: bool or int or None, optional :  Indicates whether each file should be processed in a different process.
	This can speed up parsing considerably. If not `False`, this should be
	an int to indicate the number of processes, or None to indicate that
	the number of processes should be the same as the number of cores.
* asc_encoding: str or None, optional :  Indicates the character encoding of the `.asc` files, or `None` to use
	system default.
* pupil_size: bool, optional :  Indicates whether pupil-size traces should be stored. If enabled, pupil
	size is stored as `ptrace_[phase]` columns.
* gaze_pos: bool, optional :  Indicates whether horizontal and vertical gaze-position traces should
	be stored. If enabled, gaze position is stored as `xtrace_[phase]` and
	`ytrace_[phase]` columns.
* time_trace: bool, optional :  Indicates whether timestamp traces should be stored, which indicate the
	timestamps of the corresponding pupil and gaze-position traces. If
	enabled, timestamps are stored as `ptrace_[phase]` columns.

#### Examples
```python
import eyelinkparser as ep
dm = ep.parse(defaulttraceprocessor=ep.defaulttraceprocessor(
    blinkreconstruct=True, downsample=True, mode='advanced'))
```


## Tutorial

For a tutorial about using EyeLinkParser, see:

- <https://datamatrix.cogsci.nl/eyelinkparser/>

## License

`python-eyelinkparser` is licensed under the [GNU General Public License
v3](http://www.gnu.org/licenses/gpl-3.0.en.html).
