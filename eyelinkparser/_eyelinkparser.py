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
try:
	import fastnumbers
except ImportError:
	warnings.warn('Install fastnumbers for better performance')
	fastnumbers = None
import numpy as np
from datamatrix import DataMatrix, SeriesColumn, operations
from eyelinkparser import sample, fixation, defaulttraceprocessor

ANY_VALUE = int, float, basestring


class EyeLinkParser(object):

	def __init__(self, folder=u'data', ext=u'.asc', downsample=None,
		maxtracelen=None, traceprocessor=None, phasefilter=None):
		
		"""
		desc:
			Constructor.
			
		keywords:
			folder:
				type:	str
				desc:	The folder containing data files
			ext:
				type:	str
				desc:	The data-file extension
			downsample:
				type:	[int, None]
				desc: >
						Indicates whether traces (if any) should be downsampled.
						For example, a value of 10 means that the signal becomes
						10 times shorter.
						
						Downsample creates a simple traceprocessor, and can
						therefore not be used in combination with the
						traceprocessor argument.
			maxtracelen:
				type:	[int, None]
				desc:	A maximum length for traces. Longer traces are truncated
						and a UserWarning is emitted. This length refers to the
						trace after processing.
			traceprocessor:
				type:	[callable, None]
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
			phasefilter:
				type:	[callable,None]
				desc: >
						A function that receives a phase name as argument, and
						returns a bool indicating whether that phase should be
						retained.						
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
		for fname in sorted(os.listdir(folder)):
			if not fname.endswith(ext):
				continue
			path = os.path.join(folder, fname)
			self.dm <<= self.parse_file(path)
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
		
		if len(l) != len(ref):
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

	def parse_file(self, path):

		self.filedm = DataMatrix()
		self.trialid = None
		self.print_(u'Parsing %s ' % path)		
		self.path = path
		self.on_start_file()
		ntrial = 0
		with open(path) as f:
			for line in f:
				# Only messages can be start-trial messages, so performance we
				# don't do anything with non-MSG lines.
				if not line.startswith('MSG'):
					continue
				l = self.split(line)
				if self.is_start_trial(l):
					ntrial += 1
					self.print_(u'.')
					self.filedm <<= self.parse_trial(f)
		self.on_end_file()
		self.print_(u' (%d trials)\n' % ntrial)
		# Force garbage collection. Without it, memory seems to fill
		# up more quickly than necessary.
		gc.collect()		
		return self.filedm

	def parse_trial(self, f):

		self.trialdm = DataMatrix(length=1)
		self.trialdm.path = self.path
		self.trialdm.trialid = self.trialid
		self.on_start_trial()
		for line in f:
			l = self.split(line)
			if not l:
				warnings.warn(u'Empty line')
				continue
			# Only messages can be variables or end-trial messages, so to
			# improve performance don't even check.
			if l[0] == 'MSG':
				if self.is_end_trial(l):
					break
				self.parse_variable(l)
			self.parse_phase(l)			
			self.parse_line(l)
		if self.current_phase is not None:
			warnings.warn(
				u'Trial ended while phase "%s" was still ongoing' \
				% self.current_phase)
			self.end_phase()
		self.on_end_trial()
		return self.trialdm
		
	def parse_variable(self, l):

		# MSG	6740629 var rt 805
		if not self.match(l, u'MSG', int, u'var', basestring, ANY_VALUE):
			return
		var = l[3]
		val = l[4]
		if var in self.trialdm:
			warnings.warn(u'Variable "%s" defined twice in one trial' % var)
		self.trialdm[var] = val

	def start_phase(self, l):

		if self.current_phase is not None:
			warnings.warn(
				u'Phase "%s" started while phase "%s" was still ongoing' \
				% (l[3], self.current_phase))
			self.end_phase()
		if self._phasefilter is not None and not self._phasefilter(l[3]):
			return
		self.current_phase = l[3]
		if u'ptrace_%s' % self.current_phase in self.trialdm:
			raise Exception('Phase %s occurs twice' % self.current_phase)
		self.ptrace = []
		self.xtrace = []
		self.ytrace = []
		self.ttrace = []
		self.fixxlist = []
		self.fixylist = []
		self.fixstlist = []
		self.fixetlist = []

	def end_phase(self):

		for i, (tracelabel, prefix, trace) in enumerate([
				(u'pupil', u'ptrace_', self.ptrace),
				(u'xcoor', u'xtrace_', self.xtrace),
				(u'ycoor', u'ytrace_', self.ytrace),
				(u'time', u'ttrace_', self.ttrace),
				(None, u'fixxlist_', self.fixxlist),
				(None, u'fixylist_', self.fixylist),
				(None, u'fixstlist_', self.fixstlist),
				(None, u'fixetlist_', self.fixetlist),
				]):
			trace = np.array(trace)
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
			if len(trace) and prefix == u'ttrace_':
				self.trialdm[colname][0] -= self.trialdm[colname][0][0]
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
				self.end_phase()
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
