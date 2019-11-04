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


@module.nickname_commands('open', 'auki', 'closed', 'kiinni', 'status')
@module.rule(r'^Hey,?\s'+BOT_NICK+r',?\s?(.*)$')
def set_clubroom_status(bot, trigger):
    '''Update presence and status from IRC'''
    channel = trigger.sender
    status = trigger.group(1)
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
        if trigger.group(2) is not None:
            extra = trigger.group(2)
    else:
        # Handle moose-state, status will be extra
        # and the presence will be open
        presence = True
        extra = status
        if status == 'status' and trigger.group(2) is not None:
            # Grab extra from rest of the trigger,
            # same as with boolean state above
            extra = trigger.group(2)
        status = 'open'

    # Update memory with new status and extra
    bot.memory['clubroom_status'][channel] = {
        'presence': presence,
        'status': status,
        'extra': extra
    }

    # Sync state to channel topic
    sync_channel_topic(bot, trigger.sender)

    # Sync state to presence file
    sync_presence_file(bot, trigger.sender)


@module.interval(5)
def sync_presence_timer(bot):
    '''Update channel topic from presence file'''
    presence_file = Path(PRESENCE_FILE)

    # Make a local copy of the memory
    # Iterating the dictionary you are modifying is bad 
    local_status = {}
    for channel, data in bot.memory['clubroom_status'].items():
        local_status[channel] = data

    for channel, data in local_status.items():
        if presence_file.exists() and not data['presence']:
            # Mark clubroom as open
            # @TODO Randomize these?
            bot.memory['clubroom_status'][channel]['status'] = 'open'
            bot.memory['clubroom_status'][channel]['presence'] = True
            sync_channel_topic(bot, channel)

        if not presence_file.exists() and data['presence']:
            # Mark clubroom as closed
            # @TODO Randomize these?
            bot.memory['clubroom_status'][channel]['status'] = 'closed'
            bot.memory['clubroom_status'][channel]['presence'] = False
            sync_channel_topic(bot, channel)


def sync_channel_topic(bot, channel):
    '''Helper for updating the clubroom status to the channel'''
    # Get the current topic and split it by the separator
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
    presence_file = Path(PRESENCE_FILE)

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
