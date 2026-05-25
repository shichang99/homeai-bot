from email.mime import message
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

memory_collection = client.get_or_create_collection(
    name="user_memories"
)

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

def save_memory(user_name, memory_text):

    embedding = embedding_model.encode(memory_text).tolist()

    memory_collection.add(
        documents=[memory_text],
        embeddings=[embedding],
        ids=[f"{user_name}-{hash(memory_text)}"],
        metadatas=[{"user": user_name}]
    )

def search_knowledge(query):

    query_embedding = embedding_model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    documents = results["documents"][0]

    return "\n".join(documents)

def search_memory(user_name, query):

    query_embedding = embedding_model.encode(query).tolist()

    results = memory_collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        where={"user": user_name}
    )

    documents = results["documents"][0]

    return "\n".join(documents)

def ask_ai(user_name, prompt):

    knowledge = search_knowledge(prompt)
    memory = search_memory(user_name, prompt)

    full_prompt = f"""
    你是 Discord Server 的 AI 管家。

    你会记得用户长期记忆。

    规则：

    1. 优先根据记忆与知识库回答
    2. 不允许胡乱编造
    3. 回答自然
    4. 像真正 AI 助手

    用户长期记忆：
    {memory}

    知识库内容：
    {knowledge}

    用户问题：
    {prompt}
    """

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
                    "content": full_prompt
                }
            ]
        }
    )

    data = response.json()

    print(data)

    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    else:
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
    
    memory_keywords = [
        "我喜欢",
        "我是",
        "我的",
        "我最喜欢",
        "我讨厌",
        "我不喜欢",
        "I like",
        "I'm", 
        "I love",
        "I hate",
        "I dislike",
        "My favorite"
    ]

    if any(keyword in message.content for keyword in memory_keywords):

        save_memory(
            str(message.author),
            message.content
        )

        await message.add_reaction("🧠")

    # AI 聊天功能
    if bot.user in message.mentions:

        user_message = message.content.replace(f"<@{bot.user.id}>", "").strip()

        if not user_message:
            await message.channel.send("你想问我什么呀？ 🤖")
            return

        await message.channel.send("思考中... 🤔")

        ai_response = ask_ai(
            str(message.author),
            user_message
        )

        await message.channel.send(ai_response)

    await bot.process_commands(message)
    
bot.run(DISCORD_TOKEN)