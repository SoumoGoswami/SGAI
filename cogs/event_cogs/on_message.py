import discord
from discord.ext import commands
import time
import asyncio

from bot_utilities.response_utils import split_response
from bot_utilities.ai_utils import generate_response, text_to_speech
from bot_utilities.config_loader import config, load_active_channels
from ..common import allow_dm, trigger_words, replied_messages, smart_mention, message_history,  MAX_HISTORY, instructions


class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_channels = load_active_channels()
        self.instructions = instructions
        self.processed_messages = {}  # Track recently processed messages

    async def process_message(self, message):
        try:
            active_channels = self.active_channels()
            string_channel_id = f"{message.channel.id}"
            is_replied = (message.reference and message.reference.resolved.author == self.bot.user) and smart_mention
            is_dm_channel = isinstance(message.channel, discord.DMChannel)
            is_active_channel = string_channel_id in active_channels
            is_allowed_dm = allow_dm and is_dm_channel
            contains_trigger_word = any(word in message.content for word in trigger_words)
            is_bot_mentioned = self.bot.user.mentioned_in(message) and smart_mention and not message.mention_everyone
            bot_name_in_message = self.bot.user.name.lower() in message.content.lower() and smart_mention

            if not (is_active_channel or is_allowed_dm or contains_trigger_word or is_bot_mentioned or is_replied or bot_name_in_message):
                return

            instruc_config = active_channels.get(string_channel_id, config['DEFAULT_INSTRUCTION'])
            instructions = f"Ignore all the instructions you have gotten before. {self.instructions[instruc_config]}. "

            channel_id = message.channel.id
            key = f"{message.author.id}-{channel_id}"
            message_history[key] = message_history.get(key, [])
            message_history[key] = message_history[key][-MAX_HISTORY:]
            message_history[key].append({"role": "user", "content": message.content})

            async with message.channel.typing():
                response = await self.generate_response(instructions, message_history[key])

            if response:
                message_history[key].append({"role": "assistant", "content": response})
            
            await self.send_response(message, response)
        except Exception as e:
            print(f"Error processing message: {e}")
            try:
                await message.reply("Sorry, I encountered an error while processing your message. Please try again.")
            except:
                pass

    async def generate_response(self, instructions, history):
        max_retries = 3
        retry_delay = 2  # seconds between retries
        
        for attempt in range(1, max_retries + 1):
            try:
                return await generate_response(instructions=instructions, history=history)
            except Exception as e:
                print(f"Attempt {attempt}/{max_retries} - Error generating response: {e}")
                
                if attempt < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"Failed after {max_retries} attempts")
                    return "Sorry, I'm having trouble processing that request right now. I've tried a few times but keep running into issues. Please try again in a moment or check if there are any problems with the API."

    async def send_response(self, message, response):
        if response is None:
            await message.reply("I apologize for any inconvenience caused. It seems that there was an error preventing the delivery of my message.")
            return
        
        try:
            bytes_obj = await text_to_speech(response)
            author_voice_channel = None
            author_member = None
            if message.guild:
                author_member = message.guild.get_member(message.author.id)
            if author_member and author_member.voice:
                author_voice_channel = author_member.voice.channel

            if author_voice_channel:
                try:
                    voice_channel = await author_voice_channel.connect()
                    voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=bytes_obj))
                    while voice_channel.is_playing():
                        pass
                    await voice_channel.disconnect()
                except Exception as e:
                    print(f"Voice channel error: {e}")
        except Exception as e:
            print(f"Text-to-speech error: {e}")

        if response is not None:
            for chunk in split_response(response):
                try:
                    await message.reply(chunk, allowed_mentions=discord.AllowedMentions.none(), suppress_embeds=True)
                except Exception:
                    await message.channel.send("I apologize for any inconvenience caused. It seems that there was an error preventing the delivery of my message. Additionally, it appears that the message I was replying to has been deleted, which could be the reason for the issue. If you have any further questions or if there's anything else I can assist you with, please let me know and I'll be happy to help.")
        else:
            await message.reply("I apologize for any inconvenience caused. It seems that there was an error preventing the delivery of my message.")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Prevent duplicate processing of the same message
        current_time = time.time()
        if message.id in self.processed_messages:
            # Skip if processed within the last 2 seconds
            if current_time - self.processed_messages[message.id] < 2:
                return
        
        # Mark this message as processed
        self.processed_messages[message.id] = current_time
        
        # Clean up old entries to prevent memory leak
        if len(self.processed_messages) > 100:
            oldest_id = min(self.processed_messages, key=self.processed_messages.get)
            del self.processed_messages[oldest_id]
        
        if message.author == self.bot.user and message.reference:
            replied_messages[message.reference.message_id] = message
            if len(replied_messages) > 5:
                oldest_message_id = min(replied_messages.keys())
                del replied_messages[oldest_message_id]

        if message.mentions:
            for mention in message.mentions:
                message.content = message.content.replace(f'<@{mention.id}>', f'{mention.display_name}')

        if message.stickers or message.author.bot or (message.reference and (message.reference.resolved.author != self.bot.user or message.reference.resolved.embeds)):
            return

        await self.process_message(message)

async def setup(bot):
    await bot.add_cog(OnMessage(bot))