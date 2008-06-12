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
DEBUG = True
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
from key_codes import EKeyLeftArrow, EKeyRightArrow, EKeyBackspace, EKey1, EKey2, EKeyEdit, EKeyYes
from e32 import Ao_lock, ao_yield, ao_sleep, s60_version_info, drive_list
from os.path import exists, isfile, isdir, join
from sys import getdefaultencoding, exc_info
from encodings import aliases
from graphics import FONT_ANTIALIAS
from dir_iter import Directory_iter


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
	
	def temporary(self, message):
		app.title = unicode(message)
		ao_yield()
	
	def refresh(self):
		app.title = self.title
		ao_yield()
	
	def run(self, id, message, function, separator=u' > '):
		return self._run(False, id, message, function)
	
	def run_no_path(self, id, message, function, separator=u' > '):
		return self._run(True, id, message, function)
	
	def _run(self, override, id, message, function, separator=u' > '):
		"""Execute a function while displaying a message on the Titlebar"""
		oldtitle = self.title
		oldid = self.current_id
		self.currentid = id
		if override:
			self.title = unicode(message)
		else:
			self.title = oldtitle + separator + unicode(message)
		retval = function()
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

	def __init__(self, path, titlebar=Titlebar('settings')):
		dict.__init__(self)
		self.titlebar = titlebar
		self.path = path
		self.exit = Ao_lock()
		# create a new configuration if one does not exist
		existing_conf = isfile(self.path)
		self.keep_config = False
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
			self.update(dict([(id, default) for (id,description,default,s60,options) in self.db]))
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
						for (id,description,default,s60,options) in self.db
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
			self.settings_list = Listbox([(u'dummy',u'item')], lambda: self._modify(self.settings_list.current()))
			self.refresh_ui()
			# save previous application state
			previous_body = app.body
			previous_menu = app.menu
			previous_exit_key_handler = app.exit_key_handler
			# show the settings editor
			app.body = self.settings_list
			self.settings_list.bind(EKeyEdit, lambda: self._modify(self.settings_list.current()))
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
				for (id,description,default,s60,options) in self.db
				if s60_version_info[0] >= s60
					and options != None
			][selection]
		# save a copy of current config
		oldconfig = self.copy()
		# display options
		selection = None
		if options.__class__ == type:
			if options == int:
				selection = query(unicode(description), 'number', self[id])
			if selection != None:
				self[id] = selection
		elif options.__class__ == list:
			if len(options) <= 4:
				selection = popup_menu([unicode(option).capitalize() for option in options], unicode(description))
			else:
				options = [unicode(option) for option in options]
				options.sort()
				selection = selection_list(choices=options, search_field=True)
			if selection != None:
				self[id] = str(options[selection])
		elif DEBUG:
			print("Settings : Unsupported type " + str(options.__class__))
		self.refresh_ui()
		# save if any changes have been made
		if oldconfig != self:
			self.save()


class Filebrowser (Directory_iter):
	def __init__(self, initial_dir='\\', titlebar=Titlebar('filebrowser')):
		self.drive_list = drive_list()
		Directory_iter.__init__(self, self.drive_list)
		if initial_dir != '\\':
			if isdir(initial_dir):
				self.path = initial_dir
				self.at_root = 0
			elif DEBUG:
				print("Filebrowser : Directory does not exist " + str(initial_dir))
		self.lock = Ao_lock()
		self.titlebar = titlebar
		self.listbox = None
		
	def __getSelection(self):
		if self.at_root:
			return str(self.drive_list[self.listbox.current()])
		else:
			return join(self.path, str(self.entry(self.listbox.current())))
			
	abs_path = property(fget=__getSelection)
		
	def refresh_ui(self):
			self.titlebar.temporary(self.path)
			self.listbox.set_list(self.list_repr())
			ao_yield()
	
	def show_ui(self, return_dir=False):
		def show_ui():
			self.return_path = None
			def select():
				self.return_path = self.abs_path
				note(unicode(self.return_path))
				self.lock.signal()
			def descend():
				selection = self.listbox.current()
				path = self.entry(selection)
				if self.at_root or isdir(path):
					self.add(selection)
					self.refresh_ui()
			def ascend():
				if self.path != '\\':
					self.pop()
					self.refresh_ui()
			# save ui state
			body_previous = app.body
			menu_previous = app.menu
			exit_previous = app.exit_key_handler
			# show file browser
			app.menu = [
				(u' []   Select', select),
				(u' <-   Parent directory', ascend),
				(u' ->   Enter directory', descend),
			#	(u' 1    New directory', self._mkdir),
			#	(u' 2    Execute file', self._run),
			#	(u'ABC   Rename', self._rename),
			#	(u' C    Delete', self._delete),
				(u'Cancel', self.lock.signal),
			]
			self.listbox = Listbox([(u'dummy', u'item')], select)
			self.listbox.bind(EKeyRightArrow, descend)
			self.listbox.bind(EKeyLeftArrow, ascend)
			self.refresh_ui()
			app.body = self.listbox
			app.exit_key_handler = self.lock.signal
			ao_yield()
			self.lock.wait()
			listbox = None	# let the listbox be garbage collected
			# restore ui state
			app.body = body_previous
			app.menu = menu_previous
			app.exit_key_handler = exit_previous
			return self.return_path
		return self.titlebar.run_no_path('filebrowser', unicode(self.path), show_ui)


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
				(u'Open', self.f_open),
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
		# set the 'dial' key to save document
		self.text.bind(EKeyYes, self.f_save)
		quit_app = None
		while quit_app == None:
			self.running = True
			while self.running:
				# display line numbers if enabled
				if self.hasFocus:
					if self.config[CONF_LINE_NUMBERS] == 'yes':
						n = self.text.get()[0:self.text.get_pos()].replace(u'\u2029',u'\n').count(u'\n')
						self.titlebar.prepend('document', u'[' + unicode(n + 1) + '] ')
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
		return text.replace(u'\n', u'\r\n').encode(self.config[CONT_ENCODING])
	
	def decode(self, text):
		"""decode text according to settings"""
		return unicode(text.decode(self.config[CONF_ENCODING]))
	
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
		self.titlebar.run_no_path('refresh', u'...busy...', refresh)

	def f_new(self):
		"""start a new, blank document"""
		if self.save_query() != None:
			self.text.clear()
			self.refresh()
			self.path = None
	
	def f_open(self):	# to test properly - FileBrowser cannot return dirs!
		"""open an existing document"""
		fb = Filebrowser(self.config[CONF_LAST_DIR])
		path = fb.show_ui()
		f = open(path)
		text = f.read()
		f.close()
		self.text.set(self.decode(text))
		self.text.set_pos(0)
	
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
