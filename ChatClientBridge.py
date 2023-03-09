import queue
import sched, time
from decouple import config
import openai

class ChatClientBridge:
    def __init__(self, cadence, on_response):
        self.on_response = on_response
        self._queue = queue.Queue()
        self._openai = openai
        self._ended = False
        self._prompt = ""
        self.cadence = cadence
        openai.api_key = config("OPENAI_KEY")

    # def scheduled_start(self):
    #     my_scheduler = sched.scheduler(time.time, time.sleep)
    #     my_scheduler.enter(self.cadence, 1, self.start, (my_scheduler,))
    #     my_scheduler.run()
    
    def start(self):
        # scheduler.enter(self.cadence, 1, self.start, (scheduler,))
        stream = self.generator() #the same but for string
        text = ""
        for content in stream:
            text.join(content)
        ## Create message structure here (prompt + message)
        message = self._prompt + text
        chat_response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": message}])
        self.on_response(chat_response.choices[0].message.content)
    
    def terminate(self):
        self._ended = True
    
    def add_request(self, chars):
        self._queue.put(chars, block=False)

    def add_prompt(self, text):
        self._prompt = text
    
    def generator(self):
        while not self._ended:
            chunk = self._queue.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._queue.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)