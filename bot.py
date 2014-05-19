import socket
import re
import urllib.request
import urllib.parse
import json
import time
import hmac
import hashlib
import base64
import random


class IRCBot:

    # takes bytes
    def parse_irc_msg(self, msg):

        message = msg.decode(errors='ignore').strip()
        match = re.match(self.msgregex, message) 

        if not match:
            return

        groups = match.groups()

        prefix   = groups[0]
        cmd      = groups[1].upper().strip()
        params   = groups[2]
        trailing = groups[3]

        if cmd == 'PING':
            self.send_irc_msg(b'PONG', [msg[5:].strip()])

        elif cmd == 'ERROR':
            self.setup_connection()

        if cmd == 'PRIVMSG':
            if '!' in prefix and '@' in prefix:
                sender          = prefix.split('!')[0]
                sender_ident    = prefix.split('!')[1].split('@')[0]
                sender_hostname = prefix.split('!')[1].split('@')[1]
            else:
                sender =          prefix
                sender_ident =    ''
                sender_hostname = ''

            receiver = params.split()[0]
            message  = trailing

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
                        
                    elif command == 'fellatio':
                        self.privmsg(self.channel, 'fellatio fellatio fellatio fellatio fellatio f')

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
                            for i in ['americanair', 'jihad', 'bomb', 'terroris', 'attack', 'explo']:
                                if i in parameter.lower():
                                    self.privmsg(self.channel, sender + ', FUCK OFF ALRIGHT')
                                    return
                            alphanum = [chr(i) for i in range(ord('a'), ord('z')+1)]
                            alphanum += [chr(i) for i in range(ord('0'), ord('9')+1)]
                            nonce = ''.join(random.choice(alphanum) for i in range(32))
                            timestamp = str(int(time.time()))

                            http_method = 'POST'
                            base_url = 'https://api.twitter.com/1.1/statuses/update.json'

                            oauth_params = [
                                    ('oauth_consumer_key', self.twitter_key),
                                    ('oauth_nonce', nonce),
                                    ('oauth_signature_method', 'HMAC-SHA1'),
                                    ('oauth_timestamp', timestamp),
                                    ('oauth_token', self.twitter_token),
                                    ('oauth_version', '1.0')
                            ]
                            post_params = [
                                    ('status', parameter)
                            ]

                            encoded_params = []
                            for key, value in oauth_params + post_params:
                                key = urllib.parse.quote(key, safe='')
                                value = urllib.parse.quote(value, safe='')
                                encoded_params.append((key, value))
                            encoded_params = sorted(encoded_params, key = lambda item: item[0])

                            base_string = '&'.join('='.join(item) for item in encoded_params)
                            base_string = '&'.join([http_method.upper(), urllib.parse.quote(base_url, safe=''), urllib.parse.quote(base_string, safe='')])

                            signing_key = '&'.join([urllib.parse.quote(self.twitter_secret, safe=''), urllib.parse.quote(self.twitter_token_secret, safe='')])

                            oauth_signature = base64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()).decode()
                            oauth_params.insert(2, ('oauth_signature', urllib.parse.quote(oauth_signature, safe='')))

                            post_params = [(urllib.parse.quote(item[0], safe=''), urllib.parse.quote(item[1], safe='')) for item in post_params]
                            post_body = '&'.join('='.join(item) for item in post_params)

                            request = urllib.request.Request(base_url, post_body.encode())
                            request.add_header('Authorization', 'OAuth ' + ','.join(item[0]+'="'+item[1]+'"' for item in oauth_params))

                            try:
                                self.privmsg(self.channel, sender + ', ' + self.twitter_url + '/status/' + str(json.loads(urllib.request.urlopen(request).read().decode())['id']))
                            except BaseException as e:
                                self.privmsg(self.channel, sender + ', tweet failed: ' + str(e))
                                return

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
        self.twitter_url = ''
        self.logfile = None
        self.chatlog = None
        self.log_to_stdout = False

        self.current_date = None

        self.msgregex = re.compile(r'^(?:[:](\S+) )?(\S+)(?: (?!:)(.+?))?(?: [:](.+))?$')

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

                elif param == 'twitter_url':
                    self.twitter_url = line[1]

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
        self.send_irc_msg(b'USER', [self.username.encode(), b' . . :' + self.realname.encode()])
        self.send_irc_msg(b'NICK', [self.nickname.encode()])

        msg = b''
        while msg[:4].upper() != b'PING':
            msg = self.recv_irc_msg()
        self.send_irc_msg(b'PONG', [msg[5:]])

        self.privmsg('NickServ', 'IDENTIFY' + ' ' + self.nickname + ' ' + self.password)
        self.send_irc_msg(b'JOIN', [self.channel.encode()])
        self.privmsg(self.channel, 'notice: i\'m a huge faggot')
        time.sleep(2)
        self.privmsg(self.channel, '(also die)')

    # takes bytes
    def send_irc_msg(self, command, parameters):
        message = command + b' ' + b' '.join(parameters) + b'\r\n'
        if self.log_to_stdout:
            print('>>', message.decode('ascii', 'ignore'), end='')
        if self.logfile:
            self.logfile.write(b'>> ' + message)
        self.conn.send(message)

    # returns bytes
    def recv_irc_msg(self):
        buf = b''
        while buf[-2:] != b'\r\n':
            buf += self.conn.recv(1)
        if self.log_to_stdout:
            # for stdout debugging, just printing ascii-representable characters is best
            print(buf.decode('ascii', 'ignore').strip())
        if self.logfile:
            # the logfile receives it raw (if you know what I mean)
            self.logfile.write(buf)

        return buf

    # takes strings
    def privmsg(self, nick, message):
        self.send_irc_msg(b'PRIVMSG', [nick.encode(), b':' + message.encode()])
        if nick.lower() == self.channel.lower():
            self.chatlog_write(self.nickname, message)
