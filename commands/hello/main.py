
async def run(message):
    if message['type'] != 'message' or 'subtype' in message:
        return

    print("<{0}> {1}".format(message['user'], message['text']))
