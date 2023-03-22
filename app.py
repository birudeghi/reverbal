import base64
import json
import uuid
import asyncio
import websockets
from SimpleChatBridge import SimpleChatBridge

HTTP_SERVER_PORT = 8080


def create_chat_response(on_response, on_error_response, uuid):
    bridge = SimpleChatBridge(uuid)
    bridge._init(on_response, on_error_response)

    if not isinstance(bridge.get_key(), str):
        print("OpenAI api key unknown.")
        raise

    return bridge


async def transcribe(ws):

    new_uuid = uuid.uuid4()

    async def on_chat_response(data, streaming_status):
        resObject = {"text": data, "stream": streaming_status}
        res = json.dumps(resObject)
        await ws.send(res)

    async def on_error_response(text):
        resObject = {"error": text}
        res = json.dumps(resObject)
        await ws.send(res)

    print("WS connection opened")
    chatBridge = create_chat_response(on_chat_response, on_error_response, new_uuid)

    async for message in ws:
        if message is None:
            chatBridge.add_input(None)

        data = json.loads(message)

        if data.get("event") is None:
            error_msg = {
                "error": "Invalid object. Refer to our documentation for more details."
            }
            msg = json.dumps(error_msg)
            await ws.send(msg)
            continue

        if data["event"] == "prompt":
            print(f"Media WS: Received event '{data['event']}': {message}")
            chatBridge.add_prompt(data["prompt"])
            continue

        if data["event"] == "media":
            chunk = base64.b64decode(data["media"])
            chatBridge.add_input(chunk)

        if data["event"] == "break":
            await chatBridge.send()

        if data["event"] == "text":
            chatBridge.generate_messages(data["text"])
            await chatBridge.send_chat()

        if data["event"] == "stop":
            await chatBridge.send()
            print("Stopping...")
            break
    chatBridge.clear_audio()
    print("WS connection closed")


async def main():
    async with websockets.serve(transcribe, None, HTTP_SERVER_PORT):
        print("server listening on: http://localhost:" + str(HTTP_SERVER_PORT))
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
