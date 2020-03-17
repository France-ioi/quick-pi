#!/usr/bin/python3

import websocket, sys, threading, time

LOCAL_WS = None
REMOTE_WS = None
HTTP_PROXY = None

def get_ws_args():
    # Get args for the websocket creation
    global HTTP_PROXY
    args = {"on_message": on_message, "on_error": on_error, "on_close": on_close}
    if HTTP_PROXY is not None:
        args['http_proxy_host'] = HTTP_PROXY['host']
        args['http_proxy_port'] = HTTP_PROXY['port']
    return args

def start():
    # Start remote websocket
    global REMOTE_WS, REMOTE_URI, LOCAL_WS, LOCAL_URI

    args = get_ws_args()
    if REMOTE_WS is None:
        REMOTE_WS = websocket.WebSocketApp(REMOTE_URI, **args)
        remote_t = threading.Thread(target=REMOTE_WS.run_forever)
        remote_t.start()
        print("Started remote websocket")

    if LOCAL_WS is None:
        LOCAL_WS = websocket.WebSocketApp(LOCAL_URI, **args)
        local_t = threading.Thread(target=LOCAL_WS.run_forever)
        local_t.start()
        print("Started local websocket")

def on_message(ws, message):
    # Received message on a websocket
    global LOCAL_WS, REMOTE_WS
    if ws is LOCAL_WS:
        target_ws = REMOTE_WS
        source = "local"
    else:
        target_ws = LOCAL_WS
        if target_ws is None:
            target_ws = start_local()
        source = "remote"

    print("Received message from %s" % source)
    if target_ws is not None:
        target_ws.send(message)
    else:
        print("Error (%s) : target WS is None, received message `%s`" % (source, message))

def on_error(ws, error):
    # Received error on a websocket
    global LOCAL_WS, REMOTE_WS
    source = "local" if ws is LOCAL_WS else "remote"
    print("Error (%s) : %s" % (source, error))

def on_close(ws):
    # A websocket is closing
    global LOCAL_WS, REMOTE_WS
    print("Closing")
    if ws is LOCAL_WS and REMOTE_WS is not None:
        REMOTE_WS.close()
    elif LOCAL_WS is not None:
        LOCAL_WS.close()
    LOCAL_WS = None
    REMOTE_WS = None

    time.sleep(1)

    start()


if len(sys.argv) >= 2:
    code = sys.argv[1]
    LOCAL_URI = "ws://localhost:5000/api/v1/commands"
    REMOTE_URI = "ws://api.quick-pi.org/server/%s/" % code

    start()
else:
    print("Provide the code name as a parameter")
