import discord
from discord.ext import commands
import config 

# Create bot instance
bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=discord.Intents.default())

@bot.event
async def on_ready():
    """Called when bot successfully connects to Discord"""
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='hello')
async def hello(ctx):
    """Simple test command"""
    await ctx.send('Hello! I am your friendly Catholic Discord bot. Did you pray today?')

#Rune the bot
if __name__ == '__main__':
    bot.run(config.DISCORD_TOKEN)