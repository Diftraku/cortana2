"""
Cortana

Dedicated bot for the OtaHOAS clubroom at JMT11CD
"""
from pathlib import Path
from sopel import module
from sopel.tools import SopelMemory


STATUS_PREFIX = 'JMT11CD: '
TOPIC_SEPARATOR = '|'

def setup(bot):
    if 'clubroom_status' not in bot.memory:
        bot.memory['clubroom_status'] = SopelMemory()

@module.commands('open', 'closed')
@module.rate(channel=5)
def toggle_status(bot, trigger):
    '''Toggle the clubroom status from open to closed and back'''
    bot.memory['clubroom_status'][trigger.sender] = trigger.group(1)
    # Update the channel topic, retaining the previous extra info
    update_status(bot, trigger.sender)

def update_status(bot, channel):
    '''Helper for updating the status from memory'''
    # Get the current topic and split it by the separator
    topic = bot.channels[channel].topic.split(TOPIC_SEPARATOR)
    if topic.find(TOPIC_SEPARATOR) == -1:
        # Pad the topic with a place for our status
        topic.insert(0, '')
    topic[0] = STATUS_PREFIX + \
        bot.memory['clubroom_status'][channel] + ' '
    topic = f'{TOPIC_SEPARATOR}'.join(topic)
    set_topic(bot, channel, topic)

def set_topic(bot, channel, topic):
    '''Set the clubroom channel's topic to given argument'''
    bot.write(('TOPIC', channel), topic)
