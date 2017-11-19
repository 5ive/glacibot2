""" Simple command to showcase commands/responses """

from env import UTILS

async def run(message):
    """ Parses messages sent to it from slack.py """

    # Make sure it's a message, and not a thread notification
    if message['type'] != 'message' or 'subtype' in message:
        return 1

    try:
        pieces = message['text'].split()

        # only respond if we were @mentioned
        if pieces[0] != "<@{0}>".format(UTILS['slack'].user['id']):
            return 2

        # if they said hello to us, respond in kind
        if pieces[1].lower() in ['hi', 'hello', 'heya', 'hihi']:
            print("Sending response back...")
            await UTILS['slack'].say(message['channel'], "{0}, <@{1}>!".format(pieces[1], message['user']))

    except Exception:
        return 3
