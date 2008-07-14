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
VERSION=(2, 0, 5)
DEBUG = True
CONFFILE='C:\\SYSTEM\\Data\\EasyEdit.conf.dev'
BUSY_MESSAGE = u'[busy]'

# configuration file keys
CONF_VERSION		= 'version'
CONF_SCREEN		= 'screen size'
CONF_ORIENTATION	= 'screen orentation'
CONF_FONT		= 'font'
CONF_FONT_SIZE		= 'font size'
CONF_FONT_COLOUR	= 'font colour'
CONF_FONT_ANTIALIAS	= 'font anti-aliasing'
CONF_ENCODING		= 'encoding'
CONF_HISTORY		= 'history'
CONF_HISTORY_SIZE	= 'history size'
CONF_LAST_DIR		= 'last dir'
CONF_NEW_LINES		= 'new lines'
CONF_LINE_NUMBERS	= 'line numbers'
CONF_CASE_SENSITIVE	= 'case-sensitive search'

from appuifw import *
from key_codes import EKeyLeftArrow, EKeyRightArrow, EKeyBackspace, EKey1, EKey2, EKeyEdit, EKeyYes
from e32 import Ao_lock, ao_yield, ao_sleep, s60_version_info, drive_list
from os import rename, mkdir, remove, rmdir, listdir
from os.path import exists, isfile, isdir, join, basename, dirname, normpath
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
		self.running = False
		self.current_id = id
	
	def temporary(self, message):
		"""set title but do not remember it when changed"""
		app.title = unicode(message)
		ao_yield()
	
	def refresh(self):
		"""set the titlebar to the current stored value"""
		app.title = self.title
		ao_yield()
	
	def __run(self, override, id, message, function, separator=u' > '):
		"""Execute a function while displaying/appending a message on the Titlebar"""
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
	
	def run(self, id, message, function, separator=u' > '):
		"""Execute a function while appending a message to the Titlebar"""
		return self.__run(False, id, message, function)
	
	def run_no_path(self, id, message, function, separator=u' > '):
		"""Execute a function while displaying a message on the Titlebar"""
		return self.__run(True, id, message, function)
	
	def prepend(self, id, message):
		"""temporarily prepends a string to the current titlebat text"""
		if self.current_id == id:
			app.title = unicode(message) + self.title
			ao_yield()

class Settings (dict):
	"""Settings manager"""
	
	def set_screen_size(x):
		"""action when a new screen size is selected"""
		app.screen = x
	
	def set_screen_orientation(x):
		"""action when a new screen orientation is selected"""
		app.orientation = x
	
	db = [
		# id				description		default			min. s60_version	options (None => no dialog)			immediate action f(option)
		(CONF_VERSION,			'Version',		VERSION,		1,			None,						None				),
		(CONF_ENCODING,			'File encoding',	getdefaultencoding(),	1,			[unicode(enc) for enc in aliases.aliases],	None				),
		(CONF_NEW_LINES,		'New lines',		'unix',			1,			['unix', 'windows'],				None				),
		(CONF_CASE_SENSITIVE,		'Case sensitive find',	'no',			1,			['yes', 'no'],					None				),
		(CONF_FONT,			'Font',			Text().font[0],		1,			available_fonts(),				None				),
		(CONF_FONT_SIZE,		'Font size',		15,			2,			int,						None				),
		(CONF_FONT_COLOUR,		'Font colour',		(0,0,0),		1,			None,						None				),
		(CONF_FONT_ANTIALIAS,		'Font anti-aliasing',	'no',			2,			['yes', 'no'],					None				),
		(CONF_LINE_NUMBERS,		'Display line number',	'yes',			1,			['yes', 'no'],					None				),
		(CONF_LAST_DIR,			'Last used directory',	'\\',			1,			None,						None				),
		(CONF_HISTORY,			'History',		[],			1,			None,						None				),
		(CONF_HISTORY_SIZE,		'Max history size',	8,			1,			int,						None				),
		(CONF_SCREEN,			'Screen Size',		'normal',		1,			['large', 'normal', 'full'],			set_screen_size			),
		(CONF_ORIENTATION,		'Screen orientation',	'automatic',		3,			['automatic', 'portrait', 'landscape'],		set_screen_orientation		),
	]
	saveRequired = False
	
	def __setitem__(self, key, value):
		"""equivalent to dict.__setitem__ but flags saveRequired"""
		self.saveRequired = True
		dict.__setitem__(self, key, value)

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
				self.keep_config = not(query(u'Reset settings?', 'query'))
				existing_conf = False
		if not(existing_conf):
			if DEBUG:
				print("Creating new config...")
			# set current settings to these defaults
			self.update(dict([(id, default) for (id,description,default,s60,options,action) in self.db]))
			self.save()

	def save(self):
		"""Save current config to disk"""
		if DEBUG:
			print("Saving settings to " + self.path)
		if self.saveRequired and not(self.keep_config):
			try:
				f = open(self.path, 'w')
				f.write(repr(self))
				f.close()
				self.saveRequired = False
				self.keep_config = False
			except:
				note(u'Error saving config', 'error')
		elif DEBUG:
			print("Config not saved")

	def refresh_ui(self):
		"""Update the Settings panel with the current settings"""
		if self.settings_list:
			slist = [(unicode(description), unicode(self[id]))
						for (id,description,default,s60,options,action) in self.db
						if s60_version_info[0] >= s60
							and options != None
					]
			self.settings_list.set_list(slist, self.settings_list.current())
			ao_yield()
		elif DEBUG:
			print("Settings: update: No list to update!")

	def show_ui(self, callback=None):
		"""Create and show a settings editor"""
		def show():
			def _modify(selected):
				"""edit a setting"""
				(id, description, options, action, supported_s60_version) = \
					[(id, description, options, action, s60)
						for (id,description,default,s60,options,action) in self.db
						if s60_version_info[0] >= s60
							and options != None
					][selected]
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
				# run any immediate action if one has been defined
				if action != None and s60_version_info[0] >= supported_s60_version:
					try:
						action(self[id])
					except:
						note(u'Error setting ' + unicode(description), 'error')
			self.settings_list = Listbox([(u'dummy',u'item')], lambda: _modify(self.settings_list.current()))
			self.refresh_ui()
			# save previous application state
			previous_body = app.body
			previous_menu = app.menu
			previous_exit_key_handler = app.exit_key_handler
			# show the settings editor
			app.body = self.settings_list
			self.settings_list.bind(EKeyEdit, lambda: _modify(self.settings_list.current()))
			self.settings_list.bind(EKeyYes, self.exit.signal)
			app.menu =[
				(u'Modify', lambda: _modify(self.settings_list.current())),
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


class Filebrowser (Directory_iter):
	def __init__(self, initial_dir='\\', titlebar=Titlebar('filebrowser')):
		self.drive_list = drive_list()
		Directory_iter.__init__(self, self.drive_list)
		# set initial directory if one has been specified
		if initial_dir != '\\':
			if isdir(initial_dir):
				self.path = initial_dir
				self.at_root = False
				# go up a directory if directory current is empty - listbox cannot display empty lists!
				if len(self.list_repr()) == 0:
					self.pop()
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
		
	def refresh_ui(self, current=0):
		"""refresh the current file list
		current sets the current selection"""
		dir_listing = self.list_repr()
		if len(dir_listing) > 0:
			self.titlebar.temporary(self.path)
			self.listbox.set_list(dir_listing, current)
			ao_yield()
		else:
			self.pop()
			note(u'Empty directory', 'info')
	
	def show_ui(self, allow_directory=False):
		"""show the file browser - returns the path selected
		allow_directory = True allows a directory to be selected"""
		def show_ui():
			self.return_path = None
			def descend():
				"""open the currently selected directory"""
				selection = self.listbox.current()
				path = self.entry(selection)
				if self.at_root or isdir(path):
					self.add(selection)
					self.refresh_ui()
			def ascend():
				"""go up the directory hierarchy"""
				if self.path != '\\':
					self.pop()
					self.refresh_ui()
			def select():
				"""select the current file or open the directory"""
				if allow_directory or isfile(self.abs_path):
					self.return_path = self.abs_path
					self.lock.signal()
				else:
					descend()
			def rename_file():
				"""Rename the currently selected file"""
				path = self.entry(self.listbox.current())
				filename = basename(path)
				new_name = query(u'Rename ' + filename, 'text', unicode(filename))
				if new_name != None:
					try:
						new_path = dirname(path) + str(new_name)
						rename(path, new_path)
						note(u'File renamed', 'info')
					except:
						note(u'Error renaming file', 'error')
					self.refresh_ui()
			def create_directory():
				"""create a new directory at the current location"""
				if self.at_root:
					note(u'Cannot create directory here', 'info')
				else:
					dir_name = query(u'Directory name', 'text', u'New directory')
					if dir_name != None:
						try:
							mkdir(join(self.path, str(dir_name)))
						except:
							note(u'Error creating directory', 'error')
						self.refresh_ui()
			def delete_file():
				path = self.entry(self.listbox.current())
				change_made = False
				if isfile(path):
					if query(u'Delete ' + unicode(basename(path)) + u'?', 'query'):
						try:
							remove(path)
							change_made = True
						except:
							note(u'Error delecting file', 'error')
				elif isdir(path):
					if len(listdir(path)) == 0:
						try:
							rmdir(normpath(path))
							change_made = True
						except:
							note(u'Error deleting directory', 'error')
					else:
						note(u'Directory is not empty', 'info')
				if change_made:
					self.refresh_ui()
			def os_open():
				"""open the currently selected file with the default application specified by the OS"""
				if isfile(self.entry(self.listbox.current())):
					try:
						Content_handler().open_standalone(self.entry(self.listbox.current()))
					except:
						note(u'Error opening file', 'error')
			# save ui state
			body_previous = app.body
			menu_previous = app.menu
			exit_previous = app.exit_key_handler
			# show file browser
			app.menu = [
				(u' []   Select', select),
				(u' <-   Parent directory', ascend),
				(u' ->   Enter directory', descend),
				(u' 1    New directory', create_directory),
				(u' 2    Open with OS', os_open),
				(u'ABC  Rename', rename_file),
				(u' C    Delete', delete_file),
			]
			self.listbox = Listbox([(u'dummy', u'item')], select)
			self.listbox.bind(EKeyLeftArrow, ascend)
			self.listbox.bind(EKeyRightArrow, descend)
			self.listbox.bind(EKey1, create_directory)
			self.listbox.bind(EKey2, os_open)
			self.listbox.bind(EKeyEdit, rename_file)
			self.listbox.bind(EKeyBackspace, delete_file)
			self.refresh_ui()
			app.body = self.listbox
			app.exit_key_handler = self.lock.signal
			ao_yield()
			self.lock.wait()
			self.listbox = None	# let the listbox be garbage collected
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
		self.filebrowser = None
		self.__document_lock = None

	def __open_document(self, path, read_from_disk=True):
		"""Open a document by reading from disk, and showing "busy" status.
		Locks until called again"""
		oldpath = self.path
		self.path = path
		if self.__document_lock != None:
			self.__document_lock.signal()
		def open_document():
			error = False
			if read_from_disk:
				# show "busy" message
				self.titlebar.prepend('document', BUSY_MESSAGE + u' ')
				try:
					# read file from disk
					f = open(path)
					text = f.read()
					f.close()
					text = self.decode(text)
					# show file in editor
					self.text.clear()
					self.refresh()
					self.text.set(text)
					self.text.set_pos(0)
				except:
					note(u'Error opening file', 'error')
					# ask user if they wish to remove it from the recent document list
					if query(u'Remove from Recent Documents?', 'query'):
						self.config[CONF_HISTORY].remove(path)
						self.config.save()
					# fallback to the previous document if there was an error
					self.__open_document(oldpath, read_from_disk=False)
					error = True
			if not(error):
				if self.__document_lock == None:
					self.__document_lock = Ao_lock()
				#self.__document_lock.wait()	# seems to block UI! =(
				self.__document_lock = None
		if path != None:
			# add to recent list
			if path in self.config[CONF_HISTORY]:
				self.config[CONF_HISTORY].remove(path)
			self.config[CONF_HISTORY] = ([path] + self.config[CONF_HISTORY])[:self.config[CONF_HISTORY_SIZE]]
			self.config.save()
			# show filename in titlebar until a different file is opened
			self.titlebar.run('document', unicode(basename(path)), open_document)

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
		app.orientation = self.config[CONF_ORIENTATION]
		# create editor environment
		self.text = Text()
		self.path = None
		# set up menu
		app.menu=[
			(u'File', (
				(u'New', self.f_new),
				(u'Open', self.f_open),
				(u'Open recent', self.f_open_recent),
				(u'Save', self.f_save),
				(u'Save As', self.f_save_as),
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
					# lock to stop busy waiting when app is not in focus
					focusLock.wait()
			# intent to close application has now been expressed
			quit_app = self.save_query()
		# application should now be closing
		# unlock any pending locks
		if self.__document_lock != None:
			self.__document_lock.signal()
		# restore original state
		app.title = old_title
		app.screen = old_screen
		app.exit_key_handler = old_exit_key_handler
		app.body = old_body
		app.menu = old_menu
		app.focus = old_focus_handler
		
	def encode(self, text):
		"""encode text accoridng to settings"""
		# ensure all new-lines are represented as '\n'
		encoded_text = text.replace(u'\u2029',u'\n')
		# convert to windows format if required
		if self.config[CONF_NEW_LINES] == 'windows':
			encoded_text = encoded_text.replace(u'\n', u'\r\n')
		# convert text
		encoded_text = encoded_text.encode(self.config[CONF_ENCODING])
		return encoded_text
	
	def decode(self, text):
		"""decode text according to settings"""
		# decode text
		decoded_text = unicode(text.decode(self.config[CONF_ENCODING]))
		# replace windows new lines if necessary
		if self.config[CONF_NEW_LINES] == 'windows':
			decoded_text = decoded_text.replace(u'\r\n', u'\n')
		return decoded_text
	
	def exists(self):
		"""handy function that checks if the open document exists on disk (may have different contents)"""
		return (self.path != None) and (len(self.path) > 0) and isfile(self.path)
		
	def save_query(self):
		"""check if file needs saving and prompt user if necessary - returns user reponse"""
		save = False
		save_required = True
		current_text = self.text.get()
		if self.exists():
			# read file and compare to current
			f = open(self.path, 'r')
			saved_text = f.read()
			f.close()
			if saved_text == self.encode(current_text):
				save_required = False
		elif len(current_text) == 0:
			save_required = False
		if save_required:
			if DEBUG:
				print("Save required")
			save = popup_menu([u'Yes', u'No'], u'Save file?')
			if save != None:
				save = not(save)	# because 0 => yes, 0 => no
				if save == True:
					self.f_save()
		return save

	def refresh(self):
		"""refresh the editor view"""
		def refresh():
			cursor_position = self.text.get_pos()
			text = self.text.get()
			self.text.font = (
				unicode(self.config[CONF_FONT]),
				self.config[CONF_FONT_SIZE],
				(self.config[CONF_FONT_ANTIALIAS] == 'yes') and FONT_ANTIALIAS
			)
			self.text.color = self.config[CONF_FONT_COLOUR]
			self.text.set(text)
			self.text.set_pos(cursor_position)
		self.titlebar.run_no_path('refresh', BUSY_MESSAGE, refresh)

	def f_new(self, force=False):
		"""start a new, blank document"""
		if force or self.save_query() != None:
			self.text.clear()
			self.refresh()
			#self.path = None
			self.__open_document(None)
	
	def __save_last_dir(self, path):
		"""save the location of the last viewed directory in self.config"""
		if isdir(path):
			self.config[CONF_LAST_DIR] = normpath(path)
		else:
			self.config[CONF_LAST_DIR] = dirname(normpath(path))
		self.config.save()

	def f_open(self):
		"""open an existing document"""
		# show file selector
		path = None
		if self.filebrowser == None:
			self.filebrowser = Filebrowser(self.config[CONF_LAST_DIR], self.titlebar)
		path = self.filebrowser.show_ui()
		# show "save?" dialog if necesary and open document
		if path != None:
			self.__save_last_dir(path)
			if self.save_query() != None:
				# open the document
				self.__open_document(path)
	
	def f_open_recent(self):
		"""select a file to open from the recent document list"""
		lock = Ao_lock()
		listbox = None
		def select():
			self.__open_document(self.config[CONF_HISTORY][listbox.current()])
			lock.signal()
		def current_list():
			return [(basename((unicode(file))), dirname(unicode(file))) for file in self.config[CONF_HISTORY]]
		def remove_recent():
			if query(u'Remove from recent documents?', 'query'):
				self.config[CONF_HISTORY].remove(self.config[CONF_HISTORY][listbox.current()])
				self.config.save()
				new_list = current_list()
				if len(new_list) > 0:
					listbox.set_list(current_list())
				else:
					note(u'No more recent documents', 'info')
					lock.signal()
		def exit_key_handler():
			lock.signal()
		# save previous application state
		previous_body = app.body
		previous_menu = app.menu
		previous_exit_key_handler = app.exit_key_handler
		list = current_list()
		if len(list) > 0:
			listbox = Listbox(list, select)
			app.body = listbox
			app.exit_key_handler = exit_key_handler
			listbox.bind(EKeyBackspace, remove_recent)
			lock.wait()
			# exit the editor
			app.body = previous_body
			app.menu = previous_menu
			app.exit_key_handler = previous_exit_key_handler
		else:
			note(u'No recent documents', 'info')
			
	def f_save(self, force=False):
		"""save the current file - force skips exist check"""
		if force or self.exists():
			# show "busy" message
			self.titlebar.prepend('document', BUSY_MESSAGE + u' ')
			try:
				text = self.encode(self.text.get())
				f=open(self.path, 'w')
				f.write(text)
				f.close()
				note(u'File saved','conf')
			except:
			    note(u'Error saving file.','error')
			# clear "busy" message
			self.titlebar.refresh()
		else:
			self.f_save_as()
	
	def f_save_as(self):
		"""save current file at a new location"""
		# show file selector
		path = None
		if self.filebrowser == None:
			self.filebrowser = Filebrowser(self.config[CONF_LAST_DIR], self.titlebar)
		path = self.filebrowser.show_ui(allow_directory=True)
		if path != None:
			# assume a directory has been selected -  suggest a filename in the current directory
			new_file_location = dirname(path)
			containing_dir = basename(path)
			# <hack>
			if len(new_file_location) == 2:	# if new_file_location is just a drive letter (top-level)
				new_file_location += '\\' # append a \ 
			# </hack>
			suggested_filename = join(containing_dir, 'untitled.txt')
			# if a file is selected update the suggested name with its name
			if isfile(path):
				current_filename = containing_dir	# if a dir was not selected containing_dir is the filename
				containing_dir = basename(new_file_location)
				new_file_location = dirname(new_file_location)
				suggested_filename = join(containing_dir, current_filename)
			new_filename = query(unicode(new_file_location), 'text', unicode(suggested_filename))
			if new_filename != None:
				self.path = join(new_file_location, new_filename)
				self.__save_last_dir(self.path)
				# check if file already exists and ask if it should be replaced
				save_possible = False
				if isfile(self.path):
					save_possible = query(u'Overwite file?', 'query')
				elif isdir(self.path):
					note(u'Not saved: A directory exists with that name', 'info')
				else:
					save_possible = True
				if save_possible:
					self.f_save(force=True)	# force prevents another call to f_save_as


# run the editor!
if __name__ == '__main__':
	Editor().run()
