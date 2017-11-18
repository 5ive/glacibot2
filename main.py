""" Bootstrap the environment and handle the event loop. """

import asyncio
import time
import aiohttp
import manager
from env import MODULES, UTILS, STATS, GLOBAL

STATS['birth'] = time.time()

# Bootstrap the module manager
UTILS['manager'] = manager.load('manager')
del manager

# Load the slack class in via module manager
MODULES['slack'] = UTILS['manager'].load('slack')
UTILS['slack'] = MODULES['slack'].Slack()

# Load any custom commands that are present
UTILS['manager'].scan()

# Create the main event loop and socket
GLOBAL['loop'] = asyncio.get_event_loop()
GLOBAL['loop'].set_debug(True)
GLOBAL['socket'] = aiohttp.ClientSession(loop=GLOBAL['loop'])

# Start off by connecting to slack
asyncio.ensure_future(UTILS['slack'].start())

# Kick off the main event loop
GLOBAL['loop'].run_forever()
