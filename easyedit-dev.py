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
from os.path import exists, isfile
from sys import getdefaultencoding
from encodings import aliases
from graphics import FONT_ANTIALIAS
from dir_iter import *


class Titlebar (object):
	"""A class to manage the S60 Titlebar"""		
	
	# create a wrapper around the titlebar text which ignores prepended text
	def __setTitle(self, value):
		self.__title = app.title = value
		ao_yield()
	
	def __getTitle(self):
		return self.__title
	
	title = property(fget = __getTitle, fset = __setTitle)
	
	def __init__(self, id='default', default=app.title):
		self.__title = unicode(default)
		self.running = 0
		self.current_id = id
	
	def run(self, id, message, function, *args):
		return self._run(False, id, message, function, *args)
	
	def run_no_path(self, id, message, function, *args):
		return self._run(True, id, message, function, *args)
	
	def _run(self, override, id, message, function, *args):
		"""Execute a function while displaying a message on the Titlebar"""
		separator = u" > "
		oldtitle = self.title
		oldid = self.current_id
		self.currentid = id
		if override:
			self.title = unicode(message)
		else:
			self.title = oldtitle + separator + unicode(message)
		retval = None
		try:
			retval = function(*args)
		except:
			if DEBUG:
				print "Titlebar: Error in " + function.__name__
		self.title = oldtitle
		self.currentid = oldid
		ao_yield()
		return retval
	
	def prepend(self, id, message):
		if self.current_id == id:
			app.title = unicode(message) + self.title
			ao_yield()

class Settings (dict):
	"""Settings manager"""
	
	db = [
		# id					description				default					min. s60_version	options (None => no dialog)
		(CONF_VERSION,			'Version',				VERSION,				1,					None										),
		(CONF_ENCODING,			'File encoding',		getdefaultencoding(),	1,					[unicode(enc) for enc in aliases.aliases]	),
		(CONF_NEW_LINES,		'New lines',			'unix',					1,					['unix', 'windows']							),
		(CONF_CASE_SENSITIVE,	'Case sensitive find',	'no',					1,					['yes', 'no']								),
		(CONF_FONT,				'Font',					Text().font[0],			1,					available_fonts()							),
		(CONF_FONT_SIZE,		'Font size',			15,						2,					int											),
		(CONF_FONT_COLOUR,		'Font colour',			(0,0,0),				1,					None										),
		(CONF_LINE_NUMBERS,		'Display line number',	'yes',					1,					['yes', 'no']								),
		(CONF_LAST_DIR,			'Last used directory',	'\\',					1,					None										),
		(CONF_HISTORY,			'History',				[],						1,					None										),
		(CONF_HISTORY_SIZE,		'Max history size',		8,						1,					int											),
		(CONF_SCREEN,			'Screen Size',			'normal',				1,					['large', 'normal', 'full']					),
		(CONF_ORIENTATION,		'Screen orientation',	'automatic',			3,					['automatic', 'portrait', 'landscape']		),
	]
	keep_config = False
	titlebar = None
	
	def __init__(self, path, titlebar=None):
		dict.__init__(self)
		if titlebar != None:
			self.titlebar = titlebar
		else:
			self.titlebar = Titlebar()
		self.path = path
		self.exit = Ao_lock()
		# create a new configuration if one does not exist
		existing_conf = isfile(self.path)
		if existing_conf:
			try:
				# read the config file from disk
				f = open(self.path, 'r')
				conf_string = f.read()
				f.close()
				self.update(eval(conf_string))
				# check if a new version has been installed
				existing_conf = (self[CONF_VERSION] == VERSION)
			except:
				if DEBUG:
					print("Cannot read config file " + self.path)
				note(u'Error reading settings', 'error')
				if query(u'Reset settings?', 'query'):
					self.keep_config = False
				else:
					self.keep_config = True
				existing_conf = False
		if not(existing_conf):
			if DEBUG:
				print("Creating new config...")
			textbox_font = Text().font	# not very nice, but it does what is required
			# set current settings to these defaults
			self.update(dict([(id, default) for (id,description,default,s60,options) in self.SETTINGS]))
			self.save()

	def save(self):
		"""Save current config to disk"""
		if DEBUG:
			print("Saving settings to " + self.path)
		if not(self.keep_config):
			f = open(self.path, 'w')
			f.write(repr(self))
			f.close()
		elif DEBUG:
			print("Config error on startup, not saved")

	def refresh_ui(self):
		"""Update the Settings panel with the current settings"""
		if self.settings_list:
			slist = [(unicode(description), unicode(self[id]))
						for (id,description,default,s60,options) in self.SETTINGS
						if s60_version_info[0] >= s60
							and options != None
					]
			self.settings_list.set_list(slist, self.settings_list.current())
			ao_yield()
		elif DEBUG:
			print "Settings: update: No list to update!"

	def show_ui(self, callback=None):
		"""Create and show a settings editor"""
		def show():
			self.settings_list = Listbox([(u'dummy',u'item')])
			self.refresh_ui()
			# save previous application state
			previous_body = app.body
			previous_menu = app.menu
			previous_exit_key_handler = app.exit_key_handler
			# show the settings editor
			app.body = self.settings_list
			self.settings_list.bind(EKeyEdit, lambda: self._modify(self.settings_list.current()))
			self.settings_list.bind(EKeySelect, lambda: self._modify(self.settings_list.current()))
			self.settings_list.bind(EKeyYes, self.exit.signal)
			app.menu =[
				(u'Modify', lambda: self._modify(self.settings_list.current())),
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
		retval = None
		if self.titlebar != None:
			retval = self.titlebar.run('settings', u'Settings', show)
		else:
			retval = show()
		if callback != None:
			callback()
		return retval

		
	def _modify(self, selection):
		"""edit a setting"""
		(id, description, options) = \
			[(id, description, options)
				for (id,description,default,s60,options) in self.SETTINGS
				if s60_version_info[0] >= s60
					and options != None
			][selection]
		# save a copy of current config
		oldconfig = self.copy()
		# display options
		if options == int:
			selection = query(unicode(description), 'number', self[id])			
		elif len(options) <= 4:
			selection = popup_menu([unicode(option).capitalize() for option in options], unicode(description))
		elif len(options) > 4:
			options = [unicode(option) for option in options]
			options.sort()
			selection = selection_list(choices=options,search_field=1)
		if selection != None:
			self[id] = str(options[selection])
		self.refresh_ui()
		# save if any changes have been made
		if oldconfig != self:
			self.save()


class Editor:
	"""A simple text editor for s60

	Copyright Chetan Padia ( chetbox [at] gmail [dot] com )
	Released under GPLv2 (See COPYING.txt)
	"""
	
	def __init__(self):
		self.titlebar = None
		self.config = None
		self.hasFocus = False

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
		# read settings
		self.titlebar = Titlebar('document', u'EasyEdit')
		self.config = Settings(CONFFILE, self.titlebar)
		self.hasFocus = True
		# save current state
		old_title = app.title
		old_screen = app.screen
		old_exit_key_handler = app.exit_key_handler
		old_body = app.body
		old_menu = app.menu
		old_focus_handler = app.focus
		app.screen = self.config[CONF_SCREEN]
		# create editor environment
		self.text = Text()
		self.path = None
		# set up menu
		app.menu=[
			(u'File', (
				(u'New', self.f_new),
		#		(u'Open', self.f_open),
		#		(u'Open recent', self.f_recent),
				(u'Save', self.f_save),
		#		(u'Save As', self.f_save_as),
			)),
		#	(u'Search', (
		#		(u'Find', self.s_ffind),
		#		(u'Find next', self.s_find),
		#		(u'Find previous', self.s_rfind),
		#		(u'Replace', self.s_replace),
		#		(u'Go to line', self.s_line),
		#	)),
			(u'Settings', lambda : self.config.show_ui(callback=self.refresh)),
		#	(u'Help', (
		#		(u'Open README', self.h_readme),
		#		(u'About EasyEdit', self.h_about),
		#	)),
			(u'Exit', exitHandler),
			]
		# start editing a new document
		self.f_new()
		# display editor
		app.body = self.text
		ao_yield()
		app.exit_key_handler = exitHandler
		app.focus = focusHandler
		"""# set the 'dial' key to save document
		self.text.bind(EKeyYes, self.f_save)"""
		quit_app = None
		while quit_app == None:
			self.running = True
			while self.running:
				# display line numbers if enabled
				if self.hasFocus:
					if self.config[CONF_LINE_NUMBERS] == 'yes':
						cur_pos = self.text.get_pos()
						# ...
						self.titlebar.prepend('document', u'[LNO] ')
						ao_yield()
					ao_sleep(0.2)	# refresh rate of line numbers (seconds)
				else:
					focusLock.wait()
			quit_app = self.save_query()
		# restore original state
		app.title = old_title
		app.screen = old_screen
		app.exit_key_handler = old_exit_key_handler
		app.body = old_body
		app.menu = old_menu
		app.focus = old_focus_handler
		
	def encode(self, text):
		"""encode text accoridng to settings"""
		return text.replace(u'\n', u'\r\n').encode(self.settings.config[CONT_ENCODING])
	
	def decode(self, text):
		"""decode text according to settings"""
		return unicode(text.decode(self.settings.config[CONF_ENCODING]))
	
	def exists(self):
		return self.path != None and len(self.path > 0) and isfile(self.path)
		
	def save_query(self):
		save = False
		save_required = True
		current_text = self.text.get()
		if self.exists():
			# read file and compare to current
			f = open(self.path, 'r')
			saved_text = f.read().decode(self.config[CONF_ENCODING])
			f.close()
			if saved_text == encode(current_text):
				save_required = False
		if (self.path == None or len(self.path) == 0) and len(current_text) == 0:
			save_required = False
		if DEBUG:
			print("Save required")
		if save_required:
			save = popup_menu([u'Yes', u'No'], u'Save file?')
			if save != None:
				save = not(save)	# because 0 => yes, 0 => no
				if save == True:
					f_save(self)
		return save

	def refresh(self):
		"""refresh the editor view"""
		def refresh():
			cursor_position = self.text.get_pos()
			text = self.text.get()
			self.text.font = (unicode(self.config[CONF_FONT]), self.config[CONF_FONT_SIZE], FONT_ANTIALIAS)
			self.text.color = self.config[CONF_FONT_COLOUR]
			self.text.set(text)
			self.text.set_pos(cursor_position)
		self.titlebar.run_no_path('refresh', '...busy...', refresh)

	def f_new(self):
		"""open an existing document"""
		if self.save_query() != None:
			self.text.clear()
			self.refresh()
			self.path = None
	
	def f_save(self):
		"""save the current file"""
		if self.exists():
			try:
				f=open(self.path, 'w')
				f.write(encode(self.text.get()))
				f.close()
				note(u'File saved.','conf')
			except:
			    note(u'Error saving file.','error')
		else:
			pass#self.f_save_as()
			
	

# run the editor!
if __name__ == '__main__':
	Editor().run()

