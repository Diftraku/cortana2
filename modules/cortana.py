"""
Cortana

Dedicated bot for the OtaHOAS clubroom at JMT11CD
"""
import re
from pathlib import Path

from sopel import module
from sopel.tools import (SopelMemory, get_command_pattern,
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
    """Method for mangling the trigger enough to pass to IRC side"""
    # Group 1 has sender's Telegram username
    #sender = trigger.group(1)
    # Group 2 has the rest of the line, including the bot nickname
    line = trigger.group(2)

    # Compare against the known commands
    regex = get_nickname_command_regexp(
        bot.config.core.nick, TOPIC_COMMANDS_COMBINED, bot.config.core.alias_nicks)
    match = re.match(regex, line)

    if not match:
        return

    channel = trigger.sender
    status = match.group(1).lower().translate(str.maketrans('', '', ',:'))
    rest = None
    if len(match.groups()) > 1:
        rest = match.group(2)
    update_clubroom_status(bot, channel, status, rest)


def update_clubroom_status(bot, channel, status, rest):
    presence = False
    extra = ''

    # Process true-false-moose
    if status in ['open', 'auki', 'closed', 'kiinni']:
        # Handle simple open/closed states
        if status in ['open', 'auki',]:
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
        presence_file = Path(PRESENCE_FILE_TEMPLATE.format(channel))
        if presence_file.exists() and not data['presence']:
            # Mark clubroom as open
            # @TODO Randomize these?
            bot.memory['clubroom_status'][channel]['status'] = 'open'
            bot.memory['clubroom_status'][channel]['presence'] = True
            # Channel topic requires updating
            # @TODO Sniff the topic to prevent spamming
            sync_channel_topic(bot, channel)

        if not presence_file.exists() and data['presence']:
            # Mark clubroom as closed
            # @TODO Randomize these?
            bot.memory['clubroom_status'][channel]['status'] = 'closed'
            bot.memory['clubroom_status'][channel]['presence'] = False
            # Channel topic requires updating
            # @TODO Sniff the topic to prevent spamming
            sync_channel_topic(bot, channel)


def sync_channel_topic(bot, channel):
    '''Helper for updating the clubroom status to the channel'''
    # Get the current topic and split it by the separator
    if channel not in bot.channels:
        # Skip updating at this time, bot is not currently on the channel
        return
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
    if presence and not presence_file.exists():
        presence_file.touch()
    if not presence and presence_file.exists():
        presence_file.unlink()


def set_topic(bot, channel, topic):
    '''Set the clubroom channel's topic to given argument'''
    bot.write(('TOPIC', channel), topic)
