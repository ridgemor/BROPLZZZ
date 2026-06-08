import re
import discord
import os
from dotenv import load_dotenv
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set")
 
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

#Basic URL regex
URL_PATTERN = re.compile(r"https?://\S+")

#Optional: game-related domains
GAME_DOMAINS = {
    "store.steampowered.com",
    "steamcommunity.com",
    "epicgames.com",
    "roblox.com",
    "minecraft.net",
    "itch.io",
    }
bro_count = 0

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"BRO counter: {bro_count}")

@bot.event
async def on_message(message):
    global bro_count

    if message.author.bot:
        return

    urls = URL_PATTERN.findall(message.content)

    for url in urls:
        if any(domain in url.lower() for domain in GAME_DOMAINS):
            bro_count += 1
            await message.channel.send(f"BRO PLEASEEEEE\n\nShit games recommended so far: {bro_count}")
            break

    await bot.process_commands(message)
bot.run(TOKEN)