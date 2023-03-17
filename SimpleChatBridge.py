import os
import openai
import queue
import aiohttp
import backoff
from pydub import AudioSegment
from decouple import config

class SimpleChatBridge:
    def __init__(self, uuid):
        self._queue = queue.Queue()
        self._ended = False
        self.uuid = uuid
        self._filename = "whisper_" + str(self.uuid) + ".wav"
        self._prompt = ""
        self._messages = []
        self._key = config("OPENAI_KEY")
        openai.api_key = config("OPENAI_KEY")
    
    def _init(self, on_response, on_error_response):
        self.on_response = on_response
        self.on_error_response = on_error_response

    def add_prompt(self, prompt):
        self._prompt = prompt
        self._messages.append({"role": "system", "content": self._prompt})

    def add_input(self, buffer):
        self._queue.put(bytes(buffer), block=False)

    def get_key(self):
        return self._key

    def clear_audio(self):
        if os.path.exists(self._filename):
            os.remove(self._filename)

    async def send(self):
        stream = self.audio_generator()
        segment = AudioSegment.empty()
        if stream is None:
            print("empty stream")
            return
        
        for content in stream:
            new_seg = AudioSegment(content, sample_width=2, frame_rate=44100, channels=1)
            segment += new_seg
        segment.export(self._filename, format="wav")
        print("Audio file created")
        
        file = open(self._filename, "r+b")

        openai.aiosession.set(aiohttp.ClientSession())
        
        whisper_transcript = await self.audio_transcribe(model="whisper-1", file=file)
        
        if whisper_transcript is None:
            await openai.aiosession.get().close()
            return
        
        message = whisper_transcript.text
        self._messages.append({"role": "user", "content": message})
        print("chatGPT message: " + message)

        chat_response = await self.chat_completion(model="gpt-3.5-turbo", messages=self._messages, stream=True)
        
        if chat_response is None:
            await openai.aiosession.get().close()
            return
        
        ass_message = ""
        await self.on_response("", "start")

        async for chunk in chat_response:
            if bool(chunk.choices[0].delta) == False:
                await self.on_response("", "stop")
                
            if hasattr(chunk.choices[0].delta, "content"):
                mess = chunk.choices[0].delta.content
                ass_message += mess
                await self.on_response(mess, "streaming")

        self._messages.append({"role": "assistant", "content": ass_message})
        await openai.aiosession.get().close()
        print("message stream sent.")
    
    @backoff.on_exception(backoff.expo, openai.error.RateLimitError)
    async def audio_transcribe(self, **kwargs):
        try:
            whisper_transcript = await openai.Audio.atranscribe(**kwargs)
            return whisper_transcript
        
        except openai.error.InvalidRequestError as e:
            print(f"There's a problem processing the audio: {e}")
            await self.on_error_response(f"There's a problem processing the audio: {e}")
            pass

        except openai.error.RateLimitError as e:
            print(f"{e}")
            await self.on_error_response("We are reaching the limit of the number of requests we can serve. Please bear with us or try again later.")
            pass

        except openai.error.APIError as e:
            #Handle API error here, e.g. retry or log
            print(f"OpenAI API returned an API Error: {e}")
            await self.on_error_response(f"OpenAI API returned an API Error: {e}")
            pass

        except openai.error.APIConnectionError as e:
            #Handle connection error here
            print(f"Failed to connect to OpenAI API: {e}")
            await self.on_error_response(f"Failed to connect to OpenAI API: {e}")
            pass
    
    @backoff.on_exception(backoff.expo, openai.error.RateLimitError)
    async def chat_completion(self, **kwargs):
        try:
            chat = await openai.ChatCompletion.acreate(**kwargs)
            return chat
        
        except openai.error.InvalidRequestError as e:
            print(f"There's a problem processing the audio: {e}")
            await self.on_error_response(f"There's a problem processing the audio: {e}")
            pass

        except openai.error.RateLimitError as e:
            print(f"{e}")
            await self.on_error_response("We are reaching the limit of the number of requests we can serve. Please bear with us or try again later.")
            pass

        except openai.error.APIError as e:
            #Handle API error here, e.g. retry or log
            print(f"OpenAI API returned an API Error: {e}")
            await self.on_error_response(f"OpenAI API returned an API Error: {e}")
            pass

        except openai.error.APIConnectionError as e:
            #Handle connection error here
            print(f"Failed to connect to OpenAI API: {e}")
            await self.on_error_response(f"Failed to connect to OpenAI API: {e}")
            pass

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