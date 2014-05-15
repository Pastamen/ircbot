import bot
import traceback

try:
    pastamen = bot.IRCBot('/home/torin/ircbot/config.txt')
    while 1:
        pastamen.parse_irc_msg(pastamen.recv_irc_msg())
except BaseException as e:
    traceback.print_exc();
    try:
        pastamen.logfile.write(bytes('\r\n' + '*'*20 + ' CRASH ' + '*'*20 + '\r\n', 'ascii'))
        pastamen.logfile.write(bytes('\r\n' + traceback.format_exc() + '\r\n', 'ascii'))
    except:
        pass
    input()
