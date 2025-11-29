import os
from typing import Any

import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogs import COMMANDS, EVENT_HANDLERS
from bot_utilities.config_loader import config


from keep_alive import keep_alive
keep_alive()


load_dotenv('.env')

class AIBot(commands.AutoShardedBot):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if config['AUTO_SHARDING']:
            super().__init__(*args, **kwargs)
        else:
            super().__init__(shard_count=1, *args, **kwargs)

    async def setup_hook(self) -> None:
        for cog in COMMANDS:
            cog_name = cog.split('.')[-1]
            discord.client._log.info(f"Loaded Command {cog_name}")
            await self.load_extension(f"{cog}")
        for cog in EVENT_HANDLERS:
            cog_name = cog.split('.')[-1]
            discord.client._log.info(f"Loaded Event Handler {cog_name}")
            await self.load_extension(f"{cog}")
        print('If syncing commands is taking longer than usual you are being ratelimited')
        await self.tree.sync()
        discord.client._log.info(f"Loaded {len(self.commands)} commands")

bot = AIBot(command_prefix=[], intents=discord.Intents.all(), help_command=None)

TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN is None or TOKEN.strip() == "":
    print("\033[31m❌ ERROR: DISCORD_TOKEN is not set!\033[0m")
    print("\033[33mTo fix this:")
    print("1. Click the 'Secrets' icon (lock icon) in Replit's left sidebar")
    print("2. Add a new secret: Key='DISCORD_TOKEN', Value='<your_token>'")
    print("3. Get your token from: https://discord.com/developers/applications\033[0m")
    exit(1)

# Also check for API key
API_KEY = os.getenv('API_KEY') or os.getenv('GROQ_API_KEY')
if API_KEY is None or API_KEY.strip() == "":
    print("\033[31m❌ ERROR: API_KEY is not set!\033[0m")
    print("\033[33mTo fix this:")
    print("1. Click the 'Secrets' icon (lock icon) in Replit's left sidebar")
    print("2. Add a new secret: Key='API_KEY', Value='<your_groq_api_key>'")
    print("3. Get your key from: https://console.groq.com/keys\033[0m")
    exit(1)

print("\033[32m✓ All secrets configured. Starting bot...\033[0m")
bot.run(TOKEN, reconnect=True)
