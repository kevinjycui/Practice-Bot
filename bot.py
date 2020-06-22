import discord
from discord.ext import commands, tasks
from auth import bot_token, dev_token, cat_api, client_id, client_secret, dbl_token
import random as rand
import cogs.dblapi as dblapi
import cogs.feedback as feedback
import cogs.problems_rankings as problems_rankings
import cogs.contests as contests
import cogs.searcher as searcher


statuses = ('implementation', 'dynamic programming', 'graph theory', 'data structures', 'trees', 'geometry', 'strings', 'optimization')
replies = ('Practice Bot believes that with enough practice, you can complete any goal!', 'Keep practicing! Practice Bot says that every great programmer starts somewhere!', 'Hey now, you\'re an All Star, get your game on, go play (and practice)!',
           'Stuck on a problem? Every logical problem has a solution. You just have to keep practicing!', ':heart:')

with open('prefix') as f:
    prefix = f.read()

bot = commands.Bot(command_prefix=prefix,
                   description='The all-competitive-programming-purpose Discord bot!',
                   owner_id=492435232071483392)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! (ponged in %ss)' % str(round(bot.latency, 3)))

@bot.command()
async def motivation(ctx):
    await ctx.send(ctx.message.author.mention + ' ' + rand.choice(replies))

@tasks.loop(minutes=30)
async def status_change():
    await bot.change_presence(activity=discord.Game(name='with %s | %shelp' % (rand.choice(statuses), prefix)))

@status_change.before_loop
async def status_change_before():
    await bot.wait_until_ready()

bot.remove_command('help')

@bot.command()
async def help(ctx):
    await ctx.send(ctx.message.author.mention + ' Here is a full list of my commands! https://github.com/kevinjycui/Practice-Bot/wiki/Commands')

@bot.event
async def on_command_error(ctx, error):
    if any(
        isinstance(error, CommonError) for CommonError in (
            commands.CommandNotFound, 
            commands.errors.MissingRequiredArgument,
            commands.errors.NoPrivateMessage,
            commands.errors.BadArgument
        )
    ):
        return
    raise error

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

if __name__ == '__main__':
    status_change.start()
    problems_rankings.setup(bot)
    contests.setup(bot)
    feedback.setup(bot)
    searcher.setup(bot)
    if bot_token != dev_token:
        dblapi.setup(bot, dbl_token)
    bot.run(bot_token)
