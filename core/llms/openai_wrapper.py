import os
from openai import AsyncOpenAI as OpenAI
from openai import RateLimitError
import asyncio


base_url = os.environ.get('LLM_API_BASE', "")
token = os.environ.get('LLM_API_KEY', "")

if not base_url and not token:
    raise ValueError("LLM_API_BASE or LLM_API_KEY must be set")
elif base_url and not token:
    client = OpenAI(base_url=base_url, api_key="not_use")
elif not base_url and token:
    client = OpenAI(api_key=token)
else:
    client = OpenAI(api_key=token, base_url=base_url)

llm_lock = asyncio.Lock()

async def openai_llm(messages: list, model: str, logger=None, **kwargs) -> str:
    if logger:
        logger.debug(f'messages:\n {messages}')
        logger.debug(f'model: {model}')
        logger.debug(f'kwargs:\n {kwargs}')

    async with llm_lock:
        try:
            response = await client.chat.completions.create(messages=messages, model=model, **kwargs)
        except RateLimitError as e:
            logger.warning(f'{e}\nRetrying in 60 second...')
            await asyncio.sleep(60)
            response = await client.chat.completions.create(messages=messages, model=model, **kwargs)
            if response.status_code == 200 and response.choices:
                return response.choices[0].message.content
            else:
                logger.error(f'after many try, llm error: {response}')
                return ""
        except Exception as e:
            if logger:
                logger.error(f'openai_llm error: {e}')
            return ''

    if logger:
        logger.debug(f'result:\n {response.choices[0]}')
        logger.debug(f'usage:\n {response.usage}')

    return response.choices[0].message.content
