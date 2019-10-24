"""
Cortana

Dedicated bot for the OtaHOAS clubroom at JMT11CD
"""
from pathlib import Path
from sopel import module
from sopel.tools import SopelMemory


STATUS_PREFIX = 'JMT11CD: '
TOPIC_SEPARATOR = '|'
# @TODO Get this from config?
#       Probably not possible since we use
#       decorators for hooking the regex 
BOT_NICK = 'Cortana'
PRESENCE_FILE = '/tmp/cortana.presence'


def setup(bot):
    if 'clubroom_status' not in bot.memory:
        bot.memory['clubroom_status'] = SopelMemory()


@module.nickname_commands('open', 'auki', 'closed', 'kiinni')
@module.rule(r'^Hey,?\s'+BOT_NICK+r',?\s?(.*)$')
def set_clubroom_status(bot, trigger):
    '''Set clubroom status'''
    # Get defaults
    channel = trigger.sender
    status = trigger.group(1)
    presence = False
    extra = ''

    if status in ['open', 'auki', 'closed', 'kiinni']:
        if status in ['open', 'auki']:
            status = 'open'
            presence = True
        else:
            status = 'closed'
            presence = False

        if len(trigger.groups()) > 2:
            # Something extra was said, add it to the extra status
            extra = trigger.groups()[2:]
    else:
        # Assume open but with extra status
        presence = True
        extra = status
        status = 'open'

    # Add channel to memory
    if trigger.sender not in bot.memory['clubroom_status']:
        bot.memory['clubroom_status'][channel] = {
            'presence': False,
            'status': 'closed',
            'extra': ''
        }

    # Update memory with new status and extra
    bot.memory['clubroom_status'][channel]['presence'] = extra
    bot.memory['clubroom_status'][channel]['status'] = status
    bot.memory['clubroom_status'][channel]['extra'] = extra

    # Update the channel topic, retaining the previous extra info
    update_status(bot, trigger.sender)

    # Update presence file
    update_presence_file(presence)


@module.interval(5)
def update_presence(bot):
    '''Update the presence for clubroom via button'''
    presence_file = Path(PRESENCE_FILE)

    # Make a local copy of the memory
    # Iterating the dictionary you are modifying is bad 
    local_status = {}
    for channel, data in bot.memory['clubroom_status'].items():
        local_status[channel] = data

    for channel, data in local_status:
        if presence_file.exists() and not data['presence']:
            # Mark clubroom as open
            # @TODO Randomize these?
            bot.memory['clubroom_status'][channel]['status'] = 'open'
            bot.memory['clubroom_status'][channel]['presence'] = True
            update_status(bot, channel)

        if not presence_file.exists() and data['presence']:
            # Mark clubroom as closed
            # @TODO Randomize these?
            bot.memory['clubroom_status'][channel]['status'] = 'closed'
            bot.memory['clubroom_status'][channel]['presence'] = False
            update_status(bot, channel)


def update_status(bot, channel):
    '''Helper for updating the clubroom status to the channel'''
    # Get the current topic and split it by the separator
    topic = bot.channels[channel].topic.split(TOPIC_SEPARATOR)
    if len(topic) == 1:
        # Pad the topic with a place for our status
        topic.insert(0, '')

    # Build the status string (with optional extra stuff)
    status = bot.memory['clubroom_status'][channel]['status']
    if bot.memory['clubroom_status'][channel]['extra']:
        status += ', ' + bot.memory['clubroom_status'][channel]['extra']

    # Replace the first element in topic with clubroom status
    topic[0] = f'{STATUS_PREFIX}{status} '

    # Publish the updated topic to the channel
    set_topic(bot, channel, f'{TOPIC_SEPARATOR}'.join(topic))


def update_presence_file(presence):
    presence_file = Path(PRESENCE_FILE)
    if presence and not presence_file.exists():
        presence_file.touch()
    if not presence and presence_file.exists():
        presence_file.unlink()


def set_topic(bot, channel, topic):
    '''Set the clubroom channel's topic to given argument'''
    bot.write(('TOPIC', channel), topic)
