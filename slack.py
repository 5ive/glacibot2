import asyncio, aiohttp, time, ctypes
from enum import Enum
import env

class Slack:
    class State(Enum):
        INACTIVE = 0
        CONNECTING = 1
        CONNECTED = 2
        DISCONNECTED = 3
        SHUTTING_DOWN = 4

    def __init__(self, token):
        self.token = token
        self.heartbeat_pending = False
        self.latency = []
        self.shutdown = False
        self.connected_at = 0
        self.active = False
        self.state = Slack.State.INACTIVE
        self.reconnects = 0

    async def _Heartbeat(self, interval):
        print("{0}s heartbeat is born".format(interval))

        while True:
            await asyncio.sleep(interval)

            if self.heartbeat_pending == True:
                print("Hit heartbeat timeout")
                return 1

            self.heartbeat_pending = True

            await self.socket.send_json({
                "type": "ping",
                "sent": time.time()
            })

    async def _Killswitch(self, interval):
        print ("{0}s killswitch engage(d)".format(interval))

        while True:
            await asyncio.sleep(interval)

            # Check if we've sent the kill signal to the main connection
            if self.state == Slack.State.SHUTTING_DOWN:
                print("Received termination signal")
                return 1

    async def _Listen(self):
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
                    round(time.time() - self.connected_at, 3)
                ))

                # Track the last 10 pings for historical tracking
                if len(self.latency) > 10:
                    self.latency.pop(0)

            else:
                print(message)
                # Give each custom command the input in its .run(data) method
                for command in env.manager.GetCommandList():
                    asyncio.ensure_future(command.run(message))

    async def Disconnect(self):
        self.state = Slack.State.SHUTTING_DOWN

    async def Connect(self, loop, reconnect=True):
        # Create the session to handle the connection
        # Should this be created outside of the scope of Slack?
        self.session = aiohttp.ClientSession(loop=loop)

        while reconnect and self.state != Slack.State.SHUTTING_DOWN:
            # Initialize async task variables
            task_heartbeat = None
            task_listen = None
            task_killswitch = None

            try:
                self.state = Slack.State.CONNECTING

                # Attempt to get a connection point from Slack web API
                print("Requesting RTM connection point")
                rtm = await self._ApiCall("rtm.start")

                # If we don't get a good response, just give up
                if 'ok' not in rtm or not rtm['ok']:
                    print("Couldn't get good RTM answer")
                    raise Exception("Failed to get Slack RTM endpoint.")

                # Attempt to open up a websocket to the RTM connection point
                print("Got RTM connect point: {0}".format(rtm['url']))
                self.socket = await self.session.ws_connect(rtm['url'])

                # Spin up the async tasks to interact with Slack RTM
                print("Starting up heartbeat")
                task_heartbeat = asyncio.ensure_future(self._Heartbeat(30))
                print("Starting up listener")
                task_listen = asyncio.ensure_future(self._Listen())
                print("AFTS armed")
                task_killswitch = asyncio.ensure_future(self._Killswitch(1))

                # If we get to this point, we've got a successful connection
                self.connected_at = time.time()
                self.heartbeat_pending = False
                self.reconnects = 0
                self.state = Slack.State.CONNECTED

                # Once we're here, wait until something returns (ie., closes)
                print("Healthy main loop sequence")
                await asyncio.wait(
                    [task_heartbeat, task_listen, task_killswitch],
                    return_when = asyncio.FIRST_COMPLETED
                )

                print("Broke out of healthy loop")

            except Exception as e:
                print("Broke unexpectedly out of unhealthy loop: {0}".format(e))

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

        print("Closing session")
        await self.session.close()

    async def _ApiCall(self, target, data=None):
        # Add our bot token along with any payload
        form = aiohttp.FormData(data or {})
        form.add_field('token', self.token)

        # Loop until we can send the message (to account for rate limiting)
        while True:
            async with self.session.post('https://slack.com/api/{0}'.format(target), data=form) as response:
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
