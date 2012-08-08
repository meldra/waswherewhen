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

* A database that supports "WITH" queries, eg, postgres 8.4

Brief, and possibly incomplete at this point:

* Install django as per your operating system's instructions
  (eg, for ubuntu/debian: `sudo apt-get install python-django`)
* Get the Libravatar python module
  (eg, `sudo pip install pyLibravatar` or `sudo apt-get instal python-libravatar`)
* Get the djutils module
  (`sudo pip install djutils`)
* Clone this repository into a directory somewhere
* Setup Mailman to output weekly archives with the file format like:
  `<yourmailmanlisturl>Week-of-Mon-20120716.txt`
* Set up your settings.py as per any other django site
* Add `'brain',` to the apps in the settings.py
* Add to the bottom of your settings.py:

 * Mailman baseurl Remember the trailing slash!
`MAILMAN_BASEURL = 'https://<your whereis mbox>`

 * Url to get a json response with directory info for alias mapping
`DIRECTORY_JSON = '<url to some json with names, email, phone, etc details).js'`

* To the bottom of your settings.py, add the <yourmailmanlisturl> portion
  of the above url format. Remember the trailing slash!
* If you don't want this in debug mode, make that change to settings.py
* `python manage.py runserver ip.addr.of.choice:port`



### WISHLIST FEATURES ###
* Aliases for different email addresses
* Reply catching/threading
* Search function

Novelty:
* Heatmap on calendar views

