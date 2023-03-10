import base64
import json
import logging
import threading

from flask import Flask
from flask_sock import Sock

from ChatClientBridge import ChatClientBridge
from WhisperClientBridge import WhisperClientBridge

app = Flask(__name__)
sockets = Sock(app)

HTTP_SERVER_PORT = 8000

@sockets.route('/media')
def transcribe(ws):

    def on_transcription_response(data):
        chatBridge.add_request(data)

    def on_chat_response(data):
        resObject = {
            "text": data 
        }
        res = json.dumps(resObject)
        ws.send()

    print("WS connection opened")
    chatBridge = ChatClientBridge(5, on_chat_response)
    whisperBridge = WhisperClientBridge(2, on_transcription_response)
    print("Bridges instantiated")
    t_whisper = threading.Thread(target=whisperBridge.start)
    t_chat = threading.Thread(target=chatBridge.start)
    t_whisper.start()
    t_chat.start()
    print("Bridges started")

    while True:
        message = ws.receive()
        print("Message received")
        if message is None:
            whisperBridge.add_request(None)
            whisperBridge.terminate()
            chatBridge.terminate()
            break

        data = json.loads(message)
        if data["event"] == "prompt":
            print(f"Media WS: Received event '{data['event']}': {message}")
            chatBridge.add_prompt(data["prompt"])
            continue
        if data["event"] == "media":
            media = data["media"]
            chunk = base64.b64decode(media["payload"])
            whisperBridge.add_request(chunk)
        if data["event"] == "stop":
            print(f"Media WS: Received event 'stop': {message}")
            print("Stopping...")
            break

    whisperBridge.terminate()
    chatBridge.terminate() # it terminates, and then sends the audio as this is when the generator stops
    print("WS connection closed")


if __name__ == '__main__':

    app.logger.setLevel(logging.DEBUG)
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(('', HTTP_SERVER_PORT), app, handler_class=WebSocketHandler)
    print("Server listening on: http://localhost:" + str(HTTP_SERVER_PORT))
    server.serve_forever()
