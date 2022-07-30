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

import numpy as np
from eyelinkparser import EyeLinkParser


def chain(*functions):

    return lambda: [function() for function in functions]


class EyeTribeParser(EyeLinkParser):

    def __init__(self, **kwargs):

        if u'ext' not in kwargs:
            kwargs[u'ext'] = [u'.tar.xz', u'.tsv']
        self.on_start_trial = chain(self.init_infix, self.on_start_trial)
        EyeLinkParser.__init__(self, **kwargs)

    def init_infix(self):

        self.infix = False

    def split(self, line):

        l = EyeLinkParser.split(self, line)
        if not l:
            return l
        # Convert messages to EyeLink format
        if l[0] == u'MSG':
            l = l[3:]
            l.insert(0, u'MSG')
            return l
        # Convert samples to EyeLink format:
        if len(l) == 24:
            x, y, ps = l[7:10]
            t = l[2]
            fix = l[3] == 'True'
            if fix:
                if not self.infix:
                    self.xlist = []
                    self.ylist = []
                    self.tlist = []
                    self.pslist = []
                self.xlist.append(x)
                self.ylist.append(y)
                self.tlist.append(t)
                self.pslist.append(ps)
            elif self.infix:
                mx = np.nanmean(self.xlist)
                my = np.nanmean(self.ylist)
                mps = np.nanmean(self.pslist)
                st = self.tlist[0]
                et = self.tlist[-1]
                self.parse_phase(['EFIX', 'R', st, et, et-st, mx, my, mps])
            self.infix = fix
            l = [l[2], x, y, ps, u'...']
            return l
        return l
