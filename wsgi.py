import os
from threading import Thread
from typing import Any
from dotenv import load_dotenv
import discord
from discord.ext import commands

from keep_alive import app
from cogs import COMMANDS, EVENT_HANDLERS
from bot_utilities.config_loader import config

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


def run_bot():
    bot = AIBot(command_prefix=[], intents=discord.Intents.all(), help_command=None)
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if TOKEN is None:
        print("\033[31mLooks like you haven't properly set up a Discord token environment variable. (Secrets on Render)\033[0m")
        return
    
    bot.run(TOKEN, reconnect=True)


# Start Discord bot in a background thread
bot_thread = Thread(target=run_bot, daemon=True)
bot_thread.start()

# Export the Flask app for gunicorn
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
