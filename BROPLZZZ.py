import os
import re
import sqlite3
from urllib.parse import urlparse

import discord
from dotenv import load_dotenv
from discord.ext import commands

# ----------------------------
# ENVIRONMENT
# ----------------------------

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set")

# ----------------------------
# DISCORD SETUP
# ----------------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------
# URL DETECTION
# ----------------------------

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")

GAME_DOMAINS = {
    "store.steampowered.com",
    "steamcommunity.com",
    "epicgames.com",
    "roblox.com",
    "minecraft.net",
    "itch.io",
}

# ----------------------------
# DATABASE
# ----------------------------

conn = sqlite3.connect("brotracker.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    game_url TEXT NOT NULL UNIQUE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# ----------------------------
# DATABASE HELPERS
# ----------------------------

def add_recommendation(user, url):
    try:
        cursor.execute("""
            INSERT INTO recommendations
            (user_id, username, game_url)
            VALUES (?, ?, ?)
        """, (
            user.id,
            str(user),
            url
        ))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False


def get_total_count():
    cursor.execute("""
        SELECT COUNT(*)
        FROM recommendations
    """)
    return cursor.fetchone()[0]


def get_user_count(user_id):
    cursor.execute("""
        SELECT COUNT(*)
        FROM recommendations
        WHERE user_id = ?
    """, (user_id,))

    return cursor.fetchone()[0]


def get_leader():
    cursor.execute("""
        SELECT user_id, username, COUNT(*) as total
        FROM recommendations
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT 1
    """)

    return cursor.fetchone()


# ----------------------------
# EVENTS
# ----------------------------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Tracked games: {get_total_count()}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    urls = URL_PATTERN.findall(message.content)

    for url in urls:

        domain = urlparse(url).netloc.lower()

        is_game_link = any(
            domain == game_domain or
            domain.endswith("." + game_domain)
            for game_domain in GAME_DOMAINS
        )

        if not is_game_link:
            continue

        old_leader = get_leader()

        added = add_recommendation(
            message.author,
            url
        )

        if not added:
            await message.channel.send(
                "This pile of shit has already been recommended, BRO PLEASEEEE."
            )
            break

        total_games = get_total_count()
        user_total = get_user_count(
            message.author.id
        )

        await message.channel.send(
            f"BRO PLEASEEEEE\n\n"
            f"Total shit games tracked: {total_games}\n"
            f"{message.author.display_name} has added "
            f"{user_total} turds to the pile."
        )

        new_leader = get_leader()

        if old_leader and new_leader:

            old_id, old_name, old_score = old_leader
            new_id, new_name, new_score = new_leader

            if (
                new_id != old_id and
                new_score > old_score
            ):
                await message.channel.send(
                    f"🏆🚨 NEW KING OF THE SHIT PILE 🚨🏆\n\n"
                    f"**{new_name}** has overtaken "
                    f"**{old_name}**!\n\n"
                    f"Current score: **{new_score}**"
                )

        break

    await bot.process_commands(message)

# ----------------------------
# COMMANDS
# ----------------------------

@bot.command()
async def leaderboard(ctx):

    cursor.execute("""
        SELECT username, COUNT(*) as total
        FROM recommendations
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()

    if not rows:
        await ctx.send(
            "No shit games have been tracked yet."
        )
        return

    msg = "🏆 SHIT GAME OFFENDER LEADERBOARD 🏆\n\n"

    for i, (username, count) in enumerate(
        rows,
        start=1
    ):
        msg += f"{i}. {username} — {count}\n"

    await ctx.send(msg)


@bot.command()
async def stats(ctx, member: discord.Member = None):

    member = member or ctx.author

    count = get_user_count(member.id)

    await ctx.send(
        f"{member.display_name} has recommended "
        f"**{count}** steamind dookies."
    )


@bot.command()
async def total(ctx):

    await ctx.send(
        f"📊 Total shit games tracked: "
        f"**{get_total_count()}**"
    )

# ----------------------------
# START BOT
# ----------------------------

bot.run(TOKEN)