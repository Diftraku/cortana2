#!/usr/env python
# -*- coding: utf-8 -*-

import json
import time
import urllib
import urllib2
import os
import random
import re
from botfunctions import *
from lists import *

# TG Bot token
# Use your own, I am not sharing mine
TOKEN = "INSERT TOKEN HERE"

# TG API url
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

# Path to the file indicating button status
path = "/home/cortana/status"

# Current status, initialize to button status
status = os.path.exists(path)

channel_title = "polygame"    # Lower case
channel = None                # Used to report button status change, assumes first channel with message received

def get_url(url):
    request = urllib2.Request(url)
    content = urllib2.urlopen(request).read()
    return content

def get_updates(offset=None):
    url = URL + "getUpdates"
    if offset:
        url += "?offset={}".format(offset)
    content = get_url(url)
    js = json.loads(content)
    return js

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def send_message(text, chat_id):
    text = urllib.pathname2url(str(text))
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)

# Select random line from the list to say
def randline(lista):
    return(lista[random.randint(0, len(lista)-1)])

# Process an update
def process(update):
    global status
    global channel
    global channel_title
    keys = update.keys()

    # A message
    if "message" in keys:
        msg = update["message"]
        text = msg["text"]
        chat_id = msg["chat"]["id"]
        sender = msg["from"]

        if channel == None:
            if(msg["chat"]["title"].lower() == channel_title):
                channel = msg["chat"]["id"]
                print(channel_title)
                print("\n")
                print(channel)

        # Someone replied to a message, was it for us?
        if "reply_to_message" in msg.keys():
            return # Do something here?

        if(re.search("\A((@)?(cortana)(_tg_bot)?(:)?\s(status))(\?)?(:)?\Z", text.lower())):
            if status:
                send_message(randline(status_open  ) ,chat_id)
            else:
                send_message(randline(status_closed) ,chat_id)
            return

        if(re.search("\A((@)?(cortana)(_tg_bot)?(:)?\s(who)(\sare\syou)?)(\?)?(:)?\Z", text.lower())):
            send_message(randline(whoareyou), chat_id)
            duty = "It is my duty to monitor and report on the JMT11CD Clubroom status."
            send_message(duty , chat_id)
            return

        # Something special - mention or bot command
        if "entities" in msg.keys():
            for ent in msg["entities"]:

                # Bot command?
                if ent["type"] == "bot_command":
                    if re.search("(/who)(@cortana_tg_bot)?", text.lower()):
                        send_message(randline(whoareyou), chat_id)
                        duty = "It is my duty to monitor and report on the JMT11CD Clubroom status."
                        send_message(duty , chat_id)

                    elif re.search("(/status)(@cortana_tg_bot)?", text.lower()):
                        if status:
                            send_message(randline(status_open  ) ,chat_id)
                        else:
                            send_message(randline(status_closed) ,chat_id)
                    return

                # Was I mentioned?
                if ent["type"] == "mention":
                    if( re.search("((@)?(cortana)(_tg_bot)?(:)?\s)", text.lower())):
                        return	# TODO do something?

    # Someone edited a message
    elif "edited_message" in keys:
        # Should we do something?
        return

    elif "inline_query" in keys:
	# No
        return

    # Unhandled type, print for debug purposes
    else:
        print(update)


def buttonchecker(chat):
    global status
    if(os.path.exists(path) and not status):	# Button pressed, change to open
        status = True
        send_message(randline(opentopic), chat)
    elif(not os.path.exists(path) and status):	# Room closed, change to closed
        status = False
        send_message(randline(closedtopic), chat)


def main():
    global channel
    last_update_id = 0
    while True:
        if channel != None:
            buttonchecker(channel)
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            for update in updates["result"]:
                try:
                    process(update)
                except:
                    print("\n\nUpdate handling error!\n")
                    print(update)    # For debug
        time.sleep(0.5)


if __name__ == '__main__':
    main()
