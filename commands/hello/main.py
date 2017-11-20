""" Defines Hello command object """

import command
from env import UTILS

class Hello(command.Command):
    """ Simple command to showcase command structure/responses """

    def initialize(self):
        pass

    def destroy(self):
        pass

    async def command(self, message):
        # Make sure it's a message, and not a thread notification
        if message['type'] != 'message' or 'subtype' in message:
            return

        pieces = message['text'].split()

        # only respond if we were @mentioned
        if not pieces or pieces[0] != "<@{0}>".format(UTILS['slack'].user['id']):
            return

        # if they said hello to us, respond in kind
        if pieces[1].lower() in ['hi', 'hello', 'heya', 'hihi']:
            await UTILS['slack'].say(message['channel'], "{0}, <@{1}>!".format(pieces[1], message['user']))
