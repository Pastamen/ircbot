import socket
import re
import urllib.request
import urllib.parse
import json
import time
import hmac
import base64
import random


class IRCBot:

    def chathandle(self, msg):
        # loosely decode into utf-8
        msg = msg.decode('utf-8', 'ignore')

        regexmatch = re.match(self.chatregex, msg)
        if not regexmatch:
            return

        sender          = regexmatch.group(1)
        sender_ident    = regexmatch.group(2)
        sender_hostname = regexmatch.group(3)
        receiver        = regexmatch.group(4)
        message         = regexmatch.group(5)

        if receiver.lower() == self.nickname.lower():
            self.privmsg(self.channel, sender + ' says: ' + message)

        elif receiver.lower() == self.channel.lower():
            self.chatlog_write(sender, message)
            if message[0] == ':':
                splitmessage = message[1:].split(' ', 1)
                if len(splitmessage[0]) < 2:
                    return
                command = splitmessage[0].lower()
                if len(splitmessage) > 1:
                    parameter = splitmessage[1]
                else:
                    parameter = ''

                # commands defined here
                if command == 'say':
                    self.privmsg(self.channel, parameter)

                elif command == 'me':
                    self.privmsg(self.channel, '/me ' + parameter)

                elif command == 'quote':
                    quote = json.loads(urllib.request.urlopen(self.quote_url).read().decode('utf-8'))
                    quotestr = '"' + quote[0] + '" --' + quote[1]
                    if len(quote) > 2:
                        quotestr += ', ' + quote[2]
                    self.privmsg(self.channel, quotestr)

                elif command == 'tweet':
                    if not self.twitter_enabled:
                        self.privmsg(self.channel, sender + ', tweeting is not configured!')
                    elif not len(parameter):
                        self.privmsg(self.channel, sender + ', you didn\'t provide a tweet.')
                    elif len(parameter) > 140:
                        self.privmsg(self.channel, sender + ', that tweet is too long.')
                    else:
                        random.seed()
                        base_url = 'https://api.twitter.com/1.1/statuses/update.json'
                        oauth_params = [
                            ('oauth_consumer_key',     '"' + self.twitter_key + '"'),
                            ('oauth_nonce',            '"' + ''.join([chr(random.randint(ord('a'),ord('z'))) for i in range(32)]) + '"'),
                            ('oauth_signature_method', '"HMAC_SHA1"'),
                            ('oauth_timestamp',        '"' + str(int(time.time())) + '"'),
                            ('oauth_token',            '"' + self.twitter_token + '"'),
                            ('oauth_version',          '"1.0"')
                        ]
                        params = [
                            ('status', urllib.parse.quote(parameter, safe=''))
                        ]
                        oauth_signature_msg = ('POST&' + urllib.parse.quote(base_url, safe='') + '&' + urllib.parse.quote('&'.join(['='.join(i) for i in sorted([(urllib.parse.quote(i[0], safe=''), urllib.parse.quote(i[1], safe='')) for i in (oauth_params + params)], key=lambda p: p[0])]), safe='')).encode('ascii')
                        oauth_signature_key = bytes(urllib.parse.quote(self.twitter_secret, safe='') + '&' + urllib.parse.quote(self.twitter_token_secret, safe=''), 'ascii')
                        oauth_signature = urllib.parse.quote(base64.b64encode(hmac.new(oauth_signature_key, oauth_signature_msg, 'SHA1').digest()).decode('ascii'), safe='')
                        req = urllib.request.Request(
                            base_url,
                            bytes('&'.join(['='.join(i) for i in params]), 'ascii'),
                            {'Authorization' :
                                'OAuth ' +
                                    ','.join(['='.join(i) for i in oauth_params])
                            }
                        )
                        self.privmsg(self.channel, sender + ', sending tweet now...')
                        try:
                            urllib.request.urlopen(req)
                        except BaseException as e:
                            self.privmsg(self.channel, sender + ', tweet failed: ' + str(e))
                            return
                        self.privmsg(self.channel, sender + ', tweet worked, apparently!')

                else:
                    self.privmsg(self.channel, 'Unknown fucking command, dumbass.')
            else:
                if message.lower() == 'i love cocks':
                    self.privmsg(self.channel, 'SO DO I HAHAHAHAHA wankers.')

                elif message.lower() == 'fucking die':
                    self.privmsg(self.channel, 'no.')

                else:
                    pass

    def chatlog_write(self, sender, message):
        if self.chatlog:
            t = time.localtime()
            date_now = (t.tm_mday, t.tm_mon, t.tm_year)
            if not self.current_date or date_now != self.current_date:
                self.current_date = date_now
                self.chatlog.write('\r\n\r\n' + time.strftime('%A %d %B %Y', t) + '\r\n')
                self.chatlog.write(self.server + ', ' + self.channel + '\r\n')
            self.chatlog.write('\r\n' + time.strftime('(%H:%M:%S) ', t) + sender + ': ' + message)

    def __init__(self, config_name):
        self.server = 'irc.esper.net'
        self.port   = 6667
        self.username = 'someidiotinnit'
        self.realname = 'Tom Kowalczyk'
        self.nickname = 'SomeIdiotInnit'
        self.password = 'somepasswordlel'
        self.channel = '#pastamen'
        self.quote_url = 'http://torin.org.uk/quotes/api/random/'
        self.twitter_key = ''
        self.twitter_token = ''
        self.twitter_secret = ''
        self.twitter_token_secret = ''
        self.logfile = None
        self.chatlog = None
        self.log_to_stdout = False

        self.current_date = None

        self.chatregex = re.compile(r':(.+)!(.+)@(.+) PRIVMSG (.+) :(.*)\r\n', re.IGNORECASE)

        for index, line in enumerate(open(config_name, 'r')):
            line = line.strip()
            if len(line) > 0:
                line = line.split('=', 1)
                if len(line) != 2:
                    raise RuntimeError(config_name + ', line ' + str(index) + ': invalid expression')
                param = line[0].lower()
                if param == 'server':
                    self.server = line[1]

                elif param == 'port':
                    try:
                        self.port = int(line[1])
                    except ValueError:
                        raise ValueError(config_name + ', line ' + str(index) + ': invalid port number')

                elif param == 'username':
                    self.username = line[1]

                elif param == 'realname':
                    self.realname = line[1]

                elif param == 'nickname':
                    self.nickname = line[1]

                elif param == 'password':
                    self.password = line[1]

                elif param == 'channel':
                    self.channel = line[1]

                elif param == 'quote_url':
                    self.quote_url = line[1]

                elif param == 'twitter_key':
                    self.twitter_key = line[1]

                elif param == 'twitter_token':
                    self.twitter_token = line[1]

                elif param == 'twitter_secret':
                    self.twitter_secret = line[1]

                elif param == 'twitter_token_secret':
                    self.twitter_token_secret = line[1]

                elif param == 'logfile':
                    self.logfile = open(line[1], 'ab', 0)

                elif param == 'chatlog':
                    self.chatlog = open(line[1], 'a', 1)

                elif param == 'log_to_stdout':
                    if line[1].lower() == 'true':
                        self.log_to_stdout = True
                    elif line[1].lower() == 'false':
                        self.log_to_stdout = False
                    else:
                        raise RuntimeError(config_name + ', line ' + str(index) + ': invalid bool value for log_to_stdout')
        
        if self.twitter_key != '' and self.twitter_token != '':
            self.twitter_enabled = True
        else:
            self.twitter_enabled = False

        self.setup_connection()

    def setup_connection(self):
        self.conn = socket.socket()
        self.conn.connect((self.server, self.port))
        self.send_irc_msg('USER', [self.username, ' . . :' + self.realname])
        self.send_irc_msg('NICK', [self.nickname])

        msg = b''
        while msg[:4].upper() != b'PING':
            msg = self.recv_irc_msg()
        self.send_irc_msg('PONG', [msg[5:].decode('ascii')])

        self.privmsg('NickServ', 'IDENTIFY' + ' ' + self.nickname + ' ' + self.password)
        self.send_irc_msg('JOIN', [self.channel])
        self.privmsg(self.channel, 'notice: i\'m a huge faggot')
        time.sleep(2)
        self.privmsg(self.channel, '(also die)')

    def send_irc_msg(self, command, parameters):
        message = command + ' ' + ' '.join(parameters) + '\r\n'
        if self.log_to_stdout:
            print('>>', message, end='')
        if self.logfile:
            self.logfile.write(b'>> ' + bytes(message, 'ascii'))
        self.conn.send(bytes(message, 'ascii'))

    def recv_irc_msg(self):
        buf = b''
        while buf[-2:] != b'\r\n':
            buf += self.conn.recv(1)
        if self.log_to_stdout:
            try:
                print(buf.decode('utf-8'), end='')
            except UnicodeDecodeError:
                print(buf, end='')
        if self.logfile:
            self.logfile.write(buf)

        # return as bytes because decoding can fuck up
        return buf

    def privmsg(self, nick, message):
        self.send_irc_msg('PRIVMSG', [nick, ':' + message])
        if nick.lower() == self.channel.lower():
            self.chatlog_write(self.nickname, message)

    # this expects bytes
    def parse_irc_msg(self, message):
        if message[:4].upper() == b'PING':
            self.send_irc_msg('PONG', [message[5:].strip().decode('ascii')])

        elif message[:5].upper() == b'ERROR':
            self.setup_connection()

        elif chr(message[0]) == ':':
            self.chathandle(message)

        else:
            pass
