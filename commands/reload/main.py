""" Command to reload any module/command at runtime """

import asyncio
from env import MODULES, UTILS, GLOBAL


async def _rescan_commands(message):
    new_commands, failed_commands = UTILS['manager'].scan()
    output = ""

    if new_commands or failed_commands:
        output = "```\n"

        if new_commands:
            output += "LOADED: {0}\n".format(",".join(new_commands))

        if failed_commands:
            output += "FAILED: {0}\n".format(",".join(failed_commands))

        output += "```"

    else:
        output = "No new commands found."

    await UTILS['slack'].say(message['channel'], output)
    return


async def _reload_commands(commands, message):
    success_commands = []
    failed_commands = []
    unfound_commands = []

    for command in commands:
        # Does the command exist?
        if command in GLOBAL['commands']:
            # Try to reload it, refresh returns boolean
            if UTILS['manager'].refresh(GLOBAL['commands'][command]):
                success_commands.append(command)
            else:
                failed_commands.append(command)
        else:
            unfound_commands.append(command)

    output = ""

    if success_commands:
        output += "SUCCEEDED: {0}\n".format(",".join(success_commands))

    if failed_commands:
        output += "  ERRORED: {0}\n".format(",".join(failed_commands))

    if unfound_commands:
        output += "NOT FOUND: {0}\n".format(",".join(unfound_commands))

    await UTILS['slack'].say(message['channel'], "```\n{0}```".format(output))
    return


async def _reload_utility(utility, message):
    if utility == "slack":
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

        await UTILS['slack'].update(
            message['channel'],
            "Finished reloading slack! :smile_cat:",
            timestamp
        )

    elif utility == "manager":
        print('reload manager')

    else:
        await UTILS['slack'].say(message['channel'], "Couldn't find {0} utility".format(utility))

    return


async def run(message):
    """ Parses messages sent to it from slack.py """

    # Make sure it's a message, and not a thread notification
    if message['type'] != 'message' or 'subtype' in message:
        return 1

    pieces = message['text'].lower().split()

    # only respond if we were @mentioned
    if pieces[0] != "<@{0}>".format(UTILS['slack'].user['id'].lower()):
        return 2

    if len(pieces) >= 3:
        if pieces[1] == "reload-command":
            await _reload_commands(pieces[2:], message)

        elif pieces[1] == "reload-utility":
            await _reload_utility(pieces[2], message)

    elif len(pieces) >= 2:
        if pieces[1] == "rescan-commands":
            await _rescan_commands(message)
