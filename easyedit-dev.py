"""A simple text editor for s60

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


# Settings
VERSION=(2, 0, 2)
DEBUG = False
CONFFILE='C:\\SYSTEM\\Data\\EasyEdit.conf.dev'

# configuration file keys
CONF_VERSION			= 'version'
CONF_SCREEN				= 'screen size'
CONF_ORIENTATION		= 'screen orentation'
CONF_FONT				= 'font'
CONF_FONT_SIZE			= 'font size'
CONF_FONT_COLOUR		= 'font colour'
CONF_ENCODING			= 'encoding'
CONF_HISTORY			= 'history'
CONF_HISTORY_SIZE		= 'history size'
CONF_LAST_DIR			= 'last dir'
CONF_NEW_LINES			= 'new lines'
CONF_LINE_NUMBERS		= 'line numbers'
CONF_CASE_SENSITIVE		= 'case-sensitive search'


from appuifw import *
from key_codes import EKeySelect, EKeyLeftArrow, EKeyRightArrow, EKeyBackspace, EKey1, EKey2, EKeyEdit, EKeyYes
from e32 import Ao_lock, ao_yield, ao_sleep, s60_version_info
from os.path import exists
from sys import getdefaultencoding
from encodings import aliases

class Settings:
	"""Settings manager"""
	
	def __init__(self, path):
		self.config = {}
		self.path = path
		self.exit = Ao_lock()
		# create a new configuration if one does not exist
		existing_conf = exists(self.path)
		if existing_conf:
			# read the config file from disk
			f = open(self.path, 'r')
			conf_string = f.read()
			f.close()
			self.config = eval(conf_string)
			# check if a new version has been installed
			existing_conf = (self[CONF_VERSION] == VERSION)
		if not(existing_conf):
			if DEBUG:
				print("Creating new config...")
			textbox_font = Text().font	# not very nice, but it does what is required
			self.config = {\
				CONF_VERSION: VERSION,
				CONF_SCREEN: app.screen,
				CONF_ORIENTATION: 'automatic',
				CONF_FONT: textbox_font[0],
				CONF_FONT_SIZE: textbox_font[1],
				CONF_FONT_COLOUR: (0,0,0),
				CONF_ENCODING: getdefaultencoding(),
				CONF_HISTORY: [],
				CONF_HISTORY_SIZE: 8,
				CONF_LAST_DIR: '\\',
				CONF_NEW_LINES: 'unix',
				CONF_LINE_NUMBERS: 'yes',
				CONF_CASE_SENSITIVE: 'no'
			}
			self.save()

	def __getitem__(self, index):
		return self.config.__getitem__(index)

	def __setitem__(self, index, value):
		return self.config.__setitem__(index, value)

	def save(self):
		"""Save current config to disk"""
		if DEBUG:
			print("Saving settings to " + self.path)
		f = open(self.path, 'w')
		f.write(repr(self.config))
		f.close()

	def update(self):
		"""Update the Settings panel with the current settings"""
		if self.settings_list:
			slist = [
					(u'File encoding', unicode(self[CONF_ENCODING])),
					(u'New-lines', unicode(self[CONF_NEW_LINES])),
					(u'Case-sensitive find', unicode(self[CONF_CASE_SENSITIVE])),
					(u'Font', unicode(self[CONF_FONT])),
					(u'Font size', unicode(self[CONF_FONT_SIZE])),
					(u'Display line number', unicode(self[CONF_LINE_NUMBERS])),
					(u'Max history size', unicode(self[CONF_HISTORY_SIZE])),
					(u'Screen size', unicode(self[CONF_SCREEN])),
			]
			# add screen orientation option for 3rd-edition devices
			if s60_version_info[0] >= 3:
					slist.append((u'Screen orientation', unicode(self[CONF_ORIENTATION])))
			self.settings_list.set_list(slist, self.settings_list.current())
			ao_yield()
		elif DEBUG:
			print "Settings: update: No list to update!"

	def show(self, callback=None):
		"""Create and show a settings editor"""
		self.settings_list = Listbox([(u'dummy',u'item')])
		self.update()
		# save previous application state
		previous_body = app.body
		previous_menu = app.menu
		previous_exit_key_handler = app.exit_key_handler
		# show the settings editor
		app.body = self.settings_list
		self.settings_list.bind(EKeyRightArrow, self._modify)
		self.settings_list.bind(EKeyEdit, self._modify)
		self.settings_list.bind(EKeySelect, self._modify)
		self.settings_list.bind(EKeyYes, self.exit.signal)
		app.menu =[
			(u'Modify', self._modify),
			(u'Close', self.exit.signal),
		]
		app.exit_key_handler = self.exit.signal
		# wait for a signal to exit the settings editor
		self.exit.wait()
		# exit the editor
		app.body = previous_body
		app.menu = previous_menu
		app.exit_key_handler = previous_exit_key_handler
		del(self.settings_list)	# destroy list UI to save memory
		if callback:
			callback()
		
	def _modify(self):
		"""edit a setting"""
		selection = self.settings_list.current()
		if selection == 0:
			self.encoding()
		elif selection == 1:
			self.newlines()
		elif selection == 2:
			self.casesensitive()
		elif selection == 3:
			self.font()
		elif selection == 4:
			self.font_size()
		elif selection == 5:
			self.linenos()
		elif selection == 6:
			self.history_max()
		elif selection == 7:
			self.screen()
		elif selection == 8:
			self.orientation()
		self.update()
		self.save()

	def history_max(self):
		"""set the maximum history size"""
		newsize = query(u'Max history size:', 'number', self[CONF_HISTORY_SIZE])
		if newsize != None:
			self[CONF_HISTORY_SIZE] = newsize

	def casesensitive(self):
		options = [u'Yes', u'No']
		selection = popup_menu(options, u'Case-sensitive find:')
		if selection != None:
			self[CONF_CASE_SENSITIVE] = str(options[selection]).lower()

	def linenos(self):
		options = [u'Yes', u'No']
		selection = popup_menu(options, u'Display line number:')
		if selection != None:
			self[CONF_LINE_NUMBERS] = str(options[selection]).lower()

	def newlines(self):
		options = [u'Unix', u'Windows']
		newstyle = popup_menu(options, u'New lines:')
		if newstyle != None:
			self[CONF_NEW_LINES] = str(options[newstyle]).lower()

	def screen(self):
		"""change the screen size"""
		options = [u'Normal', u'Large', u'Full']
		new_screen = popup_menu(options, u'Screen size:')
		# save the changes
		if new_screen != None:
			self[CONF_SCREEN] = str(options[new_screen]).lower()
			app.screen = self[CONF_SCREEN]

	def font(self):
		"""change the display font"""
		# get a list of fonts
		fonts = available_fonts()
		fonts.sort()
		# display a searchable list
		selection = selection_list(choices=fonts,search_field=1)
		if selection != None:
			self[CONF_FONT] = str(fonts[selection])

	def font_size(self):
		"""set the font size"""
		newsize = query(u'Font size:', 'number', self[CONF_FONT_SIZE])
		if newsize != None:
			self[CONF_FONT_SIZE] = newsize

	def encoding(self):
		"""set the file encoding"""
		# get a list of codecs to display
		codecs = [unicode(enc) for enc in aliases.aliases]
		codecs.sort()
		# display a searchable list
		selection = selection_list(choices=codecs, search_field=1)
		if selection != None:
			self[CONF_ENCODING] = str(codecs[selection]).lower()

	def orientation(self):
		"""change the screen orientation"""
		# create list of options
		options = [u'Automatic', u'Portrait', u'Landscape']
		# display a searchable list
		selection = selection_list(choices=options, search_field=1)
		if selection != None:
			self[CONF_ORIENTATION] = str(options[selection]).lower()
			app.orientation = self[CONF_ORIENTATION]

class Editor:
	"""A simple text editor for s60

	Copyright Chetan Padia ( chetbox [at] gmail [dot] com )
	Released under GPLv2 (See COPYING.txt)
	"""
	
	def __init__(self):
		self.config = Settings(CONFFILE)
		self.hasFocus = True

	def run(self):
		"""Start EasyEdit"""
		def exitHandler():
			"""Stop EasyEdit"""
			self.running = False
		focusLock = Ao_lock()
		def focusHandler(f):
			self.hasFocus = f
			if f:
				focusLock.signal()
		# save current state
		old_title = app.title
		old_screen = app.screen
		old_exit_key_handler = app.exit_key_handler
		old_body = app.body
		old_menu = app.menu
		old_focus_handler = app.focus
		app.title = u'EasyEdit' # should be handled by "titlebar"
		app.screen = self.config[CONF_SCREEN]
		# create editor environment
		self.text = Text()
		self.path = None
		# set up menu
		app.menu=[
		#	(u'File', (
		#		(u'New', self.f_new),
		#		(u'Open', self.f_open),
		#		(u'Open recent', self.f_recent),
		#		(u'Save', self.f_save),
		#		(u'Save As', self.f_save_as),
		#	)),
		#	(u'Search', (
		#		(u'Find', self.s_ffind),
		#		(u'Find next', self.s_find),
		#		(u'Find previous', self.s_rfind),
		#		(u'Replace', self.s_replace),
		#		(u'Go to line', self.s_line),
		#	)),
			(u'Settings', self.config.show),
		#	(u'Help', (
		#		(u'Open README', self.h_readme),
		#		(u'About EasyEdit', self.h_about),
		#	)),
			(u'Exit', exitHandler),
			]
		# start editing a new document
		"""self.f_new()"""
		# display editor
		app.body = self.text
		app.exit_key_handler = exitHandler
		app.focus = focusHandler
		"""app.focus = self._changefocus
		# set the 'dial' key to save document
		self.text.bind(EKeyYes, self.f_save)"""
		#
		self.running = True
		while self.running:
			# display line numbers if enabled
			if self.hasFocus:
				if self.config[CONF_LINE_NUMBERS] == 'yes':
					cur_pos = self.text.get_pos()
					# ...
					ao_yield()
				ao_sleep(0.2)	# refresh rate of line numbers (seconds)
			else:
				focusLock.wait()
		# save file?
		# ...
		# restore original state
		app.title = old_title
		app.screen = old_screen
		app.exit_key_handler = old_exit_key_handler
		app.body = old_body
		app.menu = old_menu
		app.focus = old_focus_handler

		
	def save_query(self):
		if self.path != None and len(self.path > 0) and exists(self.path):
			# read file and compare to current
			f = open(self.path, 'r')
			text = f.read().decode(self.config[CONF_ENCODING])
			f.close()
			# text if same as current text
			
			if str(self.text.get()) == 
		

# run the editor!
if __name__ == '__main__':
	Editor().run()

