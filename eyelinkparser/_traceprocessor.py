# -*- coding: utf-8 -*-

"""
This file is part of eyelinkparser.

eyelinkparser is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

eyelinkparser is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with datamatrix.  If not, see <http://www.gnu.org/licenses/>.
"""

from datamatrix.py3compat import *
import functools
from datamatrix import series as srs


def defaulttraceprocessor(blinkreconstruct=False, downsample=None):
	
	"""
	desc:
		Creates a function that is suitable as traceprocessor argument for
		eyelinkparser.__init__().
		
	arguments:
		blinkreconstruct:
			desc:	Indicates whether blink reconstruction should be applied to
					pupil size traces.
			type:	bool
		downsample:
			desc:	Indicates whether the signal should be downsampled, and if
					so, by how much.
			type:	[None, int]
		
	returns:
		desc:	A function suitable as traceprocessor argument.
		type:	callable
	"""
	
	def fnc(label, trace, blinkreconstruct, downsample):
		
		if blinkreconstruct:
			trace = srs._blinkreconstruct(trace)
		if downsample is not None:
			trace = srs._downsample(trace, downsample)
		return trace
	
	return functools.partial(fnc, blinkreconstruct=blinkreconstruct,
		downsample=downsample)
