import socket
import re
import urllib.request
import json

class IRCBot:

    def chathandle(self, msg):
        # this is received in bytes form, if we can't decode it then there's no point continuing
        try:
            msg = msg.decode('utf-8')
        except UnicodeDecodeError:
            try:
                msg = msg.decode('ascii')
            except UnicodeDecodeError:
                return

        regexmatch = re.match(self.chatregex, msg)
        if not regexmatch:
            return

        sender   = regexmatch.group(1)
        receiver = regexmatch.group(2)
        message  = regexmatch.group(3)

        if receiver.lower() == self.nickname.lower():
            self.privmsg(self.channel, sender + ' says: ' + message)

        elif receiver.lower() == self.channel.lower():
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
                    self.privmsg(self.channel, '/me' + parameter)

                elif command == 'quote':
                    quote = json.loads(urllib.request.urlopen(self.quote_url).read().decode('utf-8'))
                    quotestr = '"' + quote[0] + '" --' + quote[1]
                    if len(quote) > 2:
                        quotestr += ', ' + quote[2]
                    self.privmsg(self.channel, quotestr)

                else:
                    self.privmsg(self.channel, 'Unknown fucking command, dumbass.')
            else:
                if message.lower() == 'i love cocks':
                    self.privmsg(self.channel, 'SO DO I HAHAHAHAHA wankers.')

                elif message.lower() == 'fucking die':
                    self.privmsg(self.channel, 'no.')

                else:
                    pass

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
        self.logfile = None
        self.log_to_stdout = False

        self.chatregex = re.compile(r':(.+)!~.+@.+ PRIVMSG (.+) :(.*)\r\n', re.IGNORECASE)

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

                elif param == 'logfile':
                    self.logfile = open(line[1], 'ab')

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

    # this expects bytes
    def parse_irc_msg(self, message):
        if message[:4].upper() == b'PING':
            self.send_irc_msg('PONG', [message[5:].decode('ascii')])

        elif message[:5].upper() == b'ERROR':
            self.setup_connection()

        elif chr(message[0]) == ':':
            self.chathandle(message)

        else:
            pass
