from typing import Callable
from uuid import UUID
import openai
import aiohttp
import backoff
from decouple import config

from prompt import get_chat_messages

EXAMPLE_NAME: str = "June"
OPENAI_MODEL: str = "gpt-3.5-turbo"
MAX_TOKENS: int = 100
TEMPERATURE: float = 1.0  # default


class SimpleChatBridge:
    def __init__(
        self,
        uuid: UUID,
        on_response: Callable,
        on_error_response: Callable,
        model: str = OPENAI_MODEL,
        max_tokens: int = MAX_TOKENS,
        temperature: float = TEMPERATURE,
    ) -> None:
        self.uuid = uuid
        self.on_response = on_response
        self.on_error_response = on_error_response
        self._messages = []
        self._key = config("OPENAI_KEY")
        self.openai_model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        openai.api_key = config("OPENAI_KEY")  # TODO

        if not isinstance(self.api_key, str):
            raise Exception("OpenAI api key unknown.")

    def generate_messages(self, input: str, name: str = EXAMPLE_NAME) -> None:
        messages = get_chat_messages(name, input)
        self._messages = messages

    @property
    def api_key(self) -> str | None:
        return self._key

    def clear_messages(self) -> None:
        if self._messages:
            self._messages = []

    async def send_chat(self) -> None:
        full_message = ""
        openai.aiosession.set(aiohttp.ClientSession())

        chat_response = await self.chat_completion(
            model=self.openai_model,
            messages=self._messages,
            stream=True,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        if chat_response is None:
            await openai.aiosession.get().close()
            return

        await self.on_response("", "start")

        async for chunk in chat_response:
            if bool(chunk.choices[0].delta) == False:
                await self.on_response("", "stop")

            if hasattr(chunk.choices[0].delta, "content"):
                mess = chunk.choices[0].delta.content
                full_message += mess
                await self.on_response(mess, "streaming")

        print(f"\nFull message: {full_message}")
        await openai.aiosession.get().close()
        self.clear_messages()
        print("message stream sent.")

    @backoff.on_exception(backoff.expo, openai.error.RateLimitError)
    async def chat_completion(self, **kwargs):
        try:
            chat = await openai.ChatCompletion.acreate(**kwargs)
            return chat

        except openai.error.InvalidRequestError as e:
            print(f"There's a problem processing: {e}")
            await self.on_error_response(f"There's a problem processin: {e}")
            pass

        except openai.error.RateLimitError as e:
            print(f"{e}")
            await self.on_error_response(
                "We are reaching the limit of the number of requests we can serve. Please bear with us or try again later."
            )
            pass

        except openai.error.APIError as e:
            # Handle API error here, e.g. retry or log
            print(f"OpenAI API returned an API Error: {e}")
            await self.on_error_response(f"OpenAI API returned an API Error: {e}")
            pass

        except openai.error.APIConnectionError as e:
            # Handle connection error here
            print(f"Failed to connect to OpenAI API: {e}")
            await self.on_error_response(f"Failed to connect to OpenAI API: {e}")
            pass
