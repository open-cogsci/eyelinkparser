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

import warnings
import numbers
import numpy as np
try:
    import fastnumbers
except ImportError:
    warnings.warn('Install fastnumbers for better performance')
    fastnumbers = None


class Event(object):

    def assert_numeric(self, l, indices):

        if fastnumbers is not None:
            for i in indices:
                if not fastnumbers.isreal(l[i]):
                    raise TypeError()
            return
        for i in indices:
            if not isinstance(l[i], (int, float)) or l[i] <= 0:
                raise TypeError()


class Blink(Event):
    
    """
    desc:
        Format:
        EBLINK R 5294685	5294774	90
    """
    
    def __init__(self, l):
        self.assert_numeric(l, range(2, 5))
        self.st = l[2]
        self.et = l[3]
        self.duration = l[4]
            
    @staticmethod
    def match(l):
        return len(l) == 5 and l[0] == 'EBLINK'


class Fixation(Event):

    """
    desc:
        Format (short):
        EFIX R   1651574	1654007	2434	  653.3	  557.8	   4710
        EFIX R   299705		299872	168	  	509.0	  341.1	   2024
        Format (long):
        TODO
    """

    def __init__(self, l):
        self.assert_numeric(l, range(2,8))
        self.x = l[5]
        self.y = l[6]
        self.pupil_size = l[7]
        self.st = l[2]
        self.et = l[3]
        self.duration = self.et - self.st
        
    @staticmethod
    def match(l):
        return len(l) == 8 and l[0] == "EFIX"


class Sample(Event):

    """
    desc:
        # Normal: [Timestamp] [x] [y] [pupil size] ...
        4815155   168.2   406.5  2141.0 ...
        # During blinks:
        661781	   .	   .	    0.0	...
        # Elaborate format:
        548367    514.0   354.5  1340.0 ...      -619.0  -161.0    88.9 ...CFT..R.BLR
        # Another format:
        4333109	  981.4	  525.8	 1361.0	32768.0	...
    """

    def __init__(self, l):

        self.assert_numeric(l, [0])
        self.t = l[0]
        if l[1] == '.':
            self.x = np.nan
        else:
            self.x = l[1]
        if l[2] == '.':
            self.y = np.nan
        else:
            self.y = l[2]
        if l[3] in (0, '.'):
            self.pupil_size = np.nan
        else:
            self.pupil_size = l[3]
            
    @staticmethod
    def match(l):
        return len(l) in (5, 6, 8, 9) and not isinstance(l[0], str)


class Saccade(Event):

    """
    desc:
        Format:
        ESACC R  3216221	3216233	13	  515.2	  381.6	  531.2	  390.7	   0.51	     58
        Format (long)
        TODO
    """

    def __init__(self, l):

        if len(l) == 11:
            self.assert_numeric(l, [2,3,5,6,7,8])
            self.sx = l[5]
            self.sy = l[6]
            self.ex = l[7]
            self.ey = l[8]
        else:
            self.assert_numeric(l, [2,3,9,10,11,12])
            self.sx = l[9]
            self.sy = l[10]
            self.ex = l[11]
            self.ey = l[12]
        self.size = np.sqrt((self.sx-self.ex)**2 + (self.sy-self.ey)**2)
        self.st = l[2]
        self.et = l[3]
        self.duration = self.et - self.st
        
    @staticmethod
    def match(l):
        return len(l) in (11, 15) and l[0] == 'ESACC'


def event(l, cls):

    if not cls.match(l):
        return None
    try:
        return cls(l)
    except TypeError:
        pass
    except Exception as e:
        warnings.warn(f'Unexpected exception during parsing of {e}')


def sample(l):
    return event(l, Sample)
def fixation(l):
    return event(l, Fixation)
def saccade(l):
    return event(l, Saccade)
def blink(l):
    return event(l, Blink)
