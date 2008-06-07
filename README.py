"""
EasyEdit README
---------------
   v. 1.44


Copyright Chetan Padia ( chetbox [at] gmail [dot] com )
Released under GPLv2 (See COPYING.txt)


This file is part of EasyEdit.

EasyEdit is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

EasyEdit is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


(Please email any bugs you may find to this email address, and if possible the offending file.)


Major Changes (since v. 1.3.1)
-------------


1. Cut/copy/paste

  (Note : The existing "Edit" menu no longer exists.)

  Hold down the [ABC] button (which often has a pencil icon on it) to get access to the clipboard.
  While holding the button down move the cursor up/down/left/right to select text.
  By continuing to hold the button and pressing "Copy" or "Paste" text can be copied to the clipboard or copied to the current position, respectively.
  Cutting can be achieved by selecting text, copying it, and then pressing the "C" button after releasing the [ABC] button.

  The advantages of this cut/copy/paste method is that the clipboard is global to all applications.
  Currently, text pasted into EasyEdit appears in green. This is a limitation of the Text() object provided by Python for S60.


2. Settings panel

  (Note : The exisitng "View" menu no longer exists.)

  Settings are now all in one place and include :
   - Encoding selection
   - Windows/Unix style newline selection
   - Case-sensitivity of searches (excludes Find + Replace)
   - Screen font selection
   - Changing the screen size
   - Choosing the maximum number of files to remember in "Open Recent"


3. Find and replace

  Under the "Options menu" select "Search" and then "Replace".
  Find and replace is *always* case sensitive.


4. This ReadMe.

  Pretty self-explanatory.


5. Quick file saving

  If you're like me and want to save your file every few seconds... just in case, there is a new feature just for you.
  Pressing the [Dial] button (the one with the green telephone symbol) is a shortcut to saving files and settings.


6. Ability to execute files

  In the "Open" and "Save" dialogs the menu includes an Execute file" option (shortcut [2]). This will open the selected file in application associated with it by the OS.
  e.g. You want to install a python script.
       Select "Options" > "File" > "Open" once you have saved the file with a .py extension, select it and press [2].
       The python installer dialog will appear.
  This will work with HTML documents, ROMs, mp3s, images, etc. Though I doubt you would edit the latter few with EasyEdit.


7. Line numbers

  The current line number is now displayed at the top of the screen.
  This can be turned off in the "Settings" menu.




"""