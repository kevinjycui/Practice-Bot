import discord
from discord.ext import commands, tasks
import requests
import json
import sys


class DiscordBotLists(commands.Cog):

    def __init__(self, bot, bot_id, tokens):
        self.bot = bot
        self.data = tokens
        self.data['bot_id'] = str(bot_id)

    @tasks.loop(minutes=30)
    async def post_guild_count(self):
        self.data['server_count'] = len(self.bot.guilds)
        response = requests.post('https://botblock.org/api/count', json=self.data, headers={'Content-type':'application/json', 'Accept':'application/json'})
        with open('log.txt', 'w+') as log:
            print(response.json(), file=log)

    @post_guild_count.before_loop
    async def post_guild_count_before(self):
        await self.bot.wait_until_ready()      

def setup(bot, bot_id, tokens):
    bot.add_cog(DiscordBotLists(bot, bot_id, tokens))