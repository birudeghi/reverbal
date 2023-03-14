import os
import openai
import queue
from aiohttp import ClientSession
import requests
import soundfile as sf
from decouple import config

class SimpleChatBridge:
    def __init__(self):
        self._queue = queue.Queue()
        self._ended = False
        self._prompt = ""
        self._key = config("OPENAI_KEY")
        openai.api_key = config("OPENAI_KEY")
    
    def _init(self, on_response, on_error_response):
        self.on_response = on_response
        self.on_error_response = on_error_response

    def add_prompt(self, prompt):
        self._prompt = prompt

    def add_input(self, buffer):
        self._queue.put(bytes(buffer), block=False)

    def clear(self):
        with self._queue.mutex:
            self._queue.queue.clear()

    async def send(self):
        stream = self.audio_generator()
        bytes = b''
        if stream is None:
            print("empty stream")
            return
        for content in stream:
            bytes += content

        with open("whisper.webm", "w+b") as f:
            print("bytes to write: ", bytes[:50])
            f.write(bytes)
            print("Audio file created")

        file = open("whisper.webm", "r+b")
        openai.aiosession.set(ClientSession())
        # try:
        whisper_transcript = await openai.Audio.atranscribe(model="whisper-1", file=file, language="en")
        # except openai.InvalidRequestError:
        #     await self.on_error_response("There's a problem processing the audio.")
        #     return
        message = self._prompt + whisper_transcript.text
        print("chatGPT message: " + message)
        chat_response = await openai.ChatCompletion.acreate(model="gpt-3.5-turbo", messages=[{"role": "user", "content": message}])
        await openai.aiosession.get().close()
        await self.on_response(chat_response.choices[0].message.content)
        print("message sent")

    
    
    def audio_generator(self):
        # Use a blocking get() to ensure there's at least one chunk of
        # data, and stop iteration if the chunk is None, indicating the
        # end of the audio stream.
        chunk = self._queue.get()
        if chunk is None:
            return
        data = [chunk]

        # Now consume whatever other data's still buffered.
        while True:
            try:
                chunk = self._queue.get(block=False)
                if chunk is None:
                    return
                data.append(chunk)
            except queue.Empty:
                break

        return data