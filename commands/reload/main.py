""" Command to reload any module/command at runtime """

import asyncio
import command
from env import MODULES, UTILS, GLOBAL

class Reload(command.Command):
    """ Controls reloading modules/commands through slack """

    def initialize(self):
        pass

    def destroy(self):
        pass


    async def command(self, message):
        # Make sure it's a message, and not a thread notification
        if message['type'] != 'message' or 'subtype' in message:
            return 1

        pieces = message['text'].lower().split()

        # only respond if we were @mentioned
        if pieces[0] != "<@{0}>".format(UTILS['slack'].user['id'].lower()):
            return 2

        if len(pieces) >= 3:
            if pieces[1] == "reload-command":
                await self._reload_commands(pieces[2:], message)

            elif pieces[1] == "reload-utility":
                await self._reload_utility(pieces[2], message)

        elif len(pieces) >= 2:
            if pieces[1] == "rescan-commands":
                await self._rescan_commands(message)


    async def _rescan_commands(self, message):
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


    async def _reload_commands(self, commands, message):
        success_commands = []
        failed_commands = []
        unfound_commands = []

        for current in commands:
            # Does the command exist?
            if current in GLOBAL['commands']:
                # Try to reload it, refresh returns boolean
                if UTILS['manager'].refresh(GLOBAL['commands'][current]):
                    success_commands.append(current)
                else:
                    failed_commands.append(current)
            else:
                unfound_commands.append(current)

        output = ""

        if success_commands:
            output += "SUCCEEDED: {0}\n".format(",".join(success_commands))

        if failed_commands:
            output += "  ERRORED: {0}\n".format(",".join(failed_commands))

        if unfound_commands:
            output += "NOT FOUND: {0}\n".format(",".join(unfound_commands))

        await UTILS['slack'].say(message['channel'], "```\n{0}```".format(output))
        return


    async def _reload_utility(self, utility, message):
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
            UTILS['manager'].refresh(UTILS['manager'])
            await UTILS['slack'].say(message['channel'], "Reloaded the manager")

        else:
            await UTILS['slack'].say(message['channel'], "Couldn't find {0} utility".format(utility))

        return
