import base64
import json
import logging
import threading

from flask import Flask
from flask_sockets import Sockets

from ChatClientBridge import ChatClientBridge
from WhisperClientBridge import WhisperClientBridge

app = Flask(__name__)
sockets = Sockets(app)

HTTP_SERVER_PORT = 5000

def on_transcription_response(data):
    chatClientBridge.add_request(data)

def on_chat_response():
    

chatClientBridge = ChatClientBridge(5, on_chat_response)
whisperBridge = WhisperClientBridge(2, on_transcription_response)

t_whisper = threading.Thread(target=whisperBridge.scheduled_start)
t_chat = threading.Thread(target=chatClientBridge.scheduled_start)
t_whisper.start()
t_chat.start()

@sockets.route('/media')
def transcribe(ws):
    print("WS connection opened")
    

    while not ws.closed:
        message = ws.receive()
        if message is None:
            whisperBridge.add_request(None)
            whisperBridge.terminate()
            break

        data = json.loads(message)
        if data["event"] in ("connected", "start"):
            print(f"Media WS: Received event '{data['event']}': {message}")
            continue
        if data["event"] == "media":
            media = data["media"]
            chunk = base64.b64decode(media["payload"])
            whisperBridge.add_request(chunk)
        if data["event"] == "stop":
            print(f"Media WS: Received event 'stop': {message}")
            print("Stopping...")
            break

    whisperBridge.terminate() # it terminates, and then sends the audio as this is when the generator stops
    print("WS connection closed")


if __name__ == '__main__':
    app.logger.setLevel(logging.DEBUG)
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(('', HTTP_SERVER_PORT), app, handler_class=WebSocketHandler)
    print("Server listening on: http://localhost:" + str(HTTP_SERVER_PORT))
    server.serve_forever()
