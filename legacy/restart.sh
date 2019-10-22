#!/bin/bash
sudo -v
sudo chmod +rwx /dev/urandom
sudo killall -9 screen
screen -wipe
screen -dmS sopel python2.7 sopel/sopel.py        
sudo screen -dmS buttonreader python buttonreader.py
