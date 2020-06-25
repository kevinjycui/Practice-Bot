import discord
from discord.ext import commands, tasks
import requests


class DiscordBotLists(commands.Cog):

    def __init__(self, bot, bot_id, tokens):
        self.bot = bot
        self.data = tokens
        self.data['bot_id'] = bot_id

    @tasks.loop(minutes=30)
    async def post_guild_count(self):
        self.data['server_count'] = len(bot.guilds)
        requests.post('https://botblock.org/api/count', data=self.data, headers={'Content-type':'application/json', 'Accept':'application/json'})


def setup(bot, tokens):
    bot.add_cog(DiscordBotLists(bot, tokens))