""" Defines Admin command object """

import command
from env import UTILS

class Admin(command.Command):
    """ Controls adding/removing moderators """

    def initialize(self):
        pass

    def destroy(self):
        pass

    async def command(self, message):
        pass


async def run(message):
    """ Parses messages sent to it from slack.py """

    # Make sure it's a message, and not a thread notification
    if message['type'] != 'message' or 'subtype' in message:
        return

    pieces = message['text'].split()

    if not pieces or pieces[0] != "<@{0}>".format(UTILS['slack'].user['id']):
        return
