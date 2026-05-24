import os
import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

client = chromadb.PersistentClient(path="./chroma")

collection = client.get_or_create_collection(
    name="knowledge_base"
)

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

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
            "model": "openrouter/free",
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

    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    else:
        print(data)
        return "AI 暂时无法回应 😢"

@bot.event
async def on_message(message):

    KNOWLEDGE_CHANNEL = "📝｜ai-知识库"

    # 自动学习知识库频道内容
    if message.channel.name == KNOWLEDGE_CHANNEL:

        text = message.content

        embedding = embedding_model.encode(text).tolist()

        collection.add(
            documents=[text],
            embeddings=[embedding],
            ids=[str(message.id)]
        )

        await message.add_reaction("📚")

    # 不回复自己
    if message.author == bot.user:
        return

    # AI 聊天功能
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