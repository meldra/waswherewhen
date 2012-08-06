# WasWhereWhen is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# WasWhereWhen is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with WasWhereWhen.  If not, see <http://www.gnu.org/licenses/>.
#
import calendar, mailbox, email.utils, urllib2, simplejson, re, djutils.decorators
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import Template
from django.utils.html import escape
from django.db import connection
from django.core import serializers
from brain.models import Person, Alias, Archive
from datetime import date, datetime, timedelta, time
from dateutil.relativedelta import MO
from dateutil.rrule import rrule,DAILY
from calendar import HTMLCalendar
from itertools import groupby
from django.utils.html import conditional_escape as esc
from cStringIO import StringIO
from gzip import GzipFile
from libravatar import libravatar_url

withyear = False
aliascachetimer = date.today()

@djutils.decorators.async
def load_data_async(year, month, day):
    global aliascachetimer
    try:
        aliascount = Alias.objects.count()
    except:
        raise Exception("The db models have not been sync'd yet. Please sync them first.")
    if settings.DIRECTORY_JSON and aliascachetimer < date.today() or settings.DIRECTORY_JSON and aliascount == 0:
        aliascachetimer = resyncaliases()
    syncmbox(year, month, day)

def monday(date_obj, weekday):
    day = datetime.combine(date_obj, time())

    if weekday != 0:
        rr=rrule(DAILY,byweekday=MO,dtstart=day-timedelta(day.weekday()))
        past_monday=rr.before(day,inc=False)
        last_monday = (past_monday.date())
        return last_monday
    else:
        return date_obj

def parse_mbox(message):
    if message.is_multipart():
        for part in message.get_payload(): 
            parse_mbox(part)
    else:
        body = message.get_payload(decode=True)
        return escape(body)

def mbox(date_obj, weekday, reply=True):

    mon = monday(date_obj, weekday)
    mon = 'Week-of-Mon-%s' % mon.strftime("%Y%m%d")

    url = '%s%s.txt.gz' % (settings.MAILMAN_BASEURL, mon)
    urltxt = '%s%s.txt' % (settings.MAILMAN_BASEURL, mon)

    try:
        response = urllib2.urlopen(urltxt)
    except:
        try:
            response = urllib2.urlopen(url)
        except:
            return False
    tmpfile = '/tmp/%s.txt' % mon
    data = response.read()

    try:
        unzipped = GzipFile('', 'r', 0, StringIO(data)).read()
    except:
        unzipped = data

    tmp_file = open(tmpfile, 'w')
    tmp_file.write(unzipped)
    tmp_file.close()
    mbox = mailbox.mbox(tmpfile)
    messages = []

    for message in mbox:
        body = parse_mbox(message).replace('\n','<br />\n')
        subject = email.header.decode_header(message['subject'])
        subject = subject[0][0]
        subject = escape(subject.replace('[Whereis] ', ''))
        who = message['from'].split('(')
        who = who[0].strip()
        who = who.replace(' at ', '@')
        maildate = datetime(*email.utils.parsedate(message['date'])[:6])
        bodyexpl = body.split('--')

        archive = Archive.objects.get_or_create(date = maildate, sender = who, subject = subject, body = bodyexpl[0])

        if reply == True:
            if maildate.strftime('%b %d %Y') == date_obj.strftime('%b %d %Y'):
                messages.append({'date': message['date'],'sender': who, 'subject': subject, 'body': bodyexpl[0]})

    if reply == True:
        return messages
    else:
        return True

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
        now = datetime.now()

        if day == now.day and month == now.month and year == now.year:
            today = 'today '
        else:
            today = ''

        if day == 0:
            return '<td class="noday">&nbsp;</td>'
        else:
            return '<td class="%s%s"><a href="/%s/%s/%s">%d</a></td>' % (today, self.cssclasses[weekday], year, month, day, day)

def gettags(email, body):

    irc = mobile = home = False

    if body.lower().find('irc') > 0:
        irc = True;

    if body.lower().find('mobile') > 0:
        mobile = True;

    if body.lower().find('cell') > 0:
        mobile = True;

    if body.lower().find('text') > 0:
        mobile = True;

    if body.lower().find('phone') > 0:
        mobile = True;

    if body.lower().find('home phone') > 0:
        home = True;

    if body.lower().find('landline') > 0:
        home = True;

    tags = []
    t = tags.append
    t('email: %s' % email)

    if irc:
        try:
            nick = Alias.objects.filter( person = email, type = 'irc_nick')
            t('irc: %s' % nick[0].alias)
        except:
            irc = False

    if mobile:
        try:
            mobile = Alias.objects.filter( person = email, type = 'mobile')
            t('mobile: %s' % mobile[0].alias)
        except:
            mobile = False

    if len(tags) == 0:
        return False

    return tags

def taghilight(body):

    words = ['irc', 'email', 'cell', 'mobile', 'text', 'phone', 'home phone', 'landline']

    for w in words:
        body = re.sub(
            re.escape(w),
            ur'<span class="hilight">\g<0></span>',
            body,
            flags=re.IGNORECASE)

    return body

def getothers(subject, sender):

    subject = ' %s ' % subject.lower()
    cursor = connection.cursor()
    cursor.execute('with list as '
                   '(select a.id, a.alias, '
                   '(select distinct count(*) '
                   'as cnt from brain_alias a2 where a2.alias = a.alias) '
                   'as occurs from brain_alias a) '
                   'select alias from list '
                   'where occurs = 1 order by length(alias);')
    aliaslist = cursor.fetchall()
    aliaslist = map(' '.join, aliaslist)

    others = []
    o = others.append
    for alias in aliaslist:
        if subject.find(alias) > 0:
            matchq = Alias.objects.filter( alias = alias )
            match = matchq[0].person_id
            if match != sender:
                o(match)

    return ' '.join(others)

def singleday(year, month, day):
    d = date(year, month, day)
    dateformatted = d.strftime('%b %d %Y');
    dayname = d.weekday()
    yesterday = d - timedelta(1)
    yesterday = yesterday.strftime("%Y/%m/%d")
    tomorrow = d + timedelta(1)
    nextday = tomorrow;
    tomorrow = tomorrow.strftime("%Y/%m/%d")
    lastweek = datetime.now() - timedelta(7)
    now = date.today()

    mboxquerycount = Archive.objects.filter(date__contains=d).count()

    if mboxquerycount < 1:
        mboxlist = mbox(d, dayname)
    else:
        mboxquery = Archive.objects.filter(date__contains=d)
        jsondata = serializers.serialize('json', mboxquery)
        rows = simplejson.loads(jsondata)
        mboxlist = []
        m = mboxlist.append

        for l in rows:
            m(l['fields'])

    v = []
    a = v.append
    a('<table class="singleday">')
    a('<tr><th colspan="2"><a class="nounder" href="/%s"><</a>&nbsp;%s&nbsp;<a class="nounder" href="/%s">></a></th></tr>' % (yesterday, d, tomorrow))

    if d > now:
        a('<tr><th><h1>This date has not happened yet</h1><p>Time machines do not exist yet!</p></th></tr>')
        mboxlist = []
    elif mboxlist == False:
        mboxlist = []
        a('<tr><th><h1>This date predates the archive</h1><p>Time machines do not exist yet!</p></th></tr>')
    elif len(mboxlist) < 1:
        a('<tr><th><h1>Either this is a weekend day, or nobody mailed whereis</h1></th></tr>')

    d = d.strftime("%A, %B %d, %Y")

    for mboxmail in mboxlist:
        avatar_url = libravatar_url(email = mboxmail['sender'], size = 150)

        if settings.DIRECTORY_JSON:

            try:
                tagstring = gettags(mboxmail['sender'], mboxmail['body'])
                tagstring = ' | '.join(tagstring)
            except:
                tagstring = ''

            try:
                others = getothers(mboxmail['subject'], mboxmail['sender'])
            except:
                others = ''
        else:
            tagstring = others = ''

        if len(others) > 0:
            others = 'Possible mentions:<br/>%s' % others

        a('<tr><td class="headers"><p class="subject">%s</p><img src="%s"><p class="hilight">%s</p><p>%s</p></td><td class="what">%s<br/><br/>%s</td></tr>' % (mboxmail['subject'], avatar_url, others, mboxmail['date'], taghilight(mboxmail['body']), tagstring))

    a('</table>')

    return '\n'.join(v)

def resyncaliases():

    try:
        response = urllib2.urlopen(settings.DIRECTORY_JSON)
    except:
        response = False

    if response != False:
        json = simplejson.load(response)

    for j in json:
        person = Person.objects.get_or_create(individual = j['email'])

        if j['first_name']:
            try:
                alias = Alias.objects.get_or_create(person_id = j['email'], alias = j['first_name'].lower(), type = 'first_name')
            except:
                alias = Alias.objects.get(person = j['email'], type = 'first_name')
                alias.alias = j['first_name'].lower()
                alias.save()

        if j['surname']:
            surname_initial = '%s%s' % (j['first_name'], j['surname'][0:1])
            surname_initial_space = '%s %s' % (j['first_name'], j['surname'][0:1])

            try:
                alias = Alias.objects.get_or_create(person_id = j['email'], alias = surname_initial.lower(), type = 'surname')
            except:
                alias = Alias.objects.get(person = j['email'], type = 'surname')
                alias.alias = surname_initial.lower()
                alias.save()

            try:
                alias = Alias.objects.get_or_create(person_id = j['email'], alias = surname_initial_space.lower(), type = 'surnamesp')
            except:
                alias = Alias.objects.get(person = j['email'], type = 'surnamesp')
                alias.alias = surname_initial_space.lower()
                alias.save()

        if j['irc_nick']:
            try:
                alias = Alias.objects.get_or_create(person_id = j['email'], alias = j['irc_nick'], type = 'irc_nick')
            except:
                alias = Alias.objects.get(person = j['email'], type = 'first_name')
                alias.alias = j['irc_nick']
                alias.save()

        if j['mobile']:
            try:
                alias = Alias.objects.get_or_create(person_id = j['email'], alias = j['mobile'], type = 'mobile')
            except:
                alias = Alias.objects.get(person = j['email'], type = 'first_name')
                alias.alias = j['mobile']
                alias.save()

        if j['home']:
            try:
                alias = Alias.objects.get_or_create(person_id = j['email'], alias = j['home'], type = 'home')
            except:
                alias = Alias.objects.get(person = j['email'], type = 'first_name')
                alias.alias = j['home']
                alias.save()

    return date.today()

def syncmbox(year, month, day):

    d = date(year, month, day)
    dayname = d.weekday()

    while True:
        syncmbox = mbox(d, dayname, False)
        d = d - timedelta(7)
        if syncmbox == False:
            break

    return True

def index(request, year=0, month=0, day=0):
    now = datetime.now()

    cal = WhereisCalendar(calendar.SUNDAY)
    day = int(day)
    month = int(month)
    year = int(year)
    days = False

    try:
        load_data_async(year, month, day)
    except:
        raise

    if month > 0 and month <= 12 and year > 0:
        days = calendar.monthrange(year, month)

    if days and day > 0 and day <= days[1]:
        dayCal = singleday(year, month, day)
    elif month > 0 and month <=12:
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

