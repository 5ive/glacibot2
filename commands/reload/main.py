""" Command to reload any module/command at runtime """

import asyncio
from config import BOT_TOKEN
from env import MODULES, UTILS, GLOBAL

async def run(message):
    """ Parses messages sent to it from slack.py """

    # Make sure it's a message, and not a thread notification
    if message['type'] != 'message' or 'subtype' in message:
        return 1

    pieces = message['text'].lower().split()

    # only respond if we were @mentioned
    if pieces[0] != "<@{0}>".format(UTILS['slack'].user['id']):
        return 2

    # only continue if there are arguments
    if len(pieces) < 2:
        return 3

    if pieces[1] == "Rescan-Commands":
        await UTILS['slack'].say(message['channel'], "Rescanning for commands")
        UTILS['manager'].scan()

    # only continue if there are at least two arguments
    if len(pieces) < 3:
        return 3

    elif pieces[1] == "Reload-Command":
        if pieces[2] in GLOBAL['commands']:
            await UTILS['slack'].say(message['channel'], "Reloading {0} command".format(pieces[2]))
            UTILS['manager'].refresh(GLOBAL['commands'][pieces[2]])
        else:
            await UTILS['slack'].say(message['channel'], "Couldn't find {0} command".format(pieces[2]))

    elif pieces[1] == "Reload-Utility":
        if pieces[2] == "slack":
            timestamp = await UTILS['slack'].say(message['channel'], "Reloading slack, be right back")
            await UTILS['slack'].stop()

            # Wait for slack to gracefully shut down
            while UTILS['slack'].state != UTILS['slack'].State.INACTIVE:
                await asyncio.sleep(0.2)

            # Reload the slack module, and recreate the instance
            UTILS['slack'] = None
            UTILS['manager'].refresh(MODULES['slack'])
            UTILS['slack'] = MODULES['slack'].Slack()
            asyncio.ensure_future(UTILS['slack'].start())

            # Wait for slack to reconnect
            while UTILS['slack'].state != UTILS['slack'].State.CONNECTED:
                await asyncio.sleep(0.2)

            await UTILS['slack'].update(message['channel'], "Finished reloading slack! :smile_cat:", timestamp)

            print('reload slack')

        elif pieces[2] == "manager":
            print('reload manager')

        else:
            await UTILS['slack'].say(message['channel'], "Couldn't find {0} utility".format(pieces[2]))
