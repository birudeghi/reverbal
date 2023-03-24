import json
import uuid
import asyncio
import websockets
from websockets.server import WebSocketServerProtocol
from SimpleChatBridge import SimpleChatBridge

HTTP_SERVER_PORT = 8080


async def respond(ws: WebSocketServerProtocol):
    async def on_chat_response(data: str, streaming_status: str) -> None:
        resObject = {"text": data, "stream": streaming_status}
        res = json.dumps(resObject)
        await ws.send(res)

    async def on_error_response(text: str) -> None:
        resObject = {"error": text}
        res = json.dumps(resObject)
        await ws.send(res)

    new_uuid = uuid.uuid4()

    print("WS connection opened")
    chatBridge = SimpleChatBridge(new_uuid, on_chat_response, on_error_response)

    async for message in ws:
        data = json.loads(message)

        if data.get("event") is None:
            error_msg = {
                "error": "Invalid object. Refer to our documentation for more details."
            }
            msg = json.dumps(error_msg)
            await ws.send(msg)
            continue

        if data["event"] == "text":
            chatBridge.generate_messages(data["text"])
            await chatBridge.send_chat()

    print("WS connection closed")


async def main(port: int = HTTP_SERVER_PORT) -> None:
    async with websockets.serve(respond, None, port):
        print(f"server listening on: http://localhost:{port}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
