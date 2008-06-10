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


import appuifw
import dir_iter
import os
import os.path
import encodings
from sys import getdefaultencoding
from e32 import Ao_lock, drive_list, ao_yield, ao_sleep
from key_codes import EKeyLeftArrow, EKeyRightArrow, EKeyBackspace, EKey1, EKey2, EKeyEdit, EKeyYes

VERSION=(1, 45, 0)
CONFFILE='C:\\SYSTEM\\Data\\EasyEdit.conf'
DEFAULTENCODING=getdefaultencoding()


class editor:

 """EasyEdit : A Text Editor for s60
(chetbox[at]gmail[dot]com)"""

 def __init__(self):
  self.last_find=u''
  self.settings=Settings()
  self.settings.load(CONFFILE)
  self.file_ops=File_ops(self.settings.config['last_dir'][0])

 def run(self):
  """start application"""
  appuifw.app.title=u'EasyEdit'
  appuifw.app.screen=self.settings.config['screen']

  # create blank page
  self.text=appuifw.Text()
  self.path=''
  self.f_new()

  # set up menu
  appuifw.app.menu=[\
   (u'File', (\
    (u'New', self.f_new),\
    (u'Open', self.f_open),\
    (u'Open recent', self.f_recent),\
    (u'Save', self.f_save),\
    (u'Save As', self.f_save_as),\
   )),\
   (u'Search', (\
    (u'Find', self.s_ffind),\
    (u'Find next', self.s_find),\
    (u'Find previous', self.s_rfind),\
    (u'Replace', self.s_replace),\
    (u'Go to line', self.s_line),\
   )),\
   (u'Settings', self._editsettings),\
   (u'Help', (\
    (u'Open README', self.h_readme),\
    (u'About EasyEdit', self.h_about),\
   )),\
   (u'Exit', self.exit),\
  ]

  # display editor
  self.lock = False
  self._focus = True
  appuifw.app.body=self.text
  appuifw.app.focus = self._changefocus
  self.text.bind(EKeyYes, self.f_save)
  appuifw.app.exit_key_handler=self.exit
  self.lock = True
  #Ao_lock().wait()
  self._count()

 def _changefocus(self, focus):
   self._focus = focus

 def _count(self):
  while self.lock:
   if self._focus and self.settings.config['linenos'][0] == 'yes':
    n = self.text.get()[0:self.text.get_pos()].replace(u'\u2029',u'\n').count(u'\n')
    statusbar.refresh(prefix='[' + str(n+1) + ']')
   ao_sleep(0.1)

 def _refresh(self):
  "update the screen font"
  statusbar.busy()
  cur_pos=self.text.get_pos()
  self.text.font=unicode(self.settings.config['font'][0])
  self.text.color=\
   (\
    self.settings.config['font_colour'][0],\
    self.settings.config['font_colour'][1],\
    self.settings.config['font_colour'][2]\
   )
  self.text.set(self.text.get())
  self.text.set_pos(cur_pos)
  statusbar.signal()

 def _editsettings(self):
  "show the settings editor"
  self.settings.edit(callback=self._refresh)

 def f_new(self):
  """create a blank document"""
  selection=2
  if (self.text.len() > 0) or os.path.isfile(self.path):
   selection=appuifw.popup_menu([\
     u'Yes',\
     u'No',\
    ],\
     u'Save document?'\
   )
  if (selection == 0):
   self.f_save()
  if (selection != None):
   self.text.style=False
   self.text.set(u'')
   self._refresh()
   self.path=''
   statusbar.remove()

 def f_open(self, path=None, save_path=True):
  """open an existing document"""
  if path == None:
   self.file_ops.open(self.f_open)
  else:
   selection=2
   if os.path.isfile(self.path) or (self.text.len() > 0):
    selection=appuifw.popup_menu\
     ([\
       u'Yes',\
       u'No',\
      ],\
      u'Save document?'\
     )
   if (selection == 0):
    self.f_save()
   if (selection != None):
    statusbar.busy()
    try:
     f=open(path,'r')
     self.text.style=False
     self.text.set(unicode(f.read().decode(self.settings.config['encoding'][0])))
     self.text.set_pos(0)
     f.close()
     self.path=path
     statusbar.remove()
     statusbar.add(os.path.basename(self.path))
     if save_path:
      self.settings.config['last_dir'][0]=os.path.dirname(self.path)
     self._addrecent(self.path)
    except:
     appuifw.note(u'Error opening file', 'error')
    statusbar.signal()

 def f_recent(self):
  """open a recently opeened document"""
  recent=[]
  for path in self.settings.config['history']:
   recent.append((unicode(os.path.basename(path)),unicode(os.path.dirname(path))))
  try:
   self.recent_list=appuifw.Listbox(recent, self._f_recent_select)
   body_previous=appuifw.app.body
   menu_previous=appuifw.app.menu
   exit_previous=appuifw.app.exit_key_handler
   appuifw.app.body=self.recent_list
   appuifw.app.menu=\
    [\
     (u'Select', self._f_recent_select),\
     (u'Cancel', self._f_recent_exit)\
    ]
   statusbar.add('Select document...')
   appuifw.app.exit_key_handler=self._f_recent_exit
   self.recent_lock=Ao_lock()
   self.recent_lock.wait()
   appuifw.app.exit_key_handler=exit_previous
   appuifw.app.body=body_previous
   appuifw.app.menu=menu_previous
  except:
   appuifw.note(u'No recent documents', 'info')

 def _addrecent(self, path):
  """add a document to the list of recent documents"""
  if path in self.settings.config['history']:
   self.settings.config['history'].remove(path)
  self.settings.config['history'].insert(0, path)
  if len(self.settings.config['history']) > self.settings.config['history_max']:
   temp=self.settings.config['history'].pop()
  self.settings._saveconfig()

 def _f_recent_select(self, path=None):
  """select a document from the recent documents"""
  statusbar.busy()
  self._f_recent_exit()
  self.f_open(self.settings.config['history'][self.recent_list.current()], False)
  statusbar.signal()

 def _f_recent_exit(self):
  """close the recent documents dialog"""
  statusbar.remove()
  self.recent_lock.signal()

 def f_save(self):
  """save the current file"""
  if not(os.path.isfile(self.path)):
   self.f_save_as()
  else:
   statusbar.busy()
   try:
    text = self.text.get().replace(u'\u2029', u'\n').replace(u'\r\n', u'\n')
    if self.settings.config['newline'][0] == 'windows':
     text = text.replace(u'\n', u'\r\n').encode(self.settings.config['encoding'][0])
    else:
     text = text.encode(self.settings.config['encoding'][0])
    f=open(str(self.path),'w')
    f.write(text)
    f.close()
    self._addrecent(self.path)
    appuifw.note(u'File saved.','conf')
   except:
    appuifw.note(u'Error saving file.','error')
   statusbar.update(os.path.basename(self.path))
   statusbar.signal()

 def f_save_as(self, path=None):
  """save the current file with a new path"""
  if path == None:
   self.file_ops.open(self.f_save_as, True)
  else:
   temp=self.path[:]
   self.path=path
   if (path == None):
    self.path=temp
   elif os.path.isfile(self.path):
    if appuifw.query(u'Overwrite '+unicode(self.path)+' ?','query'):
     self.f_save()
   else:
    statusbar.busy()
    try:
     f=open(str(self.path), 'w')
     f.close()
     self.f_save()
     self.settings.config['last_dir'][0]=os.path.dirname(self.path)
     self.settings._saveconfig()
     statusbar.remove()
     statusbar.add(os.path.basename(path))
    except:
     appuifw.note(u'Invalid path: '+unicode(self.path),'error')
     self.path=temp
    statusbar.signal()

 def s_find(self, reverse=False, beginning=False):
  """find text within a document"""
  statusbar.add('Find text...')
  string = appuifw.query(u'Find text:', 'text', unicode(self.last_find))
  statusbar.remove()
  saved_string = string[:]
  if (string != None):
   statusbar.busy()
   try:
    text = self.text.get()
    if self.settings.config['casesensitive'][0] == 'no':
     text = text.lower()
     string = string.lower()
    if beginning:
     if reverse:
      cur_pos=text.rindex(string)
     else:
      cur_pos=text.index(string)
    else:
     if reverse:
      cur_pos=text.rindex(string, 0, (self.text.get_pos() -1))
     else:
      cur_pos=text.index(string, (self.text.get_pos() +1))
    self.text.set_pos(cur_pos)
   except:
    appuifw.note(u'Search string not found.', 'info')
   self.last_find = saved_string
   statusbar.signal()

 def s_ffind(self):
  """find text within a document"""
  self.s_find(beginning=True)

 def s_rfind(self):
  """find text within a document"""
  self.s_find(reverse=True)

 def s_replace(self):
  """find and replace all instances of a given string"""
  replace=appuifw.multi_query(u'Replace :', u'with : ')
  if replace != None:
   statusbar.busy()
   text=self.text.get()
   cur_pos=self.text.get_pos()
   self.text.set(text.replace(replace[0],replace[1]))
   self.text.set_pos(cur_pos + text[0:cur_pos].count(replace[0])*(len(replace[1])-len(replace[0])))
   statusbar.signal()
   appuifw.note(unicode(text.count(replace[0])) + ' instances replaced')

 def s_line(self):
  """move the cursor to a particular line no."""
  statusbar.add('Find line...')
  line=appuifw.query(u'Line number:', 'number', 1)
  statusbar.remove()
  text=self.text.get().replace(u'\u2029',u'\n')
  lines=text.count(u'\n')
  if (line == None):
   pass
  elif (line <= lines):
   statusbar.busy()
   last=-1
   for x in range(line-1):
    last=text.index('\n',(last +1))
   self.text.set_pos(last +1)
   statusbar.signal()
  else:
   appuifw.note(u'Line does not exist!', 'info')

 def h_readme(self):
  self.f_new()
  if appuifw.query(u'Open README?', 'query'):
   try:
    import README
    self.text.set(unicode(README.__doc__))
    self.text.set_pos(1)
   except:
    appuifw.note(u'README not found', 'error')

 def h_about(self):
  """display info about application"""
  null = appuifw.query(unicode(self.__doc__),'query')

 def exit(self):
  """exit application"""
  if ((self.text.len() > 0) or (os.path.isfile(self.path))):
   selection=appuifw.popup_menu([\
    u'Yes',\
    u'No',\
   ],\
    u'Save document?'
   )
   if (selection == 0):
    self.f_save()
    if os.path.isfile(self.path):
     self.lock = False
   if (selection == 1):
    self.lock = False
  else:
   self.lock = False


class File_ops(object):
 """this class create a file browsing interface for saving/opening files.
 it also provides basic useful file operations.
 """
 def __init__(self, initial_dir='\\'):
  """setup the file browser"""
  self.menu =\
   [\
    (u'[-] Select', self._select),\
    (u'<- Up', self._ascend),\
    (u'-> Enter directory', self._descend),\
    (u'[1] New directory', self._mkdir),\
    (u'[2] Execute file', self._run),\
    (u'[ABC] Rename', self._rename),\
    (u'[C] Delete', self._delete),\
    (u'Cancel', self._exit),\
   ]
  self.dir_iter=dir_iter.Directory_iter(drive_list())
  if (
   (os.path.isdir(initial_dir)) and
   (initial_dir != '\\')
  ):
   self.dir_iter.path=initial_dir
   self.dir_iter.at_root=0
  self.browse=appuifw.Listbox(self.dir_iter.list_repr(), self._select)
  self.lock = Ao_lock()

 def _state_save(self):
  """save the application state"""
  self.body_previous = appuifw.app.body
  self.menu_previous = appuifw.app.menu
  self.exit_previous = appuifw.app.exit_key_handler

 def _state_restore(self):
  """restore the application state"""
  appuifw.app.body = self.body_previous
  appuifw.app.menu = self.menu_previous
  appuifw.app.exit_key_handler = self.exit_previous

 def open(self, callback=None, new_path=False):
  """open/save a file
  'new_path'=True means that a path that does not exist may be returned
  """
  statusbar.add(self.dir_iter.path)
  self._state_save()
  self.new_path = new_path
  self.callback = callback
  self._update()

  # set up UI
  appuifw.app.body = self.browse
  appuifw.app.menu = self.menu
  appuifw.app.exit_key_handler = self._exit

  # key shortcuts
  self.browse.bind(EKeyRightArrow, self._descend)
  self.browse.bind(EKeyLeftArrow, self._ascend)
  self.browse.bind(EKeyBackspace, self._delete)
  self.browse.bind(EKeyEdit, self._rename)
  self.browse.bind(EKey1, self._mkdir)
  self.browse.bind(EKey2, self._run)

  self.lock.wait()

 def _run(self):
  """show the file browser"""
  appuifw.Content_handler().open_standalone(self.dir_iter.entry(self.browse.current()))

 def _descend(self):
  """enter a directory"""
  statusbar.busy()
  selection = self.browse.current()
  if self.dir_iter.at_root:
   self.dir_iter.add(selection)
   self._update()
  elif os.path.isdir(self.dir_iter.entry(selection)):
   self.dir_iter.add(selection)
   self._update()
  statusbar.signal()

 def _update(self):
  """refresh the directory listing"""
  statusbar.busy()
  if len(self.dir_iter.list_repr()) > 0:
   self.browse.set_list(self.dir_iter.list_repr())
   statusbar.update(self.dir_iter.path)
  else:
   self.dir_iter.pop()
   appuifw.note(u'Empty directory', 'info')
  statusbar.signal()

 def _select(self):
  """what to do if an item is selected (i.e. descend directory or open file)"""
  selection = self.browse.current()
  if self.dir_iter.at_root:
   entry = str(self.dir_iter.drives[selection][0])
  else:
   entry = self.dir_iter.entry(selection)
  if os.path.isfile(entry):
   self._exit(entry)
  elif (self.new_path and os.path.isdir(entry)):
   appuifw.note(unicode(entry) + u' selected')
   filename = appuifw.query(u'Filename', 'text')
   if filename != None:
    self._exit(entry + '\\' + str(filename))
    self.dir_iter.add(selection)
  else:
   self._descend()

 def _delete(self):
  """delete selected file/empty folder"""
  path=self.dir_iter.entry(self.browse.current())
  if appuifw.query(u'Delete ' + unicode(os.path.basename(path)), 'query'):
   try:
    if os.path.isfile(path):
     os.remove(path)
     appuifw.note(u'File deleted', 'info')
    elif os.path.isdir(path):
     os.rmdir(path)
     appuifw.note(u'Directory deleted', 'info')
   except:
    appuifw.note(u'Unable to delete!', 'error')
   self._update()

 def _rename(self):
  """rename a file/folder"""
  path=self.dir_iter.entry(self.browse.current())
  filename=unicode(os.path.basename(path))
  if appuifw.query(u'Rename ' + filename + ' ?', 'query'):
   newname=appuifw.query(u'Rename ' + filename, 'text', filename)
   if newname != None:
    try:
     os.rename(path, os.path.dirname(path) + str(newname))
     appuifw.note(u'File renamed', 'info')
    except:
     appuifw.note(u'Error renaming file!', 'error')
    self._update()

 def _mkdir(self):
  """create a new directory"""
  path=self.dir_iter.path
  if appuifw.query(u'Create directory?', 'query'):
   newname=appuifw.query(u'Directory name:', 'text', u'new_directory')
   if newname != None:
    try:
     os.mkdir(path + str(newname))
     appuifw.note(u'Directory \"' + newname + '\" created', 'info')
    except:
     appuifw.note(u'Error creating directory!', 'error')
    self._update()

 def _ascend(self):
  """go up a directory"""
  statusbar.busy()
  self.dir_iter.pop()
  self._update()
  statusbar.signal()

 def _exit(self, path=None):
  """close the file browser"""
  self._state_restore()
  statusbar.remove()
  self.lock.signal()
  if path != None:
   statusbar.busy()
   self.callback(path)
   statusbar.signal()


class Settings(object):

 def __init__(self, initial_dir='\\'):
  """setup the settings dialog"""
  self.menu =\
   [\
    (u'Modify', self._modify),\
    (u'Close', self._close),\
   ]
  self.lock = Ao_lock()

 def load(self, conf):
  """load all settings"""
  self.conffile=conf
  if os.path.exists(self.conffile):
   f = open(self.conffile, 'r')
   c = f.read()
   f.close()
   self.config=eval(c)
  else:
   self._newconfig()
  try:
   if not(self.config['version'][0] == VERSION[0] and self.config['version'][1] == VERSION[1]):
    self._newconfig()
  except:
   self._newconfig()
  self._set_items()
  self.listbox=appuifw.Listbox(self.items, self._modify)

 def _newconfig(self):
  appuifw.note(u'New version detected, creating new config.', 'info')
  self.config=\
   {\
    'version':VERSION,\
    'screen':appuifw.app.screen,\
    'encoding':[DEFAULTENCODING],\
    'font':[Text().font[0]],\
    'font_colour':(0,0,0),\
    'history':[],\
    'history_max':5,\
    'last_dir':['\\'],\
    'newline':['unix'],\
    'linenos':['yes'],\
    'casesensitive':['no']\
   }
  self._saveconfig()

 def _state_save(self):
  """save the application state"""
  self.body_previous = appuifw.app.body
  self.menu_previous = appuifw.app.menu
  self.exit_previous = appuifw.app.exit_key_handler

 def _state_restore(self):
  """restore the application state"""
  appuifw.app.body = self.body_previous
  appuifw.app.menu = self.menu_previous
  appuifw.app.exit_key_handler = self.exit_previous

 def edit(self, callback=None):
  """show the settings editor"""
  self._state_save()
  statusbar.add('EasyEdit settings')
  self.callback = callback
  self._update()
  self.oldconfig=self.config
  appuifw.app.body = self.listbox
  appuifw.app.menu = self.menu
  appuifw.app.exit_key_handler = self._close
  self.listbox.bind(EKeyRightArrow, self._modify)
  self.listbox.bind(EKeyEdit, self._modify)
  self.listbox.bind(EKeyYes, self._close)
  self.lock.wait()

 def _set_items(self):
  """refresh stored list of settings"""
  self.items=\
    [\
     (u'File encoding', unicode(self.config['encoding'][0])),\
     (u'New-lines', unicode(self.config['newline'][0])),
     (u'Case-sensitive find', unicode(self.config['casesensitive'][0])),
     (u'Screen font', unicode(self.config['font'][0])),\
     (u'Display line number', unicode(self.config['linenos'][0])),\
     (u'Screen size', unicode(self.config['screen'])),\
     (u'Max history size', unicode(self.config['history_max'])),
    ]

 def _update(self):
  """refresh displayed list of settings"""
  statusbar.busy()
  self._set_items()
  self.listbox.set_list(self.items)
  statusbar.signal()

 def _modify(self):
  """edit a setting"""
  if self.listbox.current() == 0:
   self.encoding()
  elif self.listbox.current() == 1:
   self.newline()
  elif self.listbox.current() == 2:
   self.casesensitive()
  elif self.listbox.current() == 3:
   self.font()
  elif self.listbox.current() == 4:
   self.linenos()
  elif self.listbox.current() == 5:
   self.screen()
  elif self.listbox.current() == 6:
   self.history_max()
  self._update()
  self._saveconfig()

 def _close(self):
  """close the settings dialog"""
  self._state_restore()
  statusbar.remove()
  self.lock.signal()

 def _saveconfig(self):
  """save the configuration file"""
  try:
   f = open(self.conffile, 'w')
   f.write(repr(self.config))
   f.close()
  except:
   appuifw.note(u'Error saving configuration', 'error')

 def history_max(self):
  """set the maximum history size"""
  newsize = appuifw.query(u'Max history size:', 'number', self.config['history_max'])
  if newsize != None:
   self.config['history_max'] = str(newsize)

 def casesensitive(self):
  selection = appuifw.popup_menu([u'Yes', u'No'], u'Case-sensitive find:')
  if selection == 0:
   self.config['casesensitive'][0] = 'yes'
  if selection == 1:
   self.config['casesensitive'][0] = 'no'

 def linenos(self):
  selection = appuifw.popup_menu([u'Yes', u'No'], u'Line numbers:')
  if selection == 0:
   self.config['linenos'][0] = 'yes'
  if selection == 1:
   self.config['linenos'][0] = 'no'
   statusbar.refresh()

 def newline(self):
  newstyle = appuifw.popup_menu([u'Unix style', u'Windows style'], u'New lines:')
  if newstyle != None:
   if newstyle == 0:
    self.config['newline'][0] = 'unix'
   if newstyle == 1:
    self.config['newline'][0] = 'windows'

 def screen(self):
  """change the screen size"""
  current_screen=self.config['screen']
  statusbar.add('Select screen size...')
  self.config['screen']=appuifw.popup_menu([\
   u'Normal',\
   u'Large',\
   u'Fullscreen',\
  ], u'Screen size:')
  statusbar.remove()
  if (self.config['screen'] == 0):
   appuifw.app.screen='normal'
   self.config['screen'] = 'normal'
  elif (self.config['screen'] == 1):
   appuifw.app.screen='large'
   self.config['screen'] = 'large'
  elif (self.config['screen'] == 2):
   appuifw.app.screen='full'
   self.config['screen'] = 'full'
  else:
   self.config['screen']=current_screen

 def font(self):
  """change the display font"""
  temp=self.config['font'][0]
  fonts=appuifw.available_fonts()
  fonts.sort()
  statusbar.add('Select font...')
  self.config['font'][0]=appuifw.selection_list(choices=fonts,search_field=1)
  statusbar.remove()
  if self.config['font'][0] != None:
   self.config['font'][0] = str(fonts[self.config['font'][0]])
  if (self.config['font'][0] != None):
   self.callback()
  else:
   self.config['font'][0]=temp

 def encoding(self):
  """set the file encoding"""
  codecs=[]
  for enc in encodings.aliases.aliases:
   uni_enc=unicode(encodings.aliases.aliases[enc])
   if not(uni_enc in codecs):
    codecs.append(uni_enc)
  codecs.sort()
  statusbar.add('Select encoding...')
  selection=appuifw.selection_list(choices=codecs, search_field=1)
  statusbar.remove()
  if selection != None:
   statusbar.busy()
   self.config['encoding'][0]=str(codecs[selection])
   statusbar.signal()


class StatusBar:
 """a class to nicely manage the application titlebar
 and use it as a statusbar
 """

 def __init__(self, initial=appuifw.app.title):
  """setup statusbar variables"""
  self._stack = [unicode(initial)]
  appuifw.app.title = self._stack[0]
  self._busy = 0

 def refresh(self, prefix='', suffix=''):
  """refresh the titlebar if not 'busy'"""
  if self._busy < 1:
   title = unicode(prefix) + self._stack[-1] + unicode(suffix)
  else:
   title = u'   ...busy...'
  appuifw.app.title = title
  ao_yield()

 def update(self, text):
  """change the current titlebar text"""
  if len(self._stack) > 1:
   self._stack[-1] = (unicode(text))
   self.refresh()
  else:
   self.add(text)

 def add(self, text):
  """add a new item to the statusbar"""
  self._stack.append(unicode(text))
  self.refresh()

 def remove(self):
  """return to the previous item in the statusbar"""
  if len(self._stack) > 1:
   temp = self._stack.pop()
  self.refresh()

 def busy(self):
  """set statusbar to 'busy'"""
  self._busy += 1
  self.refresh()

 def signal(self):
  """signal end of 'busy' state"""
  if self._busy > 0:
   self._busy -= 1
  self.refresh()


# create a statusbar instance
statusbar = StatusBar('EasyEdit')

# run the editor!
if __name__ == '__main__':
 editor().run()

