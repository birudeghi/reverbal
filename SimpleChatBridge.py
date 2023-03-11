import openai
from decouple import config

class SimpleChatBridge:
    def __init__(self, on_response):

        self.on_response = on_response
        self._input = ""
        self._ended = False
        self._prompt = ""
        openai.api_key = config("OPENAI_KEY")

    async def send(self):

        message = self._prompt + self.input
        print("chatGPT message: " + message)
        chat_response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": message}])
        await self.on_response(chat_response.choices[0].message.content)
    
    