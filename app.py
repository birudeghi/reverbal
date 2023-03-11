import base64
import json
import threading

import asyncio
import websockets

from SimpleChatBridge import SimpleChatBridge
from WhisperClientBridge import WhisperClientBridge

HTTP_SERVER_PORT = 8000

async def transcribe(ws):
    def on_transcription_response(data):
        chatBridge.add_request(data)

    async def on_chat_response(data):
        resObject = {
            "text": data 
        }
        res = json.dumps(resObject)
        await ws.send()

    print("WS connection opened")
    chatBridge = SimpleChatBridge(5, await on_chat_response)
    whisperBridge = WhisperClientBridge(2, on_transcription_response)

    t_whisper = threading.Thread(target=whisperBridge.start)
    t_whisper.start()
    print('whisperBridge started')
    async for message in ws:

        print("Message received")
        if message is None:
            whisperBridge.add_request(None)
            whisperBridge.terminate()
            chatBridge.terminate()

        data = json.loads(message)
        if data["event"] == "prompt":
            print(f"Media WS: Received event '{data['event']}': {message}")
            chatBridge.add_prompt(data["prompt"])
            continue

        if data["event"] == "media":
            chunk = base64.b64decode(data["media"])
            whisperBridge.add_request(chunk)
        if data["event"] == "stop":
            print(f"Media WS: Received event 'stop': {message}")
            print("Stopping...")
            break

    whisperBridge.terminate()
    chatBridge.terminate() # it terminates, and then sends the audio as this is when the generator stops
    print("WS connection closed")

async def main():
    async with websockets.serve(transcribe, "localhost", HTTP_SERVER_PORT):
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())