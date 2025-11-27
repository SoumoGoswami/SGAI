import discord
from discord.ext import commands


from ..common import current_language


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description=current_language["help"])
    async def help(self, ctx):
        try:
            embed = discord.Embed(title="Bot Commands", color=0x03a64b)
            
            # Set thumbnail safely
            if self.bot.user and self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)
            
            # Get app commands from the command tree
            try:
                commands_list = self.bot.tree.get_commands()
            except:
                commands_list = []
            
            for command in commands_list:
                try:
                    if command.hidden:
                        continue
                    command_description = command.description or "No description available"
                    embed.add_field(name=f"/{command.name}", value=command_description, inline=False)
                except:
                    pass

            footer_text = current_language.get('help_footer', 'https://google.com')
            embed.set_footer(text=footer_text)
            
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            await ctx.send(f"Error displaying help: {str(e)}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
