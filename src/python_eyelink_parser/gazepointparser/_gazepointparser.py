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

from eyelinkparser import EyeLinkParser, parse, defaulttraceprocessor
from datamatrix import io


class GazePointParser(EyeLinkParser):

    def __init__(self, **kwargs):

        if u'ext' not in kwargs:
            kwargs[u'ext'] = [u'.tar.xz', u'.tsv']
        super().__init__(**kwargs)

    def split(self, line):

        l = super().split(line.lower())
        if not l:
            return l
        # Create a MSG
        if len(l) >= 42:
            return ['MSG', l[2]] + l[41:]
        # Create a sample
        return [l[2], l[15], l[16], (l[25] + l[20]) / 2, '...']
        
    def is_start_trial(self, l):
        
        current_trialid = self.trialid
        if super().is_start_trial(l):
            return current_trialid != self.trialid
        return False
        
    def is_message(self, line):

        return len(super().split(line)) >= 42
    
    def on_end_file(self):
        
        csv_path = self.path[:-3] + 'csv'
        csv_dm = io.readtxt(csv_path)
        if len(csv_dm) != len(self.filedm):
            raise Exception('non-matching csv-file for {}'.format(self.path))
        for name, column in csv_dm.columns:
            self.filedm[name] = column
