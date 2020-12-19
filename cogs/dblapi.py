import discord
from discord.ext import commands, tasks
import dbl
import json
import sys
from utils.webclient import webc


class DiscordBotLists(commands.Cog):

    def __init__(self, bot, bot_id, tokens):
        self.bot = bot
        self.data = tokens
        self.data['bot_id'] = str(bot_id)

    @tasks.loop(minutes=30)
    async def post_guild_count(self):
        self.data['server_count'] = len(self.bot.guilds)
        response = await webc.webget_json('https://botblock.org/api/count', json=self.data, headers={'Content-type':'application/json', 'Accept':'application/json'})
        with open('log.txt', 'w+') as log:
            print(response, file=log)

    @post_guild_count.before_loop
    async def post_guild_count_before(self):
        await self.bot.wait_until_ready() 

class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot, token):
        self.bot = bot
        self.token = token
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes

    async def on_guild_post():
        print("Server count posted successfully")

def setup(bot, bot_id, tokens):
    bot.add_cog(TopGG(bot, tokens['top.gg']))
    tokens.pop('top.gg')
    bot.add_cog(DiscordBotLists(bot, bot_id, tokens))
