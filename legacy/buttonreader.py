#!/usr/bin/env python
import sys
import os
import sys
from subprocess import call

galileo_path = "/media/mmcblk0p1/storage";
if galileo_path not in sys.path:
    sys.path.append(galileo_path);

from pyGalileo import *
'''/*
 The circuit:
 * LED attached from pin 13 to ground 
 * pushbutton attached to pin 2 from +5V
 * 10K resistor attached to pin 2 from ground
 */'''

buttonPin = 4;
ledPin =  13;
path = "/home/cortana/status"

def setup():
  	pinMode(ledPin, OUTPUT);
  	pinMode(buttonPin, INPUT);

def page(state):
	if(state == 1):
		call(['cp','/home/cortana/open.html','/www/pages/index.html'])
	else:
		call(['cp','/home/cortana/closed.html','/www/pages/index.html'])

def loop():
	status = False
	global path
	while(1):
		time.sleep(0.2)
		if (digitalRead(buttonPin) == LOW):
			time.sleep(0.1)
			if(digitalRead(buttonPin) == LOW):
				if(status == True):
					status = False
					call(['rm',str(path)])
					digitalWrite(ledPin, LOW)
					time.sleep(5)
				else:
					status = True
					call(['touch',str(path)])
					call(['chmod','777',str(path)])
					digitalWrite(ledPin, HIGH)
					time.sleep(5)
				print(status)
				page(status)
		if(status != os.path.exists(path)):
			status = os.path.exists(path)
			page(status)
			if (status == True):
				digitalWrite(ledPin, HIGH)
			if (status == False):
				digitalWrite(ledPin, LOW)

setup();
loop();
