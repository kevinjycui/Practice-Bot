import re
import discord
from discord.ext import commands, tasks
import aiohttp
import random as rand
import yaml
from datetime import datetime
import cogs.dblapi as dblapi
import cogs.feedback as feedback
import cogs.problems_rankings as problems_rankings
import cogs.contests as contests
import cogs.searcher as searcher
from connector import mySQLConnection as query
from utils.country import Country
from utils.onlinejudges import OnlineJudges, NoSuchOJException

onlineJudges = OnlineJudges()

is_ascii = lambda s: re.match('^[\x00-\x7F]+$', s) != None

try:
    config_file = open('config.yml')
except FileNotFoundError:
    config_file = open('example_config.yml')
finally:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
    prefix = config['bot']['prefix']
    bot_token = config['bot']['token']
    DEBUG = config['bot']['debug']
    dbl_tokens = {}
    if 'dbl' in config:
        for dbl, dbl_token in list(config['dbl'].items()):
            dbl_tokens[dbl] = dbl_token
    bot_id = config['bot']['id']
    owner_id = config['bot']['owner_id']

replies = ('Practice Bot believes that with enough practice, you can complete any goal!', 'Keep practicing! Practice Bot says that every great programmer starts somewhere!', 'Hey now, you\'re an All Star, get your game on, go play (and practice)!',
           'Stuck on a problem? Every logical problem has a solution. You just have to keep practicing!', ':heart:')

custom_prefixes = query.get_prefixes()


async def determine_prefix(bot, message):
    guild = message.guild
    if guild:
        query.insert_ignore_server(guild.id)
        return custom_prefixes.get(guild.id, prefix)
    return prefix

intents = discord.Intents.default()
intents.members = True
bot = commands.AutoShardedBot(
    shard_count=20,
    command_prefix=determine_prefix,
    description='The all-competitive-programming-purpose Discord bot!',
    owner_id=owner_id,
    intents=intents,
    fetch_offline_members=True
)

async def changenick(ctx, member: discord.Member, fix):
    name = ctx.message.guild.get_member(bot.user.id).display_name
    arr = name.split(' ')
    prefix = arr[-1]
    
    if prefix[0] == '[' and prefix[-1] == ']':
        await member.edit(nick=f"{' '.join(arr[:-1])} [{fix}]")
    else:
        await member.edit(nick=f'{name} [{fix}]')

async def prefix_from_guild(guild):
    if guild:
        query.insert_ignore_server(guild.id)
        custom = query.get_prefix(guild.id)
        return prefix if custom is None else custom
    return prefix


@bot.command()
async def ping(ctx):
    await ctx.send('Pong! (ponged in %ss)' % str(round(bot.latency, 3)))


@bot.command()
@commands.has_permissions(manage_guild=True)
async def setprefix(ctx, fix: str=None):
    if fix is not None and len(fix) > 255:
        await ctx.send(ctx.message.author.display_name + ', Sorry, prefix is too long (maximum of 255 characters)')
    elif fix is not None and ('"' in fix or '\'' in fix):
        await ctx.send(ctx.message.author.display_name + ', Sorry, prefix cannot contain quotation charaters `\'` or `"`')
    elif fix is not None and (' ' in fix or '\n' in fix or '\r' in fix or '\t' in fix):
        await ctx.send(ctx.message.author.display_name + ', Sorry, prefix cannot contain any whitespace')
    elif fix is not None and '\\' in fix:
        await ctx.send(ctx.message.author.display_name + ', Sorry, prefix cannot contain contain backslash characters `\`')
    elif fix is not None and not is_ascii(fix):
        await ctx.send(ctx.message.author.display_name + ', Sorry, prefix cannot contain non-ASCII characters')
    else:
        default = fix is None
        if default:
            fix = prefix
        previous_prefix = custom_prefixes.get(ctx.message.guild.id, prefix)
        custom_prefixes[ctx.message.guild.id] = fix
        query.insert_ignore_server(ctx.message.guild.id)
        query.update_server_prefix(ctx.message.guild.id, fix)
        if default:
            await ctx.send(ctx.message.author.display_name + ', No prefix given, defaulting to `%s`. Server prefix changed from `%s` to `%s`' % (prefix, previous_prefix, fix))
        else:
            await ctx.send(ctx.message.author.display_name + ', Server prefix changed from `%s` to `%s`' % (previous_prefix, fix))
        await changenick(ctx, ctx.message.guild.get_member(bot.user.id), fix)


@bot.command()
async def motivation(ctx):
    await ctx.send(ctx.message.author.display_name + ', ' + rand.choice(replies))

# @tasks.loop(minutes=1)
# async def status_change():
#     await bot.change_presence(
#         activity=discord.Activity(
#             type=discord.ActivityType.watching, 
#             name='%d servers practise | %shelp' % (len(bot.guilds), prefix)
#         )
#     )

# @status_change.before_loop
# async def status_change_before():
#     await bot.wait_until_ready()


bot.remove_command('help')


@bot.command()
async def help(ctx):
    await ctx.send(ctx.message.author.display_name + ', Here is a full list of my commands! <https://github.com/kevinjycui/Practice-Bot/wiki/Commands>')


@bot.event
async def on_command_error(ctx, error):
    with open('command.log', 'a') as f:
        f.write('%s: [ERROR] %s\n' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'NULL' if ctx.command is None else ctx.command.name))
    if any(
        isinstance(error, CommonError) for CommonError in (
            commands.CommandNotFound,
            commands.errors.MissingRequiredArgument,
            commands.errors.NoPrivateMessage,
            commands.errors.BadArgument,
            commands.errors.NotOwner
        )
    ):
        return
    elif any(
        isinstance(error, FormatError) for FormatError in (
            commands.errors.UnexpectedQuoteError,
            commands.errors.ExpectedClosingQuoteError
        )
    ):
        await ctx.send(ctx.message.author.display_name + ', Invalid query. Please do not place any unnecessary quotation marks in your command.')
    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.send(ctx.message.author.display_name + ', Sorry, you are missing permissions to run this command!')
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send(ctx.message.author.display_name + ', It would seem that the bot is missing permissions to run this command! Be sure that all the required permissions are set to on: both for the bot and the channel. See here for a list of required permissions: https://github.com/kevinjycui/Practice-Bot/wiki/Permissions')
    elif isinstance(error, aiohttp.ClientError):
        await ctx.send(ctx.message.author.display_name + ', There appears to have been some HTTP error. Either your command was invalid or there is some problem in the server. Try again later!')
    else:
        server_prefix = await prefix_from_guild(ctx.message.guild)
        await ctx.send(ctx.message.author.display_name + ', An unexpected error occurred. Please try again. If this error persists, you can report it using the `%ssuggest <suggestion>` command.' % server_prefix)
        user = bot.get_user(bot.owner_id)
        await user.send('```%s\n%s```' % (repr(error), ctx.message.content))
        raise error


@bot.command(aliases=['toggleJoin', 'tj'])
@commands.has_permissions(administrator=True)
async def togglejoin(ctx):
    join_message = query.get_join_message(ctx.message.guild.id)
    query.update_server(ctx.message.guild.id, 'join_message', not join_message)
    await ctx.send(ctx.message.author.display_name + ', on-join direct messages for the bot turned `%s`.' % ('ON' if not join_message else 'OFF'))


@bot.command(aliases=['sc'])
@commands.is_owner()
async def stats(ctx, option=None):
    if option is not None and option == '-s':
        await ctx.send('Server count: `%d`' % len(bot.guilds))
        return
    embed = discord.Embed(title='Bot Analytics')
    embed.add_field(name='Server count', value=len(bot.guilds), inline=False)
    embed.add_field(name='User count', value=query.user_count(), inline=False)
    embed.add_field(name='DMOJ', value=query.get_global_linked_count('dmoj'), inline=False)
    embed.add_field(name='Codeforces', value=query.get_global_linked_count('codeforces'), inline=False)
    def country_with_count(listitem):
        return str(Country(listitem.split(' - ')[0])) + ' - ' + listitem.split(' - ')[1]
    embed.add_field(name='Countries', value='\n'.join(map(country_with_count, sorted(query.get_global_countries(), key=lambda listitem: int(listitem.split(' - ')[1]), reverse=True))), inline=False)
    await ctx.send(embed=embed)


@bot.event
async def on_member_join(member):
    global prefix
    join_message = query.get_join_message(member.guild.id)
    if not join_message:
        return
    this_user = query.get_user(member.id)
    if this_user == {}:
        query.insert_ignore_user(member.id)
        server_prefix = await prefix_from_guild(member.guild)
        await member.send('Hello, %s, and welcome to %s! The default prefix for this server is `%s`, but in direct messaging, use the prefix `%s`. It would seem that you have yet to join a server that has Practice Bot! Using Practice Bot, you can link your DMOJ or Codeforces account to your Discord account to perform different commands. You may use one of the following formats:\n\n*Please use connect commands in this direct message chat only!*\n\n`%sconnect dmoj <dmoj-api-token>` (your DMOJ API token can be found by going to https://dmoj.ca/edit/profile/ and selecting the __Generate__ or __Regenerate__ option next to API Token)\n\n`%sconnect cf <codeforces-handle>`\n\nUse `%shelp` to see a full list of commands and more details.' % (member.display_name, member.guild.name, server_prefix, prefix, prefix, prefix, prefix))


@bot.before_invoke
async def log(ctx):
    with open('command.log', 'a') as f:
        f.write('%s: %s\n' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ctx.command.name))


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name='you practise | %shelp' % prefix
        )
    )
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('Shards:', len(bot.shards))
    print('------')
    if DEBUG:
        user = bot.get_user(bot.owner_id)
        await user.send('Bot Online!')


if __name__ == '__main__':
    # status_change.start()
    problems_rankings.setup(bot)
    contests.setup(bot)
    feedback.setup(bot)
    searcher.setup(bot)
    if not DEBUG:
        dblapi.setup(bot, bot_id, dbl_tokens)
    bot.run(bot_token)
