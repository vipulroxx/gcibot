#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2012 Aviral Dasgupta <aviraldg@gmail.com>
# Copyright (C) 2013-15 Ignacio Rodríguez <ignacio@sugarlabs.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
import sys
import re
import requests
import datetime
import json
import random
import os
from bs4 import BeautifulSoup

META = [
    "I\'m a bot written by aviraldg who inserts metadata about GCI links!",
    "Original source at: http://ur1.ca/j368e current source (forked) http://ur1.ca/j368j",
    "If you want to kick gcibot from this channel, just kick, or ask for 'ignacio' for remove it"]

SOMETHING = {
    "hi": "Hi master.",
    "bye": "Good bye!",
    "i love you": "Sorry, I'm a bot. I haven't feelings.",
    "hello": "Hello master.",
    "ping": "pong",
    "you rock": "I know, lml.",
    "thanks": "you're welcome.",
    "thx": "you're welcome.",
    "help": "Paste a task link, and I will tell you everything about it",
    "shutup": "Nah."}

YEARS = {'2011': 7, '2012': 7, '2013': 16, '2014': 16}
MELANGE_LINK = "https://www.google-melange.com/gci/task/view/google/gci20{YEAR}/{TASKID}"
IGNORED = ['#haiku', '#copyleftgames']


class GCIBot(irc.IRCClient):
    nickname = 'gcibot'
    username = 'gcibot'
    password = 'irodriguez'

    def __init__(self):
        self.channels = []

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        for c in self.factory.channels:
            self.join(c)

    def joined(self, channel):
        self.channels.append(channel)

    def privmsg(self, user, channel, msg):
        try:
            isMaster = "!~IgnacioUy@unaffiliated/ignaciouy" in user
            user = user.split('!', 1)[0]
            isForMe = msg.startswith(
                self.nickname +
                ":") or msg.startswith(
                self.nickname +
                ",") or msg.startswith(
                self.nickname +
                " ")

            if "gcibot pull" in msg and isMaster:
                # FIXME: Its ugly.
                os.system("git pull && killall python && sh run.sh &")
                self.quit('Time for a break.')

            if "leave this channel " + self.nickname in msg and isMaster:
                self.msg(channel, "Yes master.")
                self.leave(channel)
                self.channels.remove(channel)
                return

            if "where are you " + self.nickname in msg and isMaster:
                txt = "I'm on: "
                for chan in self.channels:
                    txt += chan + ", "

                self.msg(channel, txt)
                return

            if isMaster and "join #" in msg:
                chan = msg[5:]
                self.join(chan)

            if "amsg" in msg and isMaster:
                msg = msg[5:]
                for channel in self.channels:
                    self.msg(channel, msg)
                return

            if isForMe and "ignore " in msg and isMaster:
                msg = msg[msg.find("ignore ") + 7:]
                IGNORED.append(msg)
                self.describe(channel, "is now ignoring: %s" % msg)
                return

            if isForMe and "about" in msg[msg.find(self.nickname):]:
                for line in META:
                    msg = "{user}, {META}".format(user=user, META=line)
                    self.msg(channel, msg)
                return

            for thing in SOMETHING:
                if isForMe and thing in msg[msg.find(self.nickname):]:
                    msg = "{user}, {msg}".format(
                        user=user,
                        msg=SOMETHING[thing])
                    self.msg(channel, msg)
                    return

            if isForMe and 'datetime' in msg:
                today = str(datetime.datetime.today())
                msg = "{user}, {date}".format(user=user, date=today)
                self.msg(channel, msg)
                return

            if isForMe and ('merry xmas' in msg or 'merry christmas' in msg):
                today = datetime.datetime.today()
                day = today.day
                month = today.month
                if day == 25 and month == 12:
                    msg = "{user}, merry christmas!".format(user=user)
                else:
                    msg = "{user}, are you serious? Christmas? pls..".format(
                        user=user)
                self.msg(channel, msg)
                return

            if isForMe and ('happy new year' in msg):
                today = datetime.datetime.today()
                day = today.day
                month = today.month
                if day == 1 and month == 11:
                    msg = "{user}, happy new year!".format(user=user)
                else:
                    msg = "{user}, are you serious? New year?? pls..".format(
                        user=user)
                self.msg(channel, msg)
                return

            ran = re.findall(
                'random.(sugarlabs|mifos|apertium|brlcad|sahana|copyleftgames|openmrs|wikimedia|kde|haiku|drupal|fossasia)',
                msg)
            if ran and isForMe:
                # Open the JSON file and choose random task.
                page_json_f = open("orgs/%s.json" % ran[0], "r")
                tasks = json.loads(page_json_f.read())['data']['']
                page_json_f.close()
                task = random.choice(tasks)
                link = "https://www.google-melange.com" + \
                    task['operations']['row']['link']
                msg = "{user}, random task in {org}: {link}".format(
                    user=user,
                    org=ran[0],
                    link=link)
                self.msg(channel, msg)

            if (channel or user) in IGNORED:
                return
            links = re.findall(
                ur'https{0,1}://(www\.google-melange\.com|google-melange\.appspot\.com)/gci/task/view/google/gci20([0-9]{2})/([0-9]+)',
                msg)

            for _ in links:
                link = MELANGE_LINK.format(YEAR=_[1], TASKID=_[2])
                YEAR = "20" + str(_[1])

                if YEAR not in YEARS or len(_[2]) != YEARS[YEAR]:
                    return

                r = requests.get(link)
                s = BeautifulSoup(r.text)
                A = {}
                try:
                    A['title'] = s.find('div', class_='flash-error').p.string
                    if 'is inactive' in A['title']:
                        self.describe(channel, "cant access to that task.")
                        return
                except:
                    A['title'] = s.find('span', class_='title').string
                A['status'] = s.find('span', class_='status').span.string
                A['mentor'] = s.find('span', class_='mentor').span.string
                A['org'] = s.find('span', class_='project').string
                A['remain'] = s.find(
                    'span',
                    class_='remaining').span.string
                for _ in A.keys():
                    # IRC and Unicode don't mix very well, it seems.
                    A[_] = unicode(A[_]).encode('utf-8')

                title = A['title']
                status = A['status']
                mentor = A['mentor']
                org = A['org']
                if A['status'] == "Claimed" or A[
                        'status'] == "NeedsReview":
                    status = A['status'] + ' (%s)' % A['remain']
                self.msg(
                    channel, '%s || %s || %s || %s' %
                    (org, title, status, mentor))
        except Exception as e:
            self.describe(
                channel,
                "ERROR: '%s'. Please contact my mantainer: ignacio@sugarlabs.org" %
                str(e))

    def alterCollidedNick(self, nickname):
        return '_' + nickname + '_'


class BotFactory(protocol.ClientFactory):

    def __init__(self, channels):
        self.channels = channels

    def buildProtocol(self, addr):
        p = GCIBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    f = BotFactory(sys.argv[1:])
    reactor.connectTCP("irc.freenode.net", 6667, f)
    print "Connected to server. Channels:"
    for channel in sys.argv[1:]:
        print channel
    reactor.run()
