#!/usr/bin/env python3
import os
from datetime import datetime
from pathlib import Path
from time import sleep
import logging

from gpiozero import LED, PWMLED, Button

PRESENCE_FILE = os.environ.get('PRESENCE_FILE', '/tmp/cortana.presence')

def main():
    # setup
    # See https://www.raspberrypi.org/documentation/usage/gpio/
    # Pins are on the edge of the connector, right next to each-other
    # Indicator should connect the positive side (anode, yellow wire) to GPIO pin 23
    # and negative side (cathode, orange wire) to ground
    # Button should connect 3V3 (blue wire) to GPIO pin 24 (green wire)
    away_indicator = PWMLED(pin=18, active_high=False, initial_value=False)
    home_indicator = LED(pin=23, active_high=False, initial_value=False)
    button = Button(pin=17, pull_up=False)
    button.when_held = handle_button
    button.hold_time = 0.5

    # Setup logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    # This is used to communicate the state relatively "thread-safely"
    # to the Sopel bot
    presence_file = Path(PRESENCE_FILE)

    # Prime the state from file, defaults to False if file does not exist
    last_state = state = read_state(presence_file)

    logger.info('Starting main loop')

    while True:
        # Update the state from file
        state = read_state(presence_file)

        # Check if state changed
        if state != last_state:
            # Set LED based on the state
            if state:
                home_indicator.on()
                away_indicator.off()
            else:
                home_indicator.off()
                away_indicator.pulse(fade_in_time=1, fade_out_time=3)
            logger.info('Toggling LED state: %s', 'on' if state else 'off')
            last_state = state

        # Sleep before next round
        sleep(0.5)


def read_state(presence_file: Path) -> bool:
    ''' No file means no presence'''
    if presence_file.exists():
        return True
    return False


def handle_button():
    '''Toggle presence based on button input'''
    presence_file = Path(PRESENCE_FILE)
    if presence_file.exists():
        logging.getLogger(__name__).info('Toggling local presence state: absent')
        presence_file.unlink()
    else:
        logging.getLogger(__name__).info('Toggling local presence state: present')
        presence_file.touch()


if __name__ == "__main__":
    main()
