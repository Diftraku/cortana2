"""
Cortana

Dedicated bot for the OtaHOAS clubroom at JMT11CD
"""
from pathlib import Path
from sopel import module


CHANNEL = '#polygame'
STATUS_PREFIX = 'JMT11CD: '
TOPIC_SEPARATOR = '|'

def setup(bot):
    if 'clubroom_status' not in bot.memory:
        bot.memory['clubroom_status'] = 'unknown'

@module.commands('open', 'closed')
@module.rate(channel=5)
def toggle_status(bot, trigger):
    '''Toggle the clubroom status from open to closed and back'''
    if bot.memory['clubroom_status'] == trigger.group(1):
        # Refuse to
    bot.memory['clubroom_status'] = trigger.group(1)
    # Update the channel topic, retaining the previous extra info
    update_status(bot)

def update_status(bot):
    '''Helper for updating the status from memory'''
    # Get the current topic and split it by the separator
    topic = bot.channels[CHANNEL].topic.split(TOPIC_SEPARATOR)
    if topic.find(TOPIC_SEPARATOR) == -1:
        # Pad the topic with a place for our status
        topic.insert(0, '')
    topic[0] = STATUS_PREFIX + bot.memory['clubroom_status'] + ' '
    topic = f'{TOPIC_SEPARATOR}'.join(topic)
    set_topic(bot, topic)

def set_topic(bot, topic):
    '''Set the clubroom channel's topic to given argument'''
    bot.write(('TOPIC', CHANNEL), topic)
