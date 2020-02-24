"""
Cortana

Dedicated bot for the OtaHOAS clubroom at JMT11CD
"""
import re
from pathlib import Path
from datetime import datetime

from sopel import module
from sopel.tools import (SopelMemory, events, get_command_pattern,
                         get_nickname_command_regexp)

STATUS_PREFIX = 'JMT11CD: '  # @TODO Move to a channel specific config
TOPIC_SEPARATOR = '|'  # @TODO Same as above
PRESENCE_FILE_TEMPLATE = '/tmp/cortana.presence.{}'

# Nick commands to change topic
TOPIC_COMMANDS = [
    '(?i)open[,:]?', '(?i)auki[,:]?', '(?i)closed[,:]?',
    '(?i)kiinni[,:]?', '(?i)status[,:]?', '(?i)reporting[,:]?',
    '(?i)reserved[,:]?', '(?i)varattu[,:]?'
]
TOPIC_COMMANDS_COMBINED = '|'.join(TOPIC_COMMANDS)
# Regex rules for triggering nick commands above
TOPIC_RULES = [
    r'^Hey,?\s$nickname,?\s?(.*)$'
]


def setup(bot):
    if 'clubroom_status' not in bot.memory:
        bot.memory['clubroom_status'] = SopelMemory()
    for channel in bot.config.core.channels:
        # Initialize state for each autojoin channel
        bot.memory['clubroom_status'][channel] = {
            'presence': False,
            'status': 'closed',
            'extra': ''
        }


@module.nickname_commands(*TOPIC_COMMANDS)
@module.rule(*TOPIC_RULES)
def handle_irc_commands(bot, trigger):
    '''Update presence and status from IRC'''
    channel = trigger.sender
    status = trigger.group(1).lower().translate(str.maketrans('', '', ',:'))
    rest = None
    if len(trigger.groups()) > 1:
        rest = trigger.group(2)
    update_clubroom_status(bot, channel, status, rest)


@module.rule(r"^<(.*)>\s($nickname[\s\:\,]?.*?)$")
def handle_teleirc_commands(bot, trigger):
    """Trigger for handling bridged messages from TeleIRC"""
    # Group 1 has sender's Telegram username
    #sender = trigger.group(1)
    # Group 2 has the rest of the line, including the bot nickname
    line = trigger.group(2)

    # Compare against the known commands
    regex = get_nickname_command_regexp(
        bot.config.core.nick, TOPIC_COMMANDS_COMBINED, bot.config.core.alias_nicks)
    match = re.match(regex, line)

    # Bail if no commands matched
    if not match:
        return

    # parse the channel and status
    channel = trigger.sender
    status = match.group(1).lower().translate(str.maketrans('', '', ',:'))

    # grab extra (if any), should always be in group 2
    rest = None
    if len(match.groups()) > 1:
        rest = match.group(2)

    # Fire an update
    update_clubroom_status(bot, channel, status, rest)


@module.event(events.RPL_TOPIC, events.RPL_NOTOPIC)
@module.rule('.*')  # Dummy to make event match work (rtfm)
def handle_topic(bot, trigger):
    """Method for mangling the trigger enough to pass to IRC side"""
    if len(trigger.args) < 3:
        # No topic set
        # @TODO Set the topic based on current state
        return

    # Expand args into channel name and topic
    _, channel, topic = trigger.args

    # Parse out status bit and the real topic
    status, _, topic = topic.partition(TOPIC_SEPARATOR)

    # Parse out the real status and extra
    status = status.replace(STATUS_PREFIX, '')
    status, _, extra = status.partition(',')

    # Check if topic needs updating
    # @TODO let update_clubroom_status() handle this?
    if channel in bot.memory['clubroom_status']:
        # Grab the clubroom details from memory
        clubroom_status = bot.memory['clubroom_status'][channel]

        # Set our dirty bit to false
        needs_updating = False

        # Check if we need to set stuff
        if status != clubroom_status['status']:
            needs_updating = True
        if extra != clubroom_status['extra']:
            needs_updating = True
        
        # Only change if we have something to change
        if needs_updating:
            # Update memory and sync the file
            presence = True if status in ['open', 'reserved'] else False
            bot.memory['clubroom_status'][channel] = {
                'presence': presence,
                'status': status,
                'extra': extra
            }

            # Fire update to GPIO
            sync_presence_file(bot, channel)


def update_clubroom_status(bot, channel, status, rest):
    '''Do the magic'''
    presence = False
    extra = ''

    # Process true-false-moose
    if status in ['open', 'auki', 'closed', 'kiinni']:
        # Handle simple open/closed states
        if status not in ['closed', 'kiinni',]:
            status = 'open'
            presence = True
        else:
            status = 'closed'
            presence = False

        # Handle additional information
        if rest is not None:
            extra = rest
    else:
        # Handle moose-state, status will be extra
        # and the presence will be open
        presence = True
        extra = status
        if rest is not None:
            # Grab extra from rest of the trigger,
            # same as with boolean state above
            extra = rest
        if status == 'status' and rest is not None:
            # We have a status report with extra stuff, mark as open
            status = 'open'
        if status in ['varattu', 'reserved']:
            status = 'reserved'

    # Update memory with new status and extra
    bot.memory['clubroom_status'][channel] = {
        'presence': presence,
        'status': status,
        'extra': extra
    }

    # Sync state to channel topic
    sync_channel_topic(bot, channel)

    # Sync state to presence file
    sync_presence_file(bot, channel)


@module.interval(5)
def sync_presence_timer(bot):
    '''Update channel topic from presence file'''
    # Make a local copy of the memory
    # Iterating the dictionary you are modifying is bad 
    local_status = {}
    for channel, data in bot.memory['clubroom_status'].items():
        local_status[channel] = data

    for channel, data in local_status.items():
        # @TODO remove these if's an use an if-else instead?
        presence_file = Path(PRESENCE_FILE_TEMPLATE.format(channel))
        dirty = False
        if presence_file.exists() and not data['presence']:
            # Mark clubroom as open
            # @TODO Randomize these?
            dirty = True
            bot.memory['clubroom_status'][channel]['status'] = 'open'
            bot.memory['clubroom_status'][channel]['presence'] = True

        if not presence_file.exists() and data['presence']:
            # Mark clubroom as closed
            # @TODO Randomize these?
            dirty = True
            bot.memory['clubroom_status'][channel]['status'] = 'closed'
            bot.memory['clubroom_status'][channel]['presence'] = False
            # Clear extra if we're past midnight
            if datetime.now().hour >= 0:
                bot.memory['clubroom_status'][channel]['extra'] = ''

        # Channel topic requires updating
        # @TODO Sniff the topic to prevent spamming
        if dirty:
            sync_channel_topic(bot, channel)


def sync_channel_topic(bot, channel):
    '''Helper for updating the clubroom status to the channel'''
    # Get the current topic and split it by the separator
    if channel not in bot.channels:
        # Skip updating at this time, bot is not currently on the channel
        return

    # Parse topic into usable chunks by exploding it
    topic = bot.channels[channel].topic.split(TOPIC_SEPARATOR)
    if len(topic) == 1:
        # Pad the topic with a place for our status
        topic.insert(0, '')

    # Build the status string (with optional extra stuff)
    status = bot.memory['clubroom_status'][channel]['status']
    if bot.memory['clubroom_status'][channel]['extra']:
        status = status + ', ' + bot.memory['clubroom_status'][channel]['extra']

    # Replace the first element in topic with clubroom status
    topic[0] = f'{STATUS_PREFIX}{status} '

    # Publish the updated topic to the channel
    set_topic(bot, channel, f'{TOPIC_SEPARATOR}'.join(topic))


def sync_presence_file(bot, channel):
    '''Sync state from memory to presence file'''
    presence_file = Path(PRESENCE_FILE_TEMPLATE.format(channel))

    # Get the presence from memory
    presence = bot.memory['clubroom_status'][channel]['presence']

    # Link or unlink the file, depending on the desired state
    # @TODO remove the extra if and turn it into an else
    if presence and not presence_file.exists():
        presence_file.touch()
    if not presence and presence_file.exists():
        presence_file.unlink()


def set_topic(bot, channel, topic):
    '''Set the clubroom channel's topic to given argument'''
    bot.write(('TOPIC', channel), topic)
