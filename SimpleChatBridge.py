import os
import openai
import queue
import wave
import soundfile as sf
from decouple import config

class SimpleChatBridge:
    def __init__(self):
        self._queue = queue.Queue()
        self._ended = False
        self._prompt = ""
        openai.api_key = config("OPENAI_KEY")
    
    def _init(self, on_response, on_error_response):
        self.on_response = on_response
        self.on_error_response = on_error_response

    def add_prompt(self, prompt):
        self._prompt = prompt

    def add_input(self, buffer):
        print("Added input")
        self._queue.put(bytes(buffer), block=False)

    async def send(self):
        stream = self.audio_generator()
        bytes = b''
        for content in stream:
            bytes += content

        os.remove("whisper.wav")

        with sf.SoundFile("whisper.wav", "w", 44100, 1) as f:
            f.buffer_write(bytes, 'float64')
        print("Audio file created")

        with wave.open("whisper.wav", "rb") as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)

            if duration < 0.1:
                await self.on_error_response("Conversation duration too short.")
                return
            
        file = open("whisper.wav", "rb")
        whisper_transcript = openai.Audio.transcribe(model="whisper-1", file=file)
        message = self._prompt + whisper_transcript.text
        print("chatGPT message: " + message)
        chat_response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": message}])
        await self.on_response(chat_response.choices[0].message.content)
    
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