import base64
import json
import asyncio
import websockets

from SimpleChatBridge import SimpleChatBridge
from WhisperClientBridge import WhisperClientBridge

HTTP_SERVER_PORT = 8000

def create_chat_response(on_response):
    bridge = SimpleChatBridge()
    bridge._init(on_response)
    return bridge

async def transcribe(ws):

    async def on_chat_response(data):
        resObject = {
            "text": data 
        }
        res = json.dumps(resObject)
        await ws.send(res)

    print("WS connection opened")
    chatBridge = create_chat_response(on_chat_response)
    async for message in ws:
        if message is None:
            chatBridge.add_input(None)
            chatBridge.terminate()

        data = json.loads(message)
        if data["event"] == "prompt":
            print(f"Media WS: Received event '{data['event']}': {message}")
            chatBridge.add_prompt(data["prompt"])
            continue

        if data["event"] == "media":
            chunk = base64.b64decode(data["media"])
            chatBridge.add_input(chunk)

        if data["event"] == "break":
            await chatBridge.send()
        if data["event"] == "stop":
            print(f"Media WS: Received event 'stop': {message}")
            print("Stopping...")
            break

    
    await chatBridge.send()
    print("WS connection closed")

async def main():
    async with websockets.serve(transcribe, "localhost", HTTP_SERVER_PORT):
        print("server listening on: http://localhost:" + str(HTTP_SERVER_PORT))
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())