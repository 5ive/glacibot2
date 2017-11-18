""" Defines slack framework for WebAPI and RTM """

from enum import Enum
import time
import ctypes
import asyncio
import aiohttp
from env import GLOBAL, STATS
from config import BOT_TOKEN

class Slack:
    """ framework to connect/reconnect, and talk to Slack WebAPI and RTM """

    class State(Enum):
        """ Enum to store the state of the slack connection """
        INACTIVE = 0
        CONNECTING = 1
        CONNECTED = 2
        DISCONNECTED = 3
        SHUTTING_DOWN = 4


    def __init__(self):
        self.socket = None
        # State storage
        self.heartbeat_pending = False
        self.state = Slack.State.INACTIVE
        self.reconnects = 0
        # Statistics storage
        self.latency = []
        # Identity storage
        self.team = {'name': None, 'id': None}
        self.user = {'name': None, 'id': None}


    async def _heartbeat(self, interval):
        print("{0}s heartbeat is born".format(interval))

        while True:
            await asyncio.sleep(interval)

            if self.heartbeat_pending:
                print("Hit heartbeat timeout")
                return 1

            self.heartbeat_pending = True

            await self.socket.send_json({
                "type": "ping",
                "sent": time.time()
            })


    async def _killswitch(self, interval):
        print("{0}s killswitch engaged".format(interval))

        while True:
            await asyncio.sleep(interval)

            # Check if we've sent the kill signal to the main connection
            if self.state == Slack.State.SHUTTING_DOWN:
                print("Received termination signal")
                return 1


    async def _listen(self):
        print("listen is born")

        while True:
            message = await self.socket.receive_json()

            # This shouldn't ever happen
            if 'type' not in message:
                print("Got malformed message: {0}".format(message))
                return 2

            # Internally handle ping/pong events
            if message['type'] == 'pong':
                self.heartbeat_pending = False
                self.latency.append(time.time() - float(message['sent']))
                print("Got heartbeat. (Latency: {0}s, Lifetime: {1}s)".format(
                    round(self.latency[-1], 3),
                    round(time.time() - STATS['connected_at'], 3)
                ))

                # Track the last 10 pings for historical tracking
                if len(self.latency) > 10:
                    self.latency.pop(0)

            else:
                # Give each custom command the input in its .run(data) method
                for command in GLOBAL['commands'].values():
                    asyncio.ensure_future(command.run(message))


    async def stop(self):
        """ Tell the slack instance to cleanly shut down """
        self.state = Slack.State.SHUTTING_DOWN


    async def start(self, reconnect=True):
        """ Create a connection to Slack's RTM capable of reconnecting """

        # Get a copy of our current identity
        await self._get_identity()

        while reconnect and self.state != Slack.State.SHUTTING_DOWN:
            await self._run()

            if self.state != Slack.State.SHUTTING_DOWN:
                self.state = Slack.State.DISCONNECTED

                # Wait some amount of time (between 1 and 32 seconds) before reconnecting
                delta = pow(2, min(5, self.reconnects))
                self.reconnects += 1
                print("Waiting {0} seconds before reconnecting (attempt {1})".format(delta, self.reconnects))
                await asyncio.sleep(delta)

                # Force refresh DNS, https://stackoverflow.com/questions/13606584/python-not-getting-ip-if-cable-connected-after-script-has-started
                try:
                    libc = ctypes.CDLL('libc.so.6')
                    res_init = getattr(libc, '__res_init')
                    res_init(None)
                except:
                    print("Error calling libc.__res_init")

        print("Exiting from slack")
        self.state = Slack.State.INACTIVE


    async def _run(self):
        # Initialize async task variables
        task_heartbeat = None
        task_listen = None
        task_killswitch = None

        try:
            self.state = Slack.State.CONNECTING

            # Attempt to get a connection point from Slack web API
            print("Requesting RTM connection point")
            rtm = await self._api_call("rtm.start")

            # Attempt to open up a websocket to the RTM connection point
            print("Got RTM connect point: {0}".format(rtm['url']))
            self.socket = await GLOBAL['socket'].ws_connect(rtm['url'])

            # Spin up the async tasks to interact with Slack RTM
            print("Starting up tasks")
            task_heartbeat = asyncio.ensure_future(self._heartbeat(30))
            task_listen = asyncio.ensure_future(self._listen())
            task_killswitch = asyncio.ensure_future(self._killswitch(1))

            # If we get to this point, we've got a successful connection
            STATS['connected_at'] = time.time()
            self.heartbeat_pending = False
            self.reconnects = 0
            self.state = Slack.State.CONNECTED

            # Once we're here, wait until something returns (ie., closes)
            print("Healthy main loop sequence")
            await asyncio.wait(
                [task_heartbeat, task_listen, task_killswitch],
                return_when=asyncio.FIRST_COMPLETED
            )

            print("Broke out of healthy loop")

        except Exception as exception:
            print("Broke unexpectedly out of unhealthy loop: {0}".format(exception))

        if task_heartbeat:
            print("Shutting down heartbeat: {0}".format(task_heartbeat))
            task_heartbeat.cancel()

        if task_listen:
            print("Shutting down listen: {0}".format(task_listen))
            task_listen.cancel()

        if task_killswitch:
            print("AFTS is safed: {0}".format(task_killswitch))
            task_killswitch.cancel()

        print("Letting tasks settle")
        await asyncio.sleep(0.5)

        print("Closing the socket")
        await self.socket.close()


    async def say(self, channel, text):
        """ Sends a plain message to the specified channel """
        try:
            response = await self._api_call(
                "chat.postMessage",
                {'channel': channel, 'text': text, 'as_user': True}
            )

            return response['ts']

        except Exception as exception:
            print("Encountered error sending chat.postMessage: {0}".format(exception))


    async def update(self, channel, text, timestamp):
        """ Similar to say, but updates an existing message """
        try:
            await self._api_call(
                "chat.update",
                {'channel': channel, 'text': text, 'ts': timestamp, 'as_user': True}
            )

        except Exception as exception:
            print("Encountered error sending chat.update: {0}".format(exception))


    async def _get_identity(self):
        """ Gets connection identity information and stores it to the slack object """
        identity = await self._api_call("auth.test")

        if 'ok' not in identity or not identity['ok']:
            print("Couldn't get good identity string. Raw response: {0}".format(identity))
        else:
            self.team.update(name=identity['team'], id=identity['team_id'])
            self.user.update(name=identity['user'], id=identity['user_id'])


    async def _api_call(self, target, data=None):
        # Add our bot token along with any payload
        form = aiohttp.FormData(data or {})
        form.add_field('token', BOT_TOKEN)

        # Loop until we can send the message (to account for rate limiting)
        while True:
            async with GLOBAL['socket'].post('https://slack.com/api/{0}'.format(target), data=form) as response:
                # Process the response
                if response.status == 200:
                    return await response.json()

                elif response.status == 404:
                    raise Exception("Received 404 (not found) error for https://slack.com/api/{0}".format(target))

                elif response.status == 429:
                    print("Received 'Too Many Requests' warning from Slack, sleeping for 5 seconds...")
                    await asyncio.sleep(5)

                else:
                    raise Exception("Received unknown API response: {0}".format(response.status))
