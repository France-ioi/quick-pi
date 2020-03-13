#!/usr/bin/python3

import asyncio, websockets, sys

async def relay_ws(ws_from, ws_to):
    # Relay messages received from a WS to a WS
    try:
        while True:
            msg = await ws_from.recv()
            await ws_to.send(msg)
    except:
        pass

async def make_relay(local_uri, remote_uri):
    while True:
        try:
            # Connect to relay server
            remote_ws = await websockets.connect(remote_uri)

            print("Connected to remote : %s" % remote_uri)

            # Wait for first message
            msg = await remote_ws.recv()

            # Connect to local server on first message
            local_ws = await websockets.connect(local_uri)
            print("Connected to local : %s" % local_uri)

            # Send first message
            await local_ws.send(msg)

            print("First message exchanged, starting relay...")

            # Set up relaying
            ltr_task = asyncio.create_task(relay_ws(local_ws, remote_ws))
            rtl_task = asyncio.create_task(relay_ws(remote_ws, local_ws))

            # Wait for tasks to finish
            await ltr_task
            await rtl_task
        except Exception as err:
            print("error: ", str(err))

        print("Cleaning up...")

        # Clean up
        local_ws = None
        remote_ws = None

        # Retry after 10 seconds
        await asyncio.sleep(10)


if len(sys.argv) >= 2:
	code = sys.argv[1]
	local_uri = "ws://localhost:5000/api/v1/commands"
	remote_uri = "ws://api.quick-pi.org/server/%s/" % code

	asyncio.get_event_loop().run_until_complete(make_relay(local_uri, remote_uri))
else:
	print("Provide the code name as a parameter")
