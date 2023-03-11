import openai
import queue
import soundfile as sf
from decouple import config

class SimpleChatBridge:
    def __init__(self):
        self._queue = queue.Queue()
        self._ended = False
        self._prompt = ""
        openai.api_key = config("OPENAI_KEY")
    
    def _init(self, on_response):
        self.on_response = on_response

    def add_prompt(self, prompt):
        self._prompt = prompt

    def add_input(self, buffer):
        print("Add input")
        self._queue.put(bytes(buffer), block=False)

    async def send(self):
        stream = self.audio_generator()
        bytes = b''
        for content in stream:
            print("generator working: ", content)
            bytes += content
        with sf.SoundFile("whisper.wav", "w", 14400, 1) as f:
            f.buffer_write(bytes, 'float64')
        print("Audio file created")
        f = open("whisper.wav", "rb")
        whisper_transcript = openai.Audio.transcribe(model="whisper-1", file=f)
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