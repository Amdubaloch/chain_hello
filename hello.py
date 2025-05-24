import os
import chainlit as cl
from dotenv import find_dotenv, load_dotenv
from agents import Agent, RunConfig, AsyncOpenAI, OpenAIChatCompletionsModel, Runner

import json
from datetime import datetime

load_dotenv(find_dotenv())

gemini_api_key = os.getenv("GEMINI_API_KEY")

provider = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=provider,
)

run_config = RunConfig(
    model=model,
    model_provider=provider,
    tracing_disabled=True,
)

agent1 = Agent(
    instructions="You are a helpful assistant that can answer questions and help with tasks.",
    name="Assistant",
)

@cl.on_chat_start
async def hendle_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(content="Hello! How can I assist you today?").send()

@cl.on_chat_end
async def save_history():
    history = cl.user_session.get("history", [])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"chat_history_{timestamp}.json", "w") as f:
        json.dump(history, f, indent=2)


@cl.on_message
async def handle_message(message: cl.Message):
    history = cl.user_session.get("history")


    history.append({"role": "user", "content": message.content})
    result = await Runner.run(
    agent1,
    input=history,
    run_config=run_config,
    )
    history.append({"role": "assistant", "content": result.final_output})
    cl.user_session.set("history", history)
    await cl.Message(content=result.final_output).send()
