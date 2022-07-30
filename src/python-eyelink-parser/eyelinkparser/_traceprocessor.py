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


def _fnc(label, trace, blinkreconstruct, downsample, mode):

    if label == 'pupil' and blinkreconstruct:
        try:
            trace = srs._blinkreconstruct(trace, mode=mode)
        except TypeError:
            warn('blinkreconstruct does not support mode keyword. '
                 'Please update datamatrix.')
    if downsample is not None:
        trace = srs._downsample(trace, downsample)
    return trace


def defaulttraceprocessor(blinkreconstruct=False,
                          downsample=None, mode='original'):
    """
    desc:
        Creates a function that is suitable as traceprocessor argument for
        eyelinkparser.__init__().

    arguments:
        blinkreconstruct:
            desc:   Indicates whether blink reconstruction should be applied to
                    pupil size traces.
            type:   bool
        downsample:
            desc:   Indicates whether the signal should be downsampled, and if
                    so, by how much.
            type:   [None, int]
        mode:
            desc:   Indicates whether blink-reconstruction should be done with
                    'original' or 'advanced' mode. Advanced mode is recommended
                    but original mode is the default for purposes of backwards
                    compatibility.
            type:   [str]

    returns:
        desc:   A function suitable as traceprocessor argument.
        type:   callable
    """

    return functools.partial(
        _fnc,
        blinkreconstruct=blinkreconstruct,
        downsample=downsample,
        mode=mode
    )
