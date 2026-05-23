import os
import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

def ask_ai(prompt):

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "deepseek/deepseek-chat:free",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
    )

    data = response.json()

    print(data)

    return data["choices"][0]["message"]["content"]

@bot.event
async def on_message(message):

    if message.author == bot.user:
        return

    if bot.user in message.mentions:

        user_message = message.content.replace(f"<@{bot.user.id}>", "").strip()

        if not user_message:
            await message.channel.send("你想问我什么呀？ 🤖")
            return

        await message.channel.send("思考中... 🤔")

        ai_response = ask_ai(user_message)

        await message.channel.send(ai_response)

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)