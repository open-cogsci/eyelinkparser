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

import math
import sys
import shlex
import os
from datamatrix import DataMatrix, SeriesColumn, operations
from datamatrix.py3compat import *
from eyelinkparser import sample
import numpy as np
import numbers
import warnings

ANY_VALUE = int, float, basestring


class EyeLinkParser(object):

	def __init__(self, folder=u'data', ext=u'.asc', downsample=None,
		maxtracelen=None):
		
		"""
		desc:
			Constructor.
			
		keywords:
			data:
				type:	str
				desc:	The folder containing data files
			ext:
				type:	str
				desc:	The data-file extension
			downsample:
				type:	[int, None]
				desc:	Indicates whether traces (if any) should be downsampled.
						For example, a value of 10 means a sample is retained
						at most once every 10 ms (but less if the sampling
						rate). is less to begin with.
			maxtracelen:
				type:	[int, None]
				desc:	A maximum length for traces. Longer traces are truncated
						and a UserWarning is emitted.
		"""

		self.dm = DataMatrix()
		self._downsample = downsample
		self._lastsampletime = None
		self._maxtracelen = maxtracelen
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
		self.print_(u'Parsing %s ' % path)
		self.path = path
		self.on_start_file()
		ntrial = 0
		with open(path) as f:
			for line in f:
				l = self.split(line)
				if self.is_start_trial(l):
					ntrial += 1
					self.print_(u'.')
					self.filedm <<= self.parse_trial(f)
		self.on_end_file()
		self.print_(u' (%d trials)\n' % ntrial)
		return self.filedm

	def parse_trial(self, f):

		self.trialdm = DataMatrix(length=1)
		self.trialdm.path = self.path
		self.trialdm.trialid = self.trialid
		self.on_start_trial()
		for line in f:
			l = self.split(line)
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
		self.current_phase = l[3]
		if self.current_phase in self.trialdm:
			raise Exception('Phase %s occurs twice' % self.current_phase)
		self.ptrace = []
		self.xtrace = []
		self.ytrace = []
		self.ttrace = []

	def end_phase(self):

		for prefix, trace in [
			(u'ptrace_', self.ptrace),
			(u'xtrace_', self.xtrace),
			(u'ytrace_', self.ytrace),
			(u'ttrace_', self.ttrace)
			]:
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
				if trace and prefix == u'ttrace_':
					self.trialdm[colname][0] -= self.trialdm[colname][0][0]
		self.current_phase = None

	def parse_phase(self, l):

		if self.match(l, u'MSG', int, (u'start_phase', u'phase'), basestring):
			self.start_phase(l)
			return
		if self.match(l, u'MSG', int, (u'end_phase', u'stop_phase'), basestring):
			assert(self.current_phase == l[3])
			self.end_phase()
			return
		if self.current_phase is None:
			return
		s = sample(l)
		if s is None:
			return
		if self._downsample is not None and self._lastsampletime is not None \
			and s.t	- self._lastsampletime < self._downsample:
				return
		self._lastsampletime = s.t
		self.ttrace.append(s.t)
		self.ptrace.append(s.pupil_size)
		self.xtrace.append(s.x)
		self.ytrace.append(s.y)

	def is_start_trial(self, l):

		# MSG	6735155 start_trial 1
		if self.match(l, u'MSG', int, u'start_trial', ANY_VALUE):
			self.trialid = l[3]
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

		l = []
		for s in shlex.split(line):
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
