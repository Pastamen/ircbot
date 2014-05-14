import bot

pastamen = bot.IRCBot('config.txt')

while 1:
    pastamen.parse_irc_msg(pastamen.recv_irc_msg())
