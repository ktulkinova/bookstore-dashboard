from google import genai
from google.genai import errors, types
import time

import tools
MODEL = 'gemini-3.6-flash'

RULES = """You are an assistant for a dashboard of 5 book stores (STORE1 - STORE5).
Answer questions about the data only with the help of the tools.
Never calculate or guess numbers yourself, take them from the tools.
If the user does not say which store, use {store} (it is selected in the dashboard).
If it is "All stores", call the tools for every store (STORE1 - STORE5), then combine or compare
the results and say which store each result is from.
Money is in USD. Dates are YYYY-MM-DD. Data is from 2024-11 to 2026-09.
If the tools can not answer the question, say that you don't know.
Answer short, in the language of the question."""


def new_client(api_key):
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30000))


def new_chat(client, store):
    config = types.GenerateContentConfig(
        system_instruction=RULES.format(store=store),
        tools=tools.ALL_TOOLS,
    )
    return client.chats.create(model=MODEL, config=config)


def ask(chat, question):
    for attempt in range(3):
        try:
            answer = chat.send_message(question).text
            return answer or 'Sorry, I could not answer'
        except errors.ServerError:
            if attempt == 2:
                raise
            time.sleep(3)
