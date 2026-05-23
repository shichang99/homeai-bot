import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):

    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        await message.channel.send("你好呀～ 我是你的 AI 管家 🤖")

    await bot.process_commands(message)

bot.run(TOKEN)