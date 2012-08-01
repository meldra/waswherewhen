# WasWhereWhen is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Libravatar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with WasWhereWhen.  If not, see <http://www.gnu.org/licenses/>.
#
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import Template
from datetime import date, datetime, timedelta, time
from dateutil.relativedelta import MO
from dateutil.rrule import rrule,DAILY
import calendar
from calendar import HTMLCalendar
from itertools import groupby
from django.utils.html import conditional_escape as esc
import mailbox
import email.utils
import urllib2
from cStringIO import StringIO
from gzip import GzipFile
from libravatar import libravatar_url

now = datetime.now()
withyear = False

def parse_mbox(message):
    if message.is_multipart():
        for part in message.get_payload(): 
            parse_mbox(part)
    else:
        return message.get_payload(decode=True)

def mbox(date_obj, weekday):  

    day = datetime.combine(date_obj, time())

    if weekday != 0:
        rr=rrule(DAILY,byweekday=MO,dtstart=day-timedelta(day.weekday()))

        past_monday=rr.before(day,inc=False)
        last_monday = (past_monday.date())
        monday = 'Week-of-Mon-%s' % last_monday.strftime("%Y%m%d")
    else:
        monday = 'Week-of-Mon-%s' % date_obj.strftime("%Y%m%d")

    url = '%s%s.txt.gz' % (settings.MAILMAN_BASEURL, monday)

    try:
        response = urllib2.urlopen(url)
    except:
        return False

    tmpfile = '/tmp/%s.txt' % monday
    data = response.read()
    unzipped = GzipFile('', 'r', 0, StringIO(data)).read()
    tmp_file = open(tmpfile, 'w')
    tmp_file.write(unzipped)
    tmp_file.close()
    mbox = mailbox.mbox(tmpfile)
    messages = []

    for message in mbox:
        body = parse_mbox(message).replace('\n','<br />\n')
        subject = email.header.decode_header(message['subject'])
        subject = subject[0][0]
        subject = subject.replace('[Whereis] ', '')
        who = message['from'].split('(')
        who = who[0].strip()
        who = who.replace(' at ', '@')
        maildate = datetime(*email.utils.parsedate(message['date'])[:6])
        bodyexpl = body.split('--')

        if maildate.strftime('%b %d %Y') == date_obj.strftime('%b %d %Y'):
            messages.append({'Date': message['date'],'From': who, 'Subject': subject, 'Body': bodyexpl[0]})

    return messages

class WhereisCalendar(HTMLCalendar):

    def formatyear(self, theyear, width=3):
        January = 1
        v = []
        a = v.append
        width = max(width, 1)
        a('<table border="0" cellpadding="0" cellspacing="0" class="year">')
        a('\n')
        a('<tr><th><a href="/%s"><</a></th><th colspan="%d" class="year">%s</th><th><a href="/%s">></a></th></tr>' % (theyear-1, width-2, theyear, theyear+1))

        for i in range(January, January+12, width):
            months = range(i, min(i+width, 13))
            a('<tr>')
            for m in months:
                a('<td>')
                a(self.formatmonth(theyear, m, withyear))
                a('</td>')
            a('</tr>')

        a('</table>')

        return ''.join(v)

    def formatmonthname(self, theyear, themonth, withyear):
        if themonth == 1:
            nextmonth = '%s/%s' % (theyear, themonth+1)
            prevmonth = '%s/%s' % (theyear-1, 12)
        elif themonth == 12:
            nextmonth = '%s/%s' % (theyear+1, 1)
            prevmonth = '%s/%s' % (theyear, themonth-1)
	else:
            nextmonth = '%s/%s' % (theyear, themonth+1)
            prevmonth = '%s/%s' % (theyear, themonth-1)

        if withyear:
            s = '%s %s' % (calendar.month_name[themonth], theyear)
        else:
            s = '%s' % calendar.month_name[themonth]

        l = '<a class="nounder" href="/%s"><</a>' % prevmonth
        r = '<a class="nounder" href="/%s">></a>' % nextmonth

        return '<tr><th class="month">%s</th><th colspan="5" class="month"><a href="/%s/%s">%s</a> - <a href="/%s">%s</a></th><th class="month">%s</th></tr>' % (l, theyear, themonth, s, theyear, theyear, r)

    def formatmonth(self, theyear, themonth, w=0, l=0):
        v = []
        a = v.append
        a('<table border="0" cellpadding="0" cellspacing="0" class="month">')
        a('\n')
        a(self.formatmonthname(theyear, themonth, withyear=withyear))
        a('\n')
        a(self.formatweekheader())
        a('\n')

        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week, themonth, theyear))
            a('\n')

        a('</table>')
        a('\n')

        return ''.join(v)

    def formatweek(self, theweek, month, year):
        s = ''.join(self.formatday(d, wd, month, year) for (d, wd) in theweek)

        return '<tr>%s</tr>' % s

    def formatday(self, day, weekday, month, year):
        if day == now.day and month == now.month and year == now.year:
            today = 'today '
        else:
            today = ''

        if day == 0:
            return '<td class="noday">&nbsp;</td>'
        else:
            return '<td class="%s%s"><a href="/%s/%s/%s">%d</a></td>' % (today, self.cssclasses[weekday], year, month, day, day)

def singleday(year, month, day):
    d = date(year, month, day)
    dateformatted = d.strftime('%b %d %Y');
    dayname = d.weekday()
    mboxlist = mbox(d, dayname)

    if mboxlist == False:
        return '<table><tr><th><h1>This date does not appear to be in the mail archive. It either pre-dates it, or has not happened yet</th></tr></h1>'

    v = []
    a = v.append
    a('<table class="singleday">')
    a('<tr><th colspan="2">%s</th></tr>' % d)

    for mboxmail in mboxlist:
        avatar_url = libravatar_url(mboxmail['From'])
        a('<tr><td class="headers"><p class="subject">%s</p><p>%s</p><img src="%s"><p>%s</p></td><td class="what">%s</td></tr>' % (mboxmail['Subject'], mboxmail['From'], avatar_url, mboxmail['Date'], mboxmail['Body']))

    a('</table>')

    return '\n'.join(v)

def index(request, year=0, month=0, day=0):
    cal = WhereisCalendar(calendar.SUNDAY)
    day = int(day)
    month = int(month)
    year = int(year)
    days = False

    if month > 0 and year > 0:
        days = calendar.monthrange(year, month)
    if days != False and day > 0 and day <= days[1]:
        dayCal = singleday(year, month, day)
    elif month > 0 and month <= 12:
        monthCal = cal.formatmonth(year, month)
        nextmonth = month+1
        prevmonth = month-1
    elif month == 0 and year > 1:
        yearCal = cal.formatyear(year, 4)
        nextyear = year+1
        prevyear = year-1
    else:
        yearCal = cal.formatyear(now.year, 4)
        nextyear = now.year+1
        prevyear = now.year-1

    return render_to_response('brain/templates/index.html', locals())

