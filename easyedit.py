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
VERSION=(2, 0, 8)
DEBUG = 0
CONFFILE='C:\\SYSTEM\\Data\\EasyEdit\\settings.conf'
BUSY_MESSAGE = u'[busy]'

from appuifw import *
from key_codes import EKeyLeftArrow, EKeyRightArrow, EKeyBackspace, EKey1, EKey2, EKeyEdit, EKeyYes
from e32 import Ao_lock, ao_yield, ao_sleep, s60_version_info, drive_list
from os import rename, mkdir, makedirs, remove, rmdir, listdir
from os.path import exists, isfile, isdir, join, basename, dirname, normpath
from sys import getdefaultencoding, exc_info
from encodings import aliases
from graphics import FONT_ANTIALIAS

# main configuration keys
CONF_VERSION			= 'version'
CONF_SCREEN			= 'screen size'
CONF_ORIENTATION		= 'screen orentation'
CONF_FONT			= 'font'
CONF_FONT_SIZE			= 'font size'
CONF_FONT_COLOUR		= 'font colour'
CONF_FONT_ANTIALIAS		= 'font anti-aliasing'
CONF_ENCODING			= 'encoding'
CONF_HISTORY			= 'history'
CONF_HISTORY_SIZE		= 'history size'
CONF_LAST_DIR			= 'last dir'
CONF_NEW_LINES			= 'new lines'
CONF_LINE_NUMBERS		= 'line numbers'

# search settings keys
CONF_FIND_CASE_SENSITIVE	= 'case-sensitive search'
CONF_FIND_TEXT			= 'search text'
CONF_FIND_DIRECTION		= 'search direction'
CONF_FIND_REGEXP		= 'regular expression'
CONF_REPLACE_TEXT		= 'replace text'

# config groups keys
CONF_GROUP_MAIN			= 'main'
CONF_GROUP_FIND			= 'find'
CONF_GROUP_FIND_DIRECTION	= 'find direction'
CONF_GROUP_REPLACE		= 'replace'

CONF_DB = [
	# id				group				description		default			min. s60_version	options (None => no dialog)			(a,'b') => a.b = option
	(CONF_VERSION,			CONF_GROUP_MAIN,		'Version',		VERSION,		1,			None,						None				),
	(CONF_ENCODING,			CONF_GROUP_MAIN,		'File encoding',	getdefaultencoding(),	1,			[unicode(enc) for enc in aliases.aliases],	None				),
	(CONF_NEW_LINES,		CONF_GROUP_MAIN,		'New lines',		'unix',			1,			['unix', 'windows'],				None				),
	(CONF_FONT,			CONF_GROUP_MAIN,		'Font',			Text().font[0],		1,			available_fonts(),				None				),
	(CONF_FONT_SIZE,		CONF_GROUP_MAIN,		'Font size',		15,			2,			int,						None				),
	(CONF_FONT_COLOUR,		CONF_GROUP_MAIN,		'Font colour',		(0,0,0),		1,			None,						None				),
	(CONF_FONT_ANTIALIAS,		CONF_GROUP_MAIN,		'Font anti-aliasing',	'no',			2,			['yes', 'no'],					None				),
	(CONF_LINE_NUMBERS,		CONF_GROUP_MAIN,		'Display line number',	'yes',			1,			['yes', 'no'],					None				),
	(CONF_LAST_DIR,			CONF_GROUP_MAIN,		'Last used directory',	'\\',			1,			None,						None				),
	(CONF_HISTORY,			CONF_GROUP_MAIN,		'History',		[],			1,			None,						None				),
	(CONF_HISTORY_SIZE,		CONF_GROUP_MAIN,		'Max history size',	8,			1,			int,						None				),
	(CONF_SCREEN,			CONF_GROUP_MAIN,		'Screen Size',		'normal',		1,			['large', 'normal', 'full'],			(app, 'screen')			),
	(CONF_ORIENTATION,		CONF_GROUP_MAIN,		'Screen orientation',	'automatic',		3,			['automatic', 'portrait', 'landscape'],		(app, 'orientation')		),
	(CONF_FIND_TEXT,		CONF_GROUP_FIND,		'Search text',		'',			1,			unicode,					None				),
	(CONF_REPLACE_TEXT,		CONF_GROUP_REPLACE,		'Replace text',		'',			1,			unicode,					None				),
	(CONF_FIND_DIRECTION,		CONF_GROUP_FIND_DIRECTION,	'Search direction',	'all',			1,			['all', 'next', 'previous'],			None				),
	(CONF_FIND_CASE_SENSITIVE,	CONF_GROUP_FIND,		'Case sensitive find',	'no',			1,			['yes', 'no'],					None				),
	(CONF_FIND_REGEXP,		CONF_GROUP_FIND,		'Regular expression',	'no',			1,			['yes', 'no'],					None				),
]

class Titlebar (object):
	"""A class to manage the S60 Titlebar"""		
	
	# create a wrapper around the titlebar text which ignores prepended text
	def __setTitle(self, value):
		self.__title = app.title = value
		ao_yield()
	
	def __getTitle(self):
		return self.__title
	
	title = property(fget = __getTitle, fset = __setTitle)
	current_id = None
	default_id = 'default'
	__oldtitle = []	# (id, message) elements
	
	def __init__(self, id='default', default=app.title):
		self.__title = unicode(default)
		self.current_id = id
		self.default_id = id
		self.default_title = default
	
	def temporary(self, message):
		"""set title but do not remember it when changed"""
		app.title = unicode(message)
		ao_yield()
	
	def refresh(self):
		"""set the titlebar to the current stored value"""
		app.title = self.title
		ao_yield()
	
	def _begin(self, override, id, message, separator=u' > '):
		oldtitle = (self.current_id, self.title)
		self.__oldtitle.append(oldtitle)
		self.current_id = id
		if override:
			self.title = unicode(message)
		else:
			self.title = oldtitle[1] + separator + unicode(message)
		ao_yield()
		
	def _end(self):
		if len(self.__oldtitle) > 0:
			(self.current_id, self.title) = self.__oldtitle.pop()
		else:
			self.current_id = self.default_id
			self.title = self.default_title
			ao_yield()
			
		
	def __run(self, override, id, message, function, separator=u' > '):
		"""Execute a function while displaying/appending a message on the Titlebar"""
		self._begin(override, id, message, separator)
		retval = function()
		self._end()
		return retval
	
	def run(self, id, message, function, separator=u' > '):
		"""Execute a function while appending a message to the Titlebar"""
		return self.__run(0, id, message, function)
	
	def run_no_path(self, id, message, function, separator=u' > '):
		"""Execute a function while displaying a message on the Titlebar"""
		return self.__run(1, id, message, function)
	
	def prepend(self, id, message):
		"""temporarily prepends a string to the current titlebat text"""
		if self.current_id == id:
			app.title = unicode(message) + self.title
			ao_yield()


class Settings (dict):
	"""Settings manager"""
	
	saveRequired = 0
	keep_config = 0
	db = None
	path = None
	exit = Ao_lock()
	titlebar = None
	
	def __setitem__(self, key, value):
		"""equivalent to dict.__setitem__ but flags saveRequired"""
		self.saveRequired = 1
		dict.__setitem__(self, key, value)
	
	def __init__(self, db, path, titlebar=Titlebar('settings')):
		dict.__init__(self)
		self.titlebar = titlebar
		self.path = path
		self.db = db
		# create a new configuration in memory if one does not exist
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
				self.keep_config = not(query(u'Reset settings?', 'query'))
				existing_conf = 0
		if not(existing_conf):
			note(u"Creating new configuration", 'info')
			# set current settings to these defaults
			self.update(dict([(id, default) for (id,group,description,default,s60,options,action) in self.db]))
			# create the folder containing config if it does not exist
			conf_folder = dirname(self.path)
			if not(exists(conf_folder)):
				makedirs(conf_folder)
			self.saveRequired = 1
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
				self.saveRequired = 0
				self.keep_config = 0
			except:
				note(u'Error saving config', 'error')
		elif DEBUG:
			print("Config not saved")
	
	def __currentSettingsList(self, groups_requested=[]):
		return [(id,group,description,default,s60,options,action)
			for (id,group,description,default,s60,options,action) in self.db
				if s60_version_info[0] >= s60
				and options != None		# filter out items with no user options
				and group in groups_requested	# filter by groups_requested list
		]

	def refresh_ui(self, settingsList=None):
		"""Update the Settings panel with the settings passed into settingsList"""
		if self.settings_list:	# make sure the UI control exists
			# get a list of all settings if one has not been provided
			if settingsList == None:
				settingsList = self.__currentSettingsList()
			slist = [(unicode(description), unicode(self[id]))
				for (id,group,description,default,s60,options,action) 
				in settingsList
			]
			self.settings_list.set_list(slist, self.settings_list.current())
			ao_yield()
		elif DEBUG:
			print("Settings: update: No list to update!")

	def show_ui(self, groups_requested=[], callback=None, titlebar=u'Settings', menu_items=[]):
		"""Create and show a settings editor"""
		def show():
			def modify(selected):
				"""edit a setting"""
				(id, description, options, action, supported_s60_version) = [(id, description, options, action, s60)
					for (id,group,description,default,s60,options,action) 
					in self.__currentSettingsList(groups_requested)
					][selected]
				# display options
				selection = None
				if options.__class__ == type:
					if options == int:
						selection = query(unicode(description), 'number', self[id])
					elif options == str or options == unicode:
						selection = query(unicode(description), 'text', unicode(self[id]))
					if selection != None:
						self[id] = selection
				elif options.__class__ == list:
					n_options = len(options)
					if n_options == 1:
						selection == 0
					elif n_options == 2:	# if there are only 2 options
						selection = (options.index(self[id]) + 1) % 2	# select the other option
					elif n_options > 2 and n_options <= 4:
						selection = popup_menu([unicode(option).capitalize() for option in options], unicode(description))
					else:
						options = [unicode(option) for option in options]
						options.sort()
						selection = self.titlebar.run(str(description), unicode(description), lambda: selection_list(choices=options, search_field=1))
					if selection != None:
						self[id] = options[selection]
				elif DEBUG:
					print("Settings : Unsupported type " + str(options.__class__))
				self.refresh_ui(self.__currentSettingsList(groups_requested))
				self.saveRequired = 1
				# run any immediate action if one has been defined
				if action != None and s60_version_info[0] >= supported_s60_version:
					try:
						setattr(action[0], action[1], self[id])
					except:
						note(u'Error setting ' + unicode(description), 'error')
			self.settings_list = Listbox([(u'dummy',u'item')], lambda: modify(self.settings_list.current()))
			self.refresh_ui(self.__currentSettingsList(groups_requested))
			# save previous application state
			previous_body = app.body
			previous_menu = app.menu
			previous_exit_key_handler = app.exit_key_handler
			# show the settings editor
			app.body = self.settings_list
			app.menu = menu_items + [
				(u'Modify', lambda: modify(self.settings_list.current())),
				(u'Close', self.exit.signal),
			]
			self.settings_list.bind(EKeyEdit, lambda: modify(self.settings_list.current()))
			self.settings_list.bind(EKeyYes, app.menu[0][1])	# set call key to do first action in menu
			app.exit_key_handler = self.exit.signal
			# wait for a signal to exit the settings editor
			self.exit.wait()
			# sve any changes
			self.save()
			# exit the editor
			app.body = previous_body
			app.menu = previous_menu
			app.exit_key_handler = previous_exit_key_handler
			del(self.settings_list)	# destroy list UI to save memory
		retval = None
		if self.titlebar != None:
			retval = self.titlebar.run('settings', titlebar, show)
		else:
			retval = show()
		if callback != None:
			callback()
		return retval


from dir_iter import Directory_iter

class Filebrowser (Directory_iter):
	def __init__(self, initial_dir='\\', titlebar=Titlebar('filebrowser')):
		self.drive_list = drive_list()
		Directory_iter.__init__(self, self.drive_list)
		# set initial directory if one has been specified
		if initial_dir != '\\':
			if isdir(initial_dir):
				self.path = initial_dir
				self.at_root = 0
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
		
	def refresh_ui(self, current=None):
		"""refresh the current file list
		current sets the current selection"""
		dir_listing = self.list_repr()
		if current == None:
			current = self.listbox.current()
		if len(dir_listing) > 0:
			self.titlebar.temporary(self.path)
			self.listbox.set_list(dir_listing, current)
			ao_yield()
		else:
			note(u'Empty directory', 'info')
			self.pop()
			self.refresh_ui(current=0)
	
	def show_ui(self, allow_directory=0):
		"""show the file browser - returns the path selected
		allow_directory = 1 allows a directory to be selected"""
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
				if query(u'Delete ' + unicode(basename(path)) + u'?', 'query'):
					change_made = 0
					if isfile(path):
						try:
							remove(path)
							change_made = 1
						except:
							note(u'Error delecting file', 'error')
					elif isdir(path):
						if len(listdir(path)) == 0:
							try:
								rmdir(normpath(path))
								change_made = 1
							except:
								note(u'Error deleting directory', 'error')
						else:
							note(u'Not deleted: Directory is not empty', 'info')
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
	"""chetbox[at]gmail[dot]com - EasyEdit is Released under GPLv2 (See bundled COPYING.txt)"""
	
	titlebar = None
	config = None
	hasFocus = 0
	filebrowser = None
	text = None
	running = 0
	path = None
	
	def __newline_fix(self, text):
		"""Used to replace S60 UI newline characters with normal \n"""
		return text.replace(u'\u2029',u'\n')

	def __open_document(self, path, read_from_disk=1):
		"""Open a document by reading from disk, and showing "busy" status."""
		oldpath = self.path
		self.path = path
		error = 0
		if path != None:
			# add to recent list
			if normpath(path) in self.config[CONF_HISTORY]:
				self.config[CONF_HISTORY].remove(path)
			self.config[CONF_HISTORY] = ([normpath(path)] + self.config[CONF_HISTORY])[:self.config[CONF_HISTORY_SIZE]]
			self.config.save()
			# show filename in titlebar until a different file is opened
			if read_from_disk:
				self.titlebar._end()
				if path != None:
					self.titlebar._begin(0, 'document', unicode(basename(path)))
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
					self.__open_document(oldpath, read_from_disk=0)
					error = 1

	def run(self):
		"""Start EasyEdit"""
		def exitHandler():
			"""Stop EasyEdit"""
			self.running = 0
		focusLock = Ao_lock()
		externalFocusHandler = app.focus
		def focusHandler(f):
			if f and not(self.hasFocus):	# if we have just got focus
				self.hasFocus = 1
				focusLock.signal()
			if not(f) and self.hasFocus:	# if we just lost focus
				self.hasFocus = 0
			if externalFocusHandler:
				externalFocusHandler(f)
		app.focus = focusHandler
		def save_query():
			"""check if file needs saving and prompt user if necessary - returns user reponse"""
			save = 0
			save_required = 1
			current_text = self.text.get()
			if self.exists():
				# read file and compare to current
				f = open(self.path, 'r')
				saved_text = f.read()
				f.close()
				if saved_text == self.encode(current_text):
					save_required = 0
			elif len(current_text) == 0:
				save_required = 0
			if save_required:
				if DEBUG:
					print("Save required")
				save = popup_menu([u'Yes', u'No'], u'Save file?')
				if save != None:
					save = not(save)	# because 0 => 'yes' option, 1 => 'no' option
					if save == 1:
						f_save()
			return save
		def f_new(force=0):
			"""start a new, blank document"""
			if force or save_query() != None:
				self.text.clear()
				self.refresh()
				self.__open_document(None)
		def f_open():
			"""open an existing document"""
			# show file selector
			path = None
			if self.filebrowser == None:
				self.filebrowser = Filebrowser(self.config[CONF_LAST_DIR], self.titlebar)
			path = self.filebrowser.show_ui()
			# show "save?" dialog if necesary and open document
			if path != None:
				self.__save_last_dir(path)
				if save_query() != None:
					# open the document
					self.__open_document(path)
		def f_open_recent():
			"""select a file to open from the recent document list"""
			lock = Ao_lock()
			listbox = None
			def select():
				lock.signal()
				self.__open_document(self.config[CONF_HISTORY][listbox.current()])
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
			list = current_list()
			if len(list) > 0:
				# save previous application state
				previous_body = app.body
				previous_menu = app.menu
				previous_exit_key_handler = app.exit_key_handler
				listbox = Listbox(list, select)
				app.body = listbox
				app.menu = [
					(u'Open', select),
					(u'Remove from list', remove_recent),
				]
				app.exit_key_handler = lock.signal
				listbox.bind(EKeyBackspace, remove_recent)
				lock.wait()
				# exit the editor
				app.body = previous_body
				app.menu = previous_menu
				app.exit_key_handler = previous_exit_key_handler
			else:
				note(u'No recent documents', 'info')
		def f_save(force=0):
			"""save the current file - force argument skips exist check"""
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
				f_save_as()
		def f_save_as():
			"""save current file at a new location"""
			# show file selector
			path = None
			if self.filebrowser == None:
				self.filebrowser = Filebrowser(self.config[CONF_LAST_DIR], self.titlebar)
			path = self.filebrowser.show_ui(allow_directory=1)
			if path != None:
				# assume a directory has been selected -  suggest a filename in the current directory
				new_file_location = dirname(path)
				containing_dir = basename(path)
				# <hack reason="top-level paths (drives) need to have a \ appended because join will not add it">
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
					save_possible = 0
					if isfile(self.path):
						save_possible = query(u'Overwite file?', 'query')
					elif isdir(self.path):
						note(u'Not saved: A directory exists with that name', 'info')
					else:
						save_possible = 1
					if save_possible:
						f_save(force=1)	# force prevents another call to f_save_as
		def s_go_to_line():
			"""move cursor to beginning of specified line number"""
			text = self.__newline_fix(self.text.get())
			total_lines = text.count(u'\n') + 1
			line_no = query(u'Line number (1 - ' + unicode(total_lines) + ')', 'number', 1)
			if line_no != None:
				if line_no > 0 and line_no <= total_lines:
					# find the position in the text of the beginning of the line required
					last_newline = -1
					for line in range(line_no - 1):
						last_newline = text.index('\n', (last_newline + 1))
					self.text.set_pos(last_newline + 1)
				else:
					note(u'Invalid line number', 'error')
		def s_find():
			"""find a string in the document"""
			def find():
				self.config.save()
				cursor_position = self.text.get_pos()
				text = self.__newline_fix(self.text.get())
				search_text = self.config[CONF_FIND_TEXT]
				if self.config[CONF_FIND_CASE_SENSITIVE] == 'no':
					text = text.lower()
					search_text = search_text.lower()
				if self.config[CONF_FIND_DIRECTION] == 'next':
					cursor_position = text.find(search_text, cursor_position + 1)
				elif self.config[CONF_FIND_DIRECTION] == 'previous':
					cursor_position = text.rfind(search_text, 0, cursor_position - 1)
				else:	# search all
					cursor_position = text.find(search_text)
				if cursor_position != -1:
					self.text.set_pos(cursor_position)
					self.config.exit.signal()
				else:
					note(u'Search text not found', 'info')
			self.config.show_ui(groups_requested=[CONF_GROUP_FIND, CONF_GROUP_FIND_DIRECTION], titlebar=u'Find', menu_items=[(u'Search',find)])
		def s_replace():
			"""replace all matching strings in the document"""
			def replace():
				self.config.save()
				cursor_position = self.text.get_pos()
				current_text = self.text.get()
				find_text = self.config[CONF_FIND_TEXT]
				if self.config[CONF_FIND_CASE_SENSITIVE] == 'no':
					current_text = current_text.lower()
					find_text = find_text.lower() # makes everything lowercase!!
				self.titlebar.prepend('settings', BUSY_MESSAGE)
				new_text = current_text.replace(find_text, self.config[CONF_REPLACE_TEXT])
				self.text.set(new_text)
				note(unicode(current_text.count(find_text)) + " matches replaces", 'info')
				if cursor_position > len(new_text):
					cursor_position = len(new_text)
				self.text.set_pos(cursor_position)
				self.config.exit.signal()
				self.titlebar.refresh()
			self.config.show_ui(groups_requested=[CONF_GROUP_FIND, CONF_GROUP_REPLACE], titlebar=u'Replace', menu_items=[(u'Replace all', replace)])
		# read settings
		self.titlebar = Titlebar('document', u'EasyEdit')
		self.config = Settings(CONF_DB, CONFFILE, Titlebar('settings', u'EasyEdit'))
		self.hasFocus = 1
		# save current state
		old_title = app.title
		old_screen = app.screen
		old_orientation = app.orientation
		old_exit_key_handler = app.exit_key_handler
		old_body = app.body
		old_menu = app.menu
		old_focus_handler = app.focus
		# set up environment from settings
		app.screen = self.config[CONF_SCREEN]
		app.orientation = self.config[CONF_ORIENTATION]
		# create editor environment
		self.text = Text()
		self.path = None
		# set up menu
		app.menu=[
			(u'File', (
				(u'New', f_new),
				(u'Open', f_open),
				(u'Open recent', f_open_recent),
				(u'Save', f_save),
				(u'Save As', f_save_as),
			)),
			(u'Search', (
				(u'Find', s_find),
				(u'Replace', s_replace),
				(u'Go to line', s_go_to_line),
			)),
			(u'Settings', lambda : self.config.show_ui(groups_requested=[CONF_GROUP_MAIN], callback=self.refresh, menu_items=[(u'Return to editor', self.config.exit.signal)])),	# show all CONF_GROUP_MAIN settings
			(u'Help', (
		#		(u'README', self.h_readme),
				(u'About EasyEdit', lambda : query(unicode(self.__doc__), 'query')),
			)),
			(u'Exit', exitHandler),
			]
		# display editor
		app.body = self.text
		app.exit_key_handler = exitHandler
		# set the 'dial' key to save document
		self.text.bind(EKeyYes, f_save)
		# start editing a new document
		f_new()
		ao_yield()
		quit_app = None
		while quit_app == None:
			self.running = 1
			while self.running:
				# display line numbers if enabled
				if self.hasFocus:
					if self.config[CONF_LINE_NUMBERS] == 'yes':
						n = self.__newline_fix(self.text.get()[:self.text.get_pos()]).count(u'\n')
						self.titlebar.prepend('document', u'[' + unicode(n + 1) + '] ')
						ao_yield()
					ao_sleep(0.2)	# refresh rate of line numbers (seconds)
				else:
					# lock to stop busy waiting when app is not in focus
					focusLock.wait()
			# intent to close application has now been expressed
			quit_app = save_query()
		# application should now be closing
		# restore original state
		app.title = old_title
		app.screen = old_screen
		app.orientation = old_orientation
		app.exit_key_handler = old_exit_key_handler
		app.body = old_body
		app.menu = old_menu
		app.focus = old_focus_handler
		
	def encode(self, text):
		"""encode text accoridng to settings"""
		# ensure all new-lines are represented as '\n'
		encoded_text = self.__newline_fix(text)
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
	
	def __save_last_dir(self, path):
		"""save the location of the last viewed directory in self.config"""
		if isdir(path):
			self.config[CONF_LAST_DIR] = normpath(path)
		else:
			self.config[CONF_LAST_DIR] = dirname(normpath(path))
		self.config.save()



# run the editor!
if __name__ == '__main__':
	Editor().run()
