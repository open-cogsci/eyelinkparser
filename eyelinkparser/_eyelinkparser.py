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
import gc
import math
import sys
import os
import warnings
import tempfile
import subprocess
import itertools
import logging
try:
    import fastnumbers
except ImportError:
    warnings.warn('Install fastnumbers for better performance')
    fastnumbers = None
import numpy as np
from datamatrix import DataMatrix, SeriesColumn, operations
from eyelinkparser import sample, fixation, blink, defaulttraceprocessor

ANY_VALUE = int, float, basestring
ANY_VALUES = list, int, float, basestring


class EyeLinkParser(object):

    def __init__(
        self,
        folder=u'data',
        ext=(u'.asc', u'.edf', u'.tar.xz'),
        downsample=None,
        maxtracelen=None,
        traceprocessor=None,
        phasefilter=None,
        trialphase=None,
        edf2asc_binary=u'edf2asc',
        multiprocess=False,
        asc_encoding=None,
        pupil_size=True,
        gaze_pos=True,
        time_trace=True
    ):

        """
        desc:
            Constructor.

        keywords:
            folder:
                type:   str
                desc:   The folder containing data files
            ext:
                type:   str, tuple
                desc:   The data-file extension, or tuple of extensions.
            downsample:
                type:   [int, None]
                desc: >
                        Indicates whether traces (if any) should be downsampled.
                        For example, a value of 10 means that the signal becomes
                        10 times shorter.

                        Downsample creates a simple traceprocessor, and can
                        therefore not be used in combination with the
                        traceprocessor argument.
            maxtracelen:
                type:   [int, None]
                desc:   A maximum length for traces. Longer traces are truncated
                        and a UserWarning is emitted. This length refers to the
                        trace after processing.
            traceprocessor:
                type:   [callable, None]
                desc: >
                        A function that is applied to each trace before the
                        trace is written to the SeriesColumn. This can be used
                        to apply a series of operations that are best done on
                        the raw signal, such as first correcting blinks and then
                        downsampling the signal.

                        The function must accept two arguments: first a label
                        for the trace, which is 'pupil', 'xcoor', 'ycoor', or
                        'time'. This allows the function to distinguish the
                        different kinds of singals; second, the trace itself.

                        See `eyelinkparser.defaulttraceprocessor` for a
                        convenience function that applies blink correction and
                        downsampling.
            trialphase:
                type:   [str, None]
                desc: >
                        Indicates the name of a phase that should be
                        automatically started when the trial starts, or `None`
                        when no trial should be automatically started. This is
                        mostly convenient for processing trials that consist
                        of a single long epoch, or when no `start_phase`
                        messages are written to the log file.
            phasefilter:
                type:   [callable,None]
                desc: >
                        A function that receives a phase name as argument, and
                        returns a bool indicating whether that phase should be
                        retained.
            edf2asc_binary:
                type:   str
                desc: >
                        The name of the edf2asc executable, which if available
                        can be used to automatically convert edf files to asc.
            multiprocess:
                type:   [bool, int, None]
                desc: >
                        Indicates whether each file should be processed in a
                        different process. This can speed up parsing
                        considerably. If it's not False, it should be an int to
                        indicate the number of processes, or None to indicate
                        that the number of processes should be the same as the
                        number of cores.
            asc_encoding:
                type:   [str, None]
                desc: >
                        Indicates the character encoding of the `.asc` files,
                        or `None` to use system default.
            pupil_size:
                type:   [bool]
                desc: >
                        Indicates whether pupil-size traces should be stored.
                        If enabled, pupil size is stored as `ptrace_[phase]`
                        columns.
            gaze_pos:
                type:   [bool]
                desc: >
                        Indicates whether horizontal and vertical gaze-position
                        traces should be stored. If enabled, gaze position is
                        stored as `xtrace_[phase]` and `ytrace_[phase]`
                        columns.
            time_trace:
                type:   [bool]
                desc: >
                        Indicates whether timestamp traces should be stored,
                        which indicate the timestamps of the corresponding
                        pupil and gaze-position traces. If enabled, timestamps
                        are stored as `ptrace_[phase]`
                        columns.
        """

        self.dm = DataMatrix()
        if downsample is not None:
            if traceprocessor is not None:
                raise ValueError(
                    'You can specify a downsampling rate or traceprocessor, but not both')
            traceprocessor = defaulttraceprocessor(downsample=downsample)
        self._maxtracelen = maxtracelen
        self._traceprocessor = traceprocessor
        self._phasefilter = phasefilter
        self._edf2asc_binary = edf2asc_binary
        self._trialphase = trialphase
        self._asc_encoding = asc_encoding
        self._temp_files = []
        self._pupil_size = pupil_size
        self._gaze_pos = gaze_pos
        self._time_trace = time_trace
        # Get a list of input files. First, only files in the data folder that
        # match any of the extensions. Then, these files are passed to the
        # converter which may return multiple files, for example if they have
        # been compressed. The result is a list of iterators, which is chained
        # into a single iterator.
        input_files = itertools.chain(*(
            self.convert_file(os.path.join(folder, fname))
            for fname in sorted(os.listdir(folder))
            if (
                fname.lower().endswith(ext.lower())
                if isinstance(ext, basestring)
                else any(fname.lower().endswith(e.lower()) for e in ext)
            )
        ))
        if multiprocess:
            import multiprocessing as mp
            with mp.Pool(multiprocess) as p:
                filedms = p.map(self.parse_file, input_files)
            while filedms:
                self.dm <<= filedms.pop()
        else:
            for fname in input_files:
                self.dm <<= self.parse_file(fname)
        operations.auto_type(self.dm)

    # Helper functions that can be overridden

    def on_start_file(self):

        pass

    def on_end_file(self):

        pass

    def on_start_trial(self):

        pass

    def on_end_trial(self):

        pass

    def parse_line(self, l):

        pass

    # Internal functions

    def match(self, l, *ref):

        if len(l) != len(ref) and (ref[-1] != ANY_VALUES or len(ref) > len(l)):
            return False
        for i1, i2 in zip(l, ref):
            # Literal match
            if i1 == i2:
                continue
            # Set match
            if isinstance(i2, tuple) and i1 in i2:
                continue
            # Direct instance match
            if isinstance(i2, type) and isinstance(i1, i2):
                continue
            # Set instance match
            if isinstance(i2, tuple) \
                and [t for t in i2 if isinstance(t, type)] \
                and isinstance(i1, i2):
                    continue
            return False
        return True

    def print_(self, s):

        sys.stdout.write(s)
        sys.stdout.flush()

    def stacked_file(self, f):

        for line in f:
            yield line
            while self._linestack:
                yield self._linestack.pop()

    def redo_line(self, line):

        self._linestack.append(line)

    def parse_file(self, path):

        logging.info(u'parsing {}'.format(path))
        path = self.edf2asc(path)
        self.filedm = DataMatrix()
        self.trialid = None
        self.path = path
        self.on_start_file()
        ntrial = 0
        self._linestack = []
        with open(path, encoding=self._asc_encoding) as f:
            for line in self.stacked_file(f):
                # Only messages can be start-trial messages, so performance we
                # don't do anything with non-MSG lines.
                if not self.is_message(line):
                    continue
                if self.is_start_trial(self.split(line)):
                    ntrial += 1
                    self.print_(u'.')
                    self.filedm <<= self.parse_trial(f)
        self.on_end_file()
        logging.info(u' ({} trials)\n'.format(ntrial))
        # Force garbage collection. Without it, memory seems to fill
        # up more quickly than necessary.
        gc.collect()
        self._delete_temp_file(path)
        return self.filedm
    
    def parse_error(self, l):
        
        if len(l) > 2 and l[2] == 'ERROR':
            warnings.warn('data error: {} (timestamp: {})'.format(
                ' '.join([str(e) for e in l[2:]]),
                l[1],
            ))
            return True
        return False

    def parse_trial(self, f):

        self.trialdm = DataMatrix(length=1)
        self.trialdm.path = self.path
        self.trialdm.trialid = self.trialid
        self.trialdm.data_error = 0
        if self._trialphase is not None:
            self.parse_phase(['MSG', 0, 'start_phase', self._trialphase])
        self.on_start_trial()
        for line in self.stacked_file(f):
            l = self.split(line)
            if not l:
                warnings.warn(u'Empty line')
                continue
            if self.parse_error(l):
                self.trialdm.data_error = 1
                warnings.warn('ending trial due to data error')
                break
            # Only messages can be variables or end-trial messages, so to
            # improve performance don't even check.
            if self.is_message(line):
                if self.is_end_trial(l):
                    break
                self.parse_variable(l)
            self.parse_phase(l)
            self.parse_line(l)
        if self.current_phase is not None:
            warnings.warn(
                u'Trial ended while phase "%s" was still ongoing' \
                % self.current_phase)
            self.end_phase(l)
        self.on_end_trial()
        return self.trialdm

    def parse_variable(self, l):

        # MSG	6740629 var rt 805
        if not self.match(l, u'MSG', int, u'var', basestring, ANY_VALUES):
            return
        var = l[3]
        val = u' '.join([safe_decode(i) for i in l[4:]])
        if var in self.trialdm:
            warnings.warn(u'Variable "%s" defined twice in one trial' % var)
        self.trialdm[var] = val

    def start_phase(self, l):

        if self.current_phase is not None:
            warnings.warn(
                u'Phase "%s" started while phase "%s" was still ongoing' \
                % (l[3], self.current_phase))
            self.end_phase(l)
        if self._phasefilter is not None and not self._phasefilter(l[3]):
            return
        self.current_phase = l[3]
        if u'ptrace_%s' % self.current_phase in self.trialdm:
            raise Exception('Phase {} occurs twice (timestamp:{})'.format(
                self.current_phase,
                l[1]
            ))
        self.ptrace = []
        self.xtrace = []
        self.ytrace = []
        self.ttrace = []
        self.fixxlist = []
        self.fixylist = []
        self.fixstlist = []
        self.fixetlist = []
        self.blinkstlist = []
        self.blinketlist = []
        self._t_onset = self.trialdm['t_onset_%s' % self.current_phase] = l[1]

    def end_phase(self, l):

        self.trialdm['t_offset_%s' % self.current_phase] = l[1]
        for i, (tracelabel, prefix, trace) in enumerate([
            (u'pupil', u'ptrace_', self.ptrace),
            (u'xcoor', u'xtrace_', self.xtrace),
            (u'ycoor', u'ytrace_', self.ytrace),
            (u'time', u'ttrace_', self.ttrace),
            (None, u'fixxlist_', self.fixxlist),
            (None, u'fixylist_', self.fixylist),
            (None, u'fixstlist_', self.fixstlist),
            (None, u'fixetlist_', self.fixetlist),
            (None, u'blinkstlist_', self.blinkstlist),
            (None, u'blinketlist_', self.blinketlist),
        ]):
            if tracelabel == 'pupil' and not self._pupil_size:
                continue
            if tracelabel in ('xcoor', 'ycoor') and not self._gaze_pos:
                continue
            if tracelabel == 'time' and not self._time_trace:
                continue
            trace = np.array(trace, dtype=float)
            if tracelabel is not None and self._traceprocessor is not None:
                trace = self._traceprocessor(tracelabel, trace)
            if self._maxtracelen is not None \
                and len(trace) > self._maxtracelen:
                    warnings.warn(u'Trace %s is too long (%d samples)' \
                        % (self.current_phase, len(trace)))
                    trace = trace[:self._maxtracelen]
            colname = prefix + self.current_phase
            self.trialdm[colname] = SeriesColumn(
                len(trace), defaultnan=True)
            self.trialdm[colname][0] = trace
            # Start the time trace at 0
            if len(trace) and prefix in ('ttrace_', 'fixstlist_',
                                         'fixetlist_', 'blinkstlist',
                                         'blinketlist'):
                self.trialdm[colname][0] -= self._t_onset
        # DEBUG CODE
        # 	from matplotlib import pyplot as plt
        # 	plt.subplot(4,2,i+1)
        # 	plt.title(colname)
        # 	plt.plot(_trace, color='blue')
        # 	xdata = np.linspace(0, len(_trace)-1, len(trace))
        # 	plt.plot(xdata, trace, color='red')
        # plt.show()
        self.current_phase = None

    def parse_sample(self, s):

        self.ttrace.append(s.t)
        self.ptrace.append(s.pupil_size)
        self.xtrace.append(s.x)
        self.ytrace.append(s.y)

    def parse_fixation(self, f):

        self.fixxlist.append(f.x)
        self.fixylist.append(f.y)
        self.fixstlist.append(f.st)
        self.fixetlist.append(f.et)
        
    def parse_blink(self, b):
        
        self.blinkstlist.append(b.st)
        self.blinketlist.append(b.et)

    def parse_phase(self, l):

        # For performance only check for start- and end-phase messages if there
        # actually is a message
        if l[0] == 'MSG':
            if self.match(l, u'MSG', int, (u'start_phase', u'phase'), basestring):
                self.start_phase(l)
                return
            if self.match(l, u'MSG', int, (u'end_phase', u'stop_phase'), basestring):
                if self.current_phase != l[3]:
                    warnings.warn(u'Trace %s was ended while current phase was %s' \
                        % (l[3], self.current_phase))
                    return
                self.end_phase(l)
                return
        if self.current_phase is None:
            return
        s = sample(l)
        if s is not None:
            self.parse_sample(s)
            return
        f = fixation(l)
        if f is not None:
            self.parse_fixation(f)
        b = blink(l)
        if b is not None:
            self.parse_blink(b)

    def is_start_trial(self, l):

        # MSG	6735155 start_trial 1
        if self.match(l, u'MSG', int, u'start_trial', ANY_VALUE):
            self.trialid = l[3]
            self.current_phase = None
            return True
        # MSG	6735155 start_trial
        if self.match(l, u'MSG', int, u'start_trial'):
            if self.trialid is None:
                self.trialid = 0
            else:
                self.trialid += 1
            self.current_phase = None
            return True
        return False

    def is_end_trial(self, l):

        # MSG	6740629 end_trial
        if self.match(l, u'MSG', int, (u'end_trial', u'stop_trial')):
            self.trialid = None
            return True
        return False

    def is_message(self, line):

        return line.startswith(u'MSG')

    def split(self, line):

        if fastnumbers is not None:
            return [fastnumbers.fast_real(s, nan=u'nan', inf=u'inf') \
                for s in line.split()]
        l = []
        for s in line.split():
            try:
                l.append(int(s))
            except:
                try:
                    # Make sure we don't convert 'inf' and 'nan' strings to
                    # float
                    assert(not math.isinf(float(s)))
                    assert(not math.isnan(float(s)))
                    l.append(float(s))
                except:
                    l.append(s)
        return l

    def _temp_path(self, path):

        new_path = os.path.join(
            tempfile.gettempdir(),
            tempfile.gettempprefix() + os.path.basename(path)
        )
        return new_path

    def convert_file(self, path):

        if not path.lower().endswith(u'.tar.xz'):
            yield path
        else:
            # Compressed files are extracted and the contents are then converted
            # again
            from tarfile import TarFile
            tf = TarFile.open(path)
            for ti in tf:
                tmp_folder = self._temp_path(ti.name)
                new_path = os.path.join(tmp_folder, ti.name)
                self._register_temp_file(new_path)
                logging.info('Extracting {} ...'.format(ti.name))
                tf.extract(ti.name, tmp_folder)
                for newer_path in self.convert_file(new_path):
                    yield newer_path
            tf.close()

    def _delete_temp_file(self, path):

        if path not in self._temp_files:
            return
        os.remove(path)
        logging.info('deleting temporary file {}'.format(path))
        self._temp_files.remove(path)

    def _register_temp_file(self, path):

        logging.info('creating temporary file {}'.format(path))
        self._temp_files.append(path)

    def edf2asc(self, path):

        if not path.lower().endswith(u'.edf'):
            return path
        new_path = self._temp_path(path) + u'.asc'
        subprocess.call([self._edf2asc_binary, u'-y', path, new_path])
        self._register_temp_file(new_path)
        self._delete_temp_file(path)
        print(new_path)
        return new_path
