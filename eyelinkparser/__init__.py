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

from datamatrix import cached
from datamatrix.py3compat import *
from eyelinkparser._events import sample, fixation, saccade
from eyelinkparser._traceprocessor import defaulttraceprocessor
from eyelinkparser._eyelinkparser import EyeLinkParser

__version__ = u'0.6.1'

@cached
def parse(parser=EyeLinkParser, **kwdict):

	return parser(**kwdict).dm
