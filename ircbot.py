import socket
import re
import urllib.request
import json


def get_line(socket):
    buf = b''
    while buf[-2:] != b'\r\n':
        buf += conn.recv(1)
    try:
        print(buf.decode('utf-8'), end='')
    except UnicodeDecodeError:
        print(buf)
    return buf


def send_line(socket, line):
    try:
        print('>>', line.decode('utf-8'), end='')
    except UnicodeDecodeError:
        print('>>', line, end='')
    socket.send(line)


def send_to_channel(socket, channel, message):
    send_line(socket, b'PRIVMSG ' + channel + b' :' + bytes(message, 'ascii') + b'\r\n')


def send_to_nick(socket, nick, message):
    send_line(socket, b'PRIVMSG ' + nick + b' :' + bytes(message, 'ascii') + b'\r\n')


buf = b''


server   = bytes('irc.esper.net', 'ascii')
port     = 6667
realname = bytes('Kill Me Pls', 'ascii')
username = bytes('killmepls', 'ascii')
nickname = bytes('KillMePls', 'ascii')
password = bytes('killmepl0x', 'ascii')
channel  = bytes('#pastamen', 'ascii')

torin    = 'localhost'
quoteapi = '/quotes/api/random/'


# overall message regexes
privmsg_to_me      = re.compile(r':(.+)!~.+@.+ PRIVMSG ' + nickname.decode('utf-8') + ' :(.*)\r\n', re.IGNORECASE)
privmsg_to_channel = re.compile(r':(.+)!~.+@.+ PRIVMSG ' +  channel.decode('utf-8') + ' :(.*)\r\n', re.IGNORECASE)


while 1:
    # connect
    conn = socket.socket()
    conn.connect((server, port))


    # register
    send_line(conn, b'USER ' + username + b' . . :' + realname + b'\r\n')
    send_line(conn, b'NICK ' + nickname + b'\r\n')
    while buf[:4] != b'PING':
        buf = get_line(conn)
    send_line(conn, b'PONG' + buf[4:])


    # identify with nickserv
    send_to_nick(conn, b'NickServ', 'identify ' + nickname.decode('utf-8') + ' ' + password.decode('utf-8'))
    get_line(conn)


    # join channel
    send_line(conn, b'JOIN ' + channel + b'\r\n')


    # bot loop
    while 1:
        buf = get_line(conn)
        strbuf = ''

        # ping response
        if buf[:4] == b'PING':
            send_line(conn, b'PONG' + buf[4:])
            continue

        # fuckup
        if buf[:5] == b'ERROR':
            break

        try:
            strbuf = buf.decode('utf-8')
        except UnicodeDecodeError:
            continue

        match = re.match(privmsg_to_me, strbuf)
        if match:
            send_to_channel(conn, channel, match.group(1) + ' says: ' + match.group(2))
            continue

        match = re.match(privmsg_to_channel, strbuf)
        if match:
            user = match.group(1)
            message = match.group(2)

            if message[0] == ':':
                message = message[1:]

                if message.lower() == 'roll' or message.lower() == 'rtd':
                    send_to_channel(conn, channel, 'It\'s your lucky day, ' + user + '! You rolled a COPIOUS AMOUNT OF SEMEN.')

                elif message.lower()[:3] == 'me ':
                    send_to_channel(conn, channel, '/me ' + message[3:])

                elif message.lower()[:4] == 'say ':
                    send_to_channel(conn, channel, message[4:])

                elif message.lower() == 'quote':
                    quote = json.loads(urllib.request.urlopen('http://' + torin + quoteapi).read().decode('utf-8'))
                    quotestr = '"' + quote[0] + '" --' + quote[1]
                    if len(quote) > 2:
                        quotestr += ', ' + quote[2]
                    send_to_channel(conn, channel, quotestr)

                else:
                    send_to_channel(conn, channel, 'Unknown fucking command, dumbass.')

            elif message == 'i love cocks':
                send_to_channel(conn, channel, 'SO DO I HAHAHAHAHA wankers.')

            elif message == 'fucking die':
                send_to_channel(conn, channel, 'no.')
