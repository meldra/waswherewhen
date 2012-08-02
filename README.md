WasWhereWhen - Whereis mailing list mbox formatter

    Copyright (C) 2012  Melissa Draper <melissa@catalyst.net.nz>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

### INSTALL INSTRUCTIONS ###

Brief, and possibly incomplete at this point:

* Install django as per your operating system's instructions
  (eg, for ubuntu/debian: `sudo apt-get install python-django`)
* Get the Libravatar python module
  (eg, `sudo pip install pyLibravatar` or `sudo apt-get instal python-libravatar`)
* Clone this repository into a directory somewhere
* Setup Mailman to output weekly archives with the file format like:
  `<yourmailmanlisturl>Week-of-Mon-20120716.txt`
* Set up your settings.py as per any other django site
* To the bottom of your settings.py, add the <yourmailmanlisturl> portion
  of the above url format. Remember the trailing slash!
* If you don't want this in debug mode, make that change to settings.py
* `python manage.py runserver ip.addr.of.choice:port`



### WISHLIST FEATURES ###
* Aliases for different email addresses, etc
* Detection of when someone mails for someone else
* Keyword detection to display icons (irc, cell, etc, become icons irc nick/number)
* Reply catching/threading
* Search function

Novelty:
* Heatmap on calendar views

