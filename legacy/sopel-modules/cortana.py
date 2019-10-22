#coding=utf-8

from subprocess import call
import time
import os
import sys
import sopel
import sopel.module
from sopel.tools import events
from sopel.tools.target import User, Channel
from sopel.module import (commands, priority, OP, rate, require_owner, require_admin, HALFOP, require_privilege, require_chanmsg, 
require_privmsg)
import random
import sopel.config

channelmask = "JMT11CD: "
botname = "Cortana"
path = "/home/cortana/status"
status = 2
quietmode = True
channel = "#polygame"

exec(open("/home/cortana/sopel/sopel/modules/cortana-resources/wordlists.py").read())
#exec(open(path +"../sopel/modules/cortana-resources/cortana-functions.py").read())

# picks a random line from the given list
def list(lista):
	return(lista[random.randint(0, len(lista)-1)])

# logger of sorts
def logger(who,text):
	call(["date"])
	print("<"+str(who)+"> "+ str(text)+"\n")


# TOPIC UPDATER
@require_chanmsg('How do you expect me to change the topic of a private conversation?')
@sopel.module.rule('(Hey(?::|,)?\s'+botname+'(?:\s)?(?::|,)?\s)')
def topicparser(bot, trigger):
	global status
	global quietmode
	global channel
	logger(trigger.nick,trigger)
	if(isbanned(bot,trigger.nick,channel)):
		return
	rivi = trigger.split(' ')
			# BLANK TOPICS
	if ((len(rivi) == 2) or (rivi[2] == '')):
		bot.reply(list(blanktopic))
		return
			# BANNED WORDS?
	for banned in bannedwords:
		if (trigger.upper().find(banned)!= -1):
				bot.reply(list(stupidtopic))
				return
		# CLUBROOM CLOSED
	if (rivi[2].upper() in closewords):
		status = 0
		writetopic(bot,"closed",channel)
		return
			# I guess the room is open then?
	status = 1
	writetopic(bot,trigger,channel)
	return

def writetopic(bot,triggeri,channel):
	global status
	global path
	global channelmask
	global quietmode
	topic = ''
	rivi = triggeri.split(' ')
	if (status == True):
		call(['touch',str(path)])
		if(quietmode == False):
			speak(bot,list(opentopic),channel)
		for index in range(len(rivi)-2):
			topic += rivi[index + 2].strip() + ' '
	else:
		call(['rm', str(path)])
		if(quietmode == False):
			speak(bot,list(closedtopic),channel)
		topic = 'closed '
	bot.write(('TOPIC', channel))
	oldtopic = bot.channels[channel].topic
	oldtopic = oldtopic.split('|')
	for index in range(len(oldtopic)-1):
		topic += '| ' + oldtopic[index + 1].strip() + ' '
	bot.write(('TOPIC', channel + " :" + channelmask + topic))


# Who ARE YOU RESPONDER
@sopel.module.nickname_commands('(Who\sare\syou(:?\?)?)')
def whoami(bot, trigger):
	if(isbanned(bot,trigger.nick,trigger.sender)):
		return
	logger(trigger.nick,trigger)
	bot.reply(list(whoareyou))
	bot.reply("My duty is to monitor the JMT11CD clubroom status.")


# HELP
@sopel.module.nickname_commands('Help')
def helptext(bot, trigger):
	if(isbanned(bot,trigger.nick,trigger.sender)):
		return
	logger(trigger.nick,trigger)
	bot.msg(trigger.nick, list(help))
	for line in helplist:
		bot.msg(trigger.nick, line)


# BUTTONCHECKER
@sopel.module.interval(5)
def buttonreader(bot):
	global status
	global path
	global channel
	if (status != os.path.exists(str(path))):
		time.sleep(0.25)
		if (status != os.path.exists(str(path))):		# removes race condition between topicwriter and this check
			if(status == True):
				status = 0
				writetopic(bot,"plop plop closed",channel)
			else:
				status = 1
				writetopic(bot,"plop plop open",channel)		# plop plop removed by topicwriter... purkkakorjaus
	elif (status == 2):
		topicscanner(bot,channel)

def topicscanner(bot,channel):
	global status
	global path
	global quietmode
	bot.write(('TOPIC', channel))
	oldtopic = bot.channels[channel.lower()].topic
	oldtopic = oldtopic.split(" ")
	if(oldtopic[1].upper() in closewords and status == 1):
		if(quietmode==False):
			speak(bot,list(closedtopic),channel)
		status = 0
		call(["rm",str(path)])
	elif(oldtopic[1].upper() not in closewords and status == 0):
		if(quietmode == False):
			speak(bot,list(opentopic),channel)
		status = 1
		call(["touch",str(path)])

#@sopel.module.nickname_commands('quiet')
#def quietmodeon(bot,trigger):
#	global quietmode
#	logger(trigger.nick,trigger)
#	if(isbanned(bot,trigger.nick,trigger.sender)):
#		return
#	quietmode = True

#@sopel.module.nickname_commands('speak')
#def quietmodeoff(bot,trigger):
#	global quietmode
#	logger(trigger.nick,trigger)
#	if(isbanned(bot,trigger.nick,trigger.sender)):
#		return
#	quietmode = False
#	speak(bot,"Understood!",trigger.sender)

def speak(bot,text,whereto):
	global quietmode
	if(quietmode != True):
		bot.say(text,whereto)

def isbanned(bot,nick,whereto):
	if nick.upper in bannedusers:
		speak(bot,list(notallowed),whereto)
		return True
	else:
		return False

