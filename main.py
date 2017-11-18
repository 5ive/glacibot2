import asyncio, os, time
import slack, manager, env, config

env.birth = time.time()

env.manager = manager.Manager()
env.slack = slack.Slack(config.BOT_TOKEN)

env.manager.Rescan()

loop = asyncio.get_event_loop()
loop.set_debug(True)

asyncio.ensure_future(env.slack.Connect(loop))

loop.run_forever()
