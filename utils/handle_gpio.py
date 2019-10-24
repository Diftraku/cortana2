from datetime import datetime
from pathlib import Path
from time import sleep

from gpiozero import LED, Button

PRESENCE_FILE = '/tmp/cortana.presence'

def main():
    # setup
    # See https://www.raspberrypi.org/documentation/usage/gpio/
    # Pins are on the edge of the connector, right next to each-other
    # Indicator should connect the positive side (anode) to GPIO pin 20
    # and negative side (cathode) to ground 
    # Button should connect 3V3 to GPIO pin 21
    indicator = LED(pin=20, initial_value=False)
    button = Button(pin=21, pull_up=False, bounce_time=0.5)
    button.when_pressed = handle_button

    # This is used to communicate the state relatively "thread-safely"
    # to the Sopel bot
    presence_file = Path(PRESENCE_FILE)

    # Prime the state from file, defaults to False if file does not exist
    last_state = state = read_state(presence_file)

    while True:
        # Update the state from file
        state = read_state(presence_file)

        # Check if state changed
        if state != last_state:
            # Set LED based on the state
            if state:
                indicator.on()
            else:
                indicator.off()
            print(f'{datetime.now().isoformat("seconds")} - Toggling LED state')
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
        presence_file.unlink()
    else:
        presence_file.touch()
    print(f'{datetime.now().isoformat("seconds")} - Toggling presence state')


if __name__ == "__main__":
    main()
