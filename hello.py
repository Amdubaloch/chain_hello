import os
import chainlit as cl
from dotenv import find_dotenv, load_dotenv
from agents import Agent, RunConfig, AsyncOpenAI, OpenAIChatCompletionsModel, Runner
import json
from datetime import datetime

load_dotenv(find_dotenv())

# 🔑 Load providers from .env
providers = {
    "japanese": AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=os.getenv("GEMINI_API_BASE_URL")
    ),
    "english": AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=os.getenv("GEMINI_API_BASE_URL")
    ),
    "roman_urdu": AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=os.getenv("GEMINI_API_BASE_URL")
    ),
}

# 🧠 Models per provider
models = {
    "japanese": OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=providers["japanese"]),
    "english": OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=providers["english"]),
    "roman_urdu": OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=providers["roman_urdu"]),
}

# ✅ Define run configs
run_configs = {
    key: RunConfig(model=models[key], model_provider=providers[key], tracing_disabled=True)
    for key in models
}
agents = {
    "japanese": Agent(
        instructions="You are a Japanese language assistant. Answer everything in Japanese.",
        name="日本語アシスタント"
    ),
    "english": Agent(
        instructions="You are an English language assistant. Answer in formal but clear English.",
        name="English Assistant"
    ),
    "roman_urdu": Agent(
        instructions="Tum Roman Urdu mein jawab do, casual aur friendly tone mein.",
        name="Roman Urdu Dost"
    ),
}

agents = {
    "japanese": Agent(
        instructions="You are a Japanese language assistant. Answer everything in Japanese.",
        name="日本語アシスタント"
    ),
    "english": Agent(
        instructions="You are an English language assistant. Answer in formal but clear English.",
        name="English Assistant"
    ),
    "roman_urdu": Agent(
        instructions="Tum Roman Urdu mein jawab do, casual aur friendly tone mein.",
        name="Roman Urdu Dost"
    ),
}
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(label="Talk in Japanese", message="__select_agent__:japanese", icon="/public/japan.svg"),
        cl.Starter(label="Speak in English", message="__select_agent__:english", icon="/public/uk.svg"),
        cl.Starter(label="Roman Urdu Chitchat", message="__select_agent__:roman_urdu", icon="/public/urdu.svg"),
    ]


@cl.on_chat_start
async def handle_chat_start():
    cl.user_session.set("user_id", "admin")

    # Load history
    if not cl.user_session.get("history"):
        try:
            with open("chat_history_admin.json", "r") as f:
                history = json.load(f)
                cl.user_session.set("history", history)
        except FileNotFoundError:
            cl.user_session.set("history", [])

    # Set default agent
    if not cl.user_session.get("agent_key"):
        cl.user_session.set("agent_key", "developer")

@cl.on_chat_end
async def save_history():
    history = cl.user_session.get("history", [])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"chat_history_{timestamp}.json", "w") as f:
        json.dump(history, f, indent=2)

@cl.on_message
async def handle_message(message: cl.Message):
    if message.content.startswith("__select_agent__:"):
        key = message.content.split(":")[1]
        cl.user_session.set("agent_key", key)
        await cl.Message(content=f"✅ Agent **{key}** selected! Ab aap message likh saktay hain.").send()
        return

    agent_key = cl.user_session.get("agent_key", "developer")
    selected_agent = agents.get(agent_key)
    history = cl.user_session.get("history", [])
    history.append({"role": "user", "content": message.content})

    # ✨ Language agents use their own RunConfig
    if agent_key in run_configs:
        config = run_configs[agent_key]
    else:
        config = RunConfig(model=models["english"], model_provider=providers["english"], tracing_disabled=True)

    result = await Runner.run(
        selected_agent,
        input=history,
        run_config=config,
    )

    history.append({"role": "assistant", "content": result.final_output})
    cl.user_session.set("history", history)
    await cl.Message(content=result.final_output).send()
