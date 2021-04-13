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
from eyelinkparser._eyelinkparser import ANY_VALUE, ANY_VALUES


class SMIParser(EyeLinkParser):

    def __init__(self, **kwargs):

        if u'ext' not in kwargs:
            kwargs[u'ext'] = [u'.tar.xz', u'.txt']
        EyeLinkParser.__init__(self, **kwargs)

    def is_end_trial(self, l):

        # 12529411046	MSG	1	# Message: 066_baseline.jpg
        if self.match(l, int, u'MSG', int, ANY_VALUES):
            self.redo_line(u' '.join([str(e) for e in l]))
            return True
        return False

    def is_start_trial(self, l):

        # 12529411046	MSG	1	# Message: 066_baseline.jpg
        if self.match(l, int, u'MSG', int, ANY_VALUES):
            if self.trialid is None:
                self.trialid = 0
            else:
                self.trialid += 1
            self._message = u' '.join(l[5:])
            self.current_phase = None
            return True
        return False

    def end_phase(self, l):

        EyeLinkParser.end_phase(self, l)
        del self.trialdm.fixetlist_phase
        del self.trialdm.fixstlist_phase
        del self.trialdm.fixxlist_phase
        del self.trialdm.fixylist_phase

    def on_start_trial(self):

        self.trialdm.message = self._message
        self.start_phase([u'MSG', 0, u'start_phase', 'phase'])

    def is_message(self, line):

        # 12529411046	MSG	1	# Message: 066_baseline.jpg
        return u'MSG' in line

    def split(self, line):

        l = EyeLinkParser.split(self, line)
        # Convert samples to EyeLink format. The IDF encodes like this:
        # 00 Time
        # 01 Type
        # 02 Trial
        # 03 L Dia X [px]
        # 04 L Dia Y [px]
        # 05 L Mapped Diameter [mm]
        # 06 R Dia X [px]
        # 07 R Dia Y [px]
        # 08 R Mapped Diameter [mm]
        # 09 L POR X [px]
        # 10 L POR Y [px]
        # 11 R POR X [px]
        # 12 R POR Y [px]
        # 13 Timing
        # 14 Latency
        # 15 L Validity
        # 16 R Validity
        # 17 Pupil Confidence
        # 18 L Plane
        # 19 R Plane
        # 20 L EPOS X
        # 21 L EPOS Y
        # 22 L EPOS Z
        # 23 R EPOS X
        # 24 R EPOS Y
        # 25 R EPOS Z
        # 26 L GVEC X
        # 27 L GVEC Y
        # 28 L GVEC Z
        # 29 R GVEC X
        # 30 R GVEC Y
        # 31 R GVEC Z
        # 32 Aux1 (seems to be missing in actual data. Maybe an extra field?)
        if not l or len(l) < 32 or l[1] != u'SMP':
            # Not a sample!
            return l
        x = .5*l[20]+.5*l[23]
        y = .5*l[21]+.5*l[24]
        ps = .5*l[5]+.5*l[8]
        t = l[0]
        return [t, x, y, ps, u'...']

    def parse_sample(self, s):

        if s.pupil_size == '#':
            return
        EyeLinkParser.parse_sample(self, s)
