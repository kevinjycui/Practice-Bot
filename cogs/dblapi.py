import discord
from discord.ext import commands, tasks
import requests
import json


class DiscordBotLists(commands.Cog):

    def __init__(self, bot, bot_id, tokens):
        self.bot = bot
        self.data = tokens
        self.data['bot_id'] = bot_id

    @tasks.loop(minutes=30)
    async def post_guild_count(self):
        self.data['server_count'] = len(self.bot.guilds)
        requests.post('https://botblock.org/api/count', data=json.dumps(self.data), headers={'Content-type':'application/json', 'Accept':'application/json'})

    @commands.command()
    @commands.is_owner()
    async def post_guild_count_manual(self, ctx):
        self.data['server_count'] = len(self.bot.guilds)
        response = requests.post('https://botblock.org/api/count', data=json.dumps(self.data), headers={'Content-type':'application/json', 'Accept':'application/json'})
        print(response.status_code)
        print(response.json())

def setup(bot, bot_id, tokens):
    bot.add_cog(DiscordBotLists(bot, bot_id, tokens))