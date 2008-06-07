"""A simple python dictionary serialiser
 -- this code is probably redundant since this functionality is built into python--

Copyright Chetan Padia ( chetbox [at] gmail [dot] com )
Released under GPLv2 (See COPYING.txt)
"""

# This file is part of EasyEdit.
#
# EasyEdit is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# EasyEdit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import string

null = chr(0) # ASCII null character

class Parser:

	def __init__(self, path):
		self.comment = '#'
		self.unifier = '='
		self.separator = ','
		self.path = path
		self.contents = {}

	def _nextchar(self):
	    	self.last = self.file.read(1)
		if self.last == '':
			self.last = null

	def _ignorewhitespace(self, ignorenewline=True):
		while (self.last in string.whitespace) and (self.last != null) and (ignorenewline or self.last != '\n'):
			self._nextchar()

	def parse(self):

		self.file = open(self.path, 'r')
		self._nextchar()

		while self.last != null:

			name = ''
			data = ''

			self._ignorewhitespace()

			## ignore comments
			if (self.last in self.comment) and (self.last != null):
				while self.last != '\n':
				    self._nextchar()

			## parse data
			if (self.last in string.ascii_letters) and (self.last != null):
				while not(
				    (self.last in string.whitespace) or
				    (self.last in self.unifier) or
				    (self.last in self.comment) or
				    (self.last == null)
				):
					name += self.last
					self._nextchar()

				self._ignorewhitespace()

				if self.last in self.unifier:
					self._nextchar()

					self._ignorewhitespace(ignorenewline=False)

					while not(
					    (self.last == '\n') or
					    (self.last in self.comment) or
					    (self.last == null)
					):
						data += self.last
						self._nextchar()

					## convert to list
					data = string.split(data, self.separator)

					## convert numbers from ASCII if necessary
					datalist = []
					for element in data:
						element = string.strip(element)
						try:
							element = string.atoi(element)
						except:
							try:
								element = string.atof(element)
							except:
								pass
						if element != '':
							datalist.append(element)


			if len(name) > 0:
				self.contents[name] = datalist

		self.file.close()

		return self.contents


	def create(self, contents=None, comment=None):
		string = ''
		if comment != None:
			string += self.comment + ' ' + str(comment) + '\n\n'
		if contents == None:
			contents = self.contents
		for record in contents:
			string += str(record) + ' ' + self.unifier
			elements = False
			for element in contents[record]:
				string += ' ' + str(element) + self.separator
				elements = True
			if elements:
				string = string[:-1]
			string += '\n'

		return string

	def write(self, contents=None, comment=None, path=None):
		if path == None:
			path = self.path
		f = open(path, 'w')
		f.write(self.create(contents, comment))
		f.close
