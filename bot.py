import discord
from discord.ext import commands, tasks
import random as rand
import yaml
import cogs.dblapi as dblapi
import cogs.feedback as feedback
import cogs.problems_rankings as problems_rankings
import cogs.contests as contests
import cogs.searcher as searcher
from backend import mySQLConnection as query


try:
    config_file = open('config.yaml')
except FileNotFoundError:
    config_file = open('example_config.yaml')
finally:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
    prefix = config['bot']['prefix']
    bot_token, dev_token = config['bot']['token'], config['bot']['dev_token']
    dbl_token = config['dbl']['token']

statuses = ('implementation', 'dynamic programming', 'graph theory', 'data structures', 'trees', 'geometry', 'strings', 'optimization')
replies = ('Practice Bot believes that with enough practice, you can complete any goal!', 'Keep practicing! Practice Bot says that every great programmer starts somewhere!', 'Hey now, you\'re an All Star, get your game on, go play (and practice)!',
           'Stuck on a problem? Every logical problem has a solution. You just have to keep practicing!', ':heart:')

custom_prefixes = query.get_prefixes()

async def determine_prefix(bot, message):
    guild = message.guild
    if guild:
        return custom_prefixes.get(guild.id, prefix)
    return prefix

bot = commands.Bot(command_prefix=determine_prefix,
                   description='The all-competitive-programming-purpose Discord bot!',
                   owner_id=492435232071483392)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! (ponged in %ss)' % str(round(bot.latency, 3)))

@bot.command()
@commands.has_permissions(administrator=True)
async def setprefix(ctx, fix: str=prefix):
    if len(fix) > 255:
        await ctx.send(ctx.message.author.mention + ' Sorry, prefix is too long (maximum of 255 characters)')
    elif '"' in fix or '\'' in fix:
        await ctx.send(ctx.message.author.mention + ' Sorry, prefix cannot contain quotation charaters `\'` or `"`')
    elif ' ' in fix or '\n' in fix or '\r' in fix or '\t' in fix:
        await ctx.send(ctx.message.author.mention + ' Sorry, prefix cannot contain any whitespace')
    else:
        previous_prefix = custom_prefixes.get(ctx.message.guild.id, prefix)
        custom_prefixes[ctx.message.guild.id] = fix
        query.insert_ignore_server(ctx.message.guild.id)
        query.update_server_prefix(ctx.message.guild.id, fix)
        await ctx.send(ctx.message.author.mention + ' Server prefix changed from `%s` to `%s`' % (previous_prefix, fix))

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
    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.send(ctx.message.author.mention + ' Sorry, you are missing permissions to run this command!')
    else:
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
