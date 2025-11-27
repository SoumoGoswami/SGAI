import os
from threading import Thread
from typing import Any
from dotenv import load_dotenv
import discord
from discord.ext import commands
from flask import Flask, render_template_string

from cogs import COMMANDS, EVENT_HANDLERS
from bot_utilities.config_loader import config

load_dotenv('.env')

# Create Flask app
app = Flask(__name__)

# HTML page content
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SG AI</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

        body {
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
            font-family: 'Press Start 2P', cursive;
            color: #00ff00;
            text-align: center;
        }

        h1, h2 {
            margin: 0;
            padding: 0;
            animation: flicker 1.5s infinite alternate;
        }

        h1 { font-size: 3em; }
        h2 { font-size: 1.5em; }

        @keyframes flicker {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .hacking-theme {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: -1;
            pointer-events: none;
        }

        .hacking-theme div {
            position: absolute;
            width: 2px;
            height: 100%;
            background: #00ff00;
            opacity: 0;
            animation: moveAndFade 5s linear infinite;
        }

        @keyframes moveAndFade {
            0% { transform: translateY(-100%); opacity: 0; }
            50% { opacity: 1; }
            100% { transform: translateY(100%); opacity: 0; }
        }

        .hacking-theme div:nth-child(odd) { animation-duration: 4s; }
        .hacking-theme div:nth-child(even) { animation-duration: 6s; }
    </style>
</head>
<body bgcolor='black'>
    <div class="content">
        <h1>SG AI</h1>
        <h2>Hare Krishna</h2>
    </div>
    <div class="hacking-theme">
        <div style="left: 10%;"></div>
        <div style="left: 20%;"></div>
        <div style="left: 30%;"></div>
        <div style="left: 40%;"></div>
        <div style="left: 50%;"></div>
        <div style="left: 60%;"></div>
        <div style="left: 70%;"></div>
        <div style="left: 80%;"></div>
        <div style="left: 90%;"></div>
    </div>
</body>
</html>"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
