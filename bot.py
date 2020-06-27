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
    dbl_tokens = {}
    for dbl, dbl_token in list(config['dbl'].items()):
        dbl_tokens[dbl] = dbl_token
    bot_id = config['bot']['id']

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
async def oj(ctx, oj: str):
    if oj.lower() == 'dmoj':
        about = 'DMOJ, DMOJ: Modern Online Judge, or Don Mills Online Judge, is a Canadian \
        modern contest platform and archive of programming problems made in 2014 by \
        Tudor Brindus and Guanzhong Chen from Don Mills Collegiate Institute and based in \
        Toronto. It is entirely open-source and inspired by WCIPEG, which merged with DMOJ \
        in 2020. DMOJ is known to have many problems from the CCC, CCO, IOI, and COCI. Notable \
        contests hosted by DMOJ include the DMOPC or DMOJ Monthly Open Programming Contest and \
        the DMPG or Don Mills Programming Gala. DMOJ contests support ICPC/IOI/AtCoder/ECOO formats. \
        As of 2020, DMOJ has over 50, 000 users and supports 65 programming languages. DMOJ is \
        primarily in English but also has translations to other languages such as Japanese, \
        Vietnamese, and Simplified Chinese. DMOJ has hosted national olympiads such as the MOI \
        (Moroccan Olympiad in Informatics) in 2017.'
        embed = discord.Embed(title='DMOJ: Modern Online Judge', description=about, inline=False)
        embed.add_field(name='Country', value=':flag_ca:', inline=False)
        embed.add_field(name='Abbreviations', value='`$random dmoj`', inline=False)
        embed.add_field(name='Random Problems', value='Yes', inline=False)
        embed.add_field(name='Contest Notifications', value='Yes', inline=False)
        embed.add_field(name='Rating Roles', value='Yes', inline=False)
        embed.add_field(name='Account Link', value='Yes', inline=False)
        embed.add_field(name='Submission', value='Yes', inline=False)
        await ctx.send(embed=embed)
    elif oj.lower() == 'cf' or oj.lower() == 'codeforces':
        about = 'Codeforces is a Russian online judge and contest platform made in 2009 by students \
        from ITMO University led by Mikhail Mirzayanov based in St. Petersburg. As of 2018, Codeforces \
        has over 600, 000 users, \
        surpassing TopCoder in 2013. Codeforces contests include Codeforces Rounds, which are 2 hour \
        rounds held about once a week and Educational Rounds, held 2-3 times per month and followed by \
        a 24 hour hacking period. Rated contests are split into divisions, with Div 1 being the most difficult \
        and Div 4 being the least difficult. Notable users of Codeforces include top sport programmers like \
        Gennady Korotkevich, Petr Mitrichev, Benjamin Qi and Makoto Soejima. Codeforces is available in both \
        English and Russian. Many universities use Codeforces as a tool for teaching concepts in Competitive \
        Programming.'
        embed = discord.Embed(title='Codeforces', description=about, inline=False)
        embed.add_field(name='Country', value=':flag_ru:', inline=False)
        embed.add_field(name='Abbreviations', value='`$random codeforces`, `$random cf`', inline=False)
        embed.add_field(name='Random Problems', value='Yes', inline=False)
        embed.add_field(name='Contest Notifications', value='Yes', inline=False)
        embed.add_field(name='Rating Roles', value='No', inline=False)
        embed.add_field(name='Account Link', value='No', inline=False)
        embed.add_field(name='Submission', value='No', inline=False)
        await ctx.send(embed=embed)
    elif oj.lower() == 'atcoder' or oj.lower() == 'at' or oj.lower() == 'ac':
        about = 'AtCoder is a Japanese programming contest management service that specializes in the development \
        and administration of programming contests. It also specializes in the plan, administration of the \
        programming contest, and adoption support and ability judgment duties of the software engineer. AtCoder was \
        made in 2012 and based in Tokyo. AtCoder has 3 official contest types: AtCoder Grand Contest (AGC), which is the \
        most difficult, AtCoder Regular Contest (ARC), and AtCoder Beginner Contest (ABC). AGC is held about twice \
        a month, with other weeks consisting of both ARC and ABC. AtCoder is available in both \
        English and Japanese.'
        embed = discord.Embed(title='AtCoder', description=about, inline=False)
        embed.add_field(name='Abbreviations', value='`$random atcoder`, `$random at`, `$random ac`', inline=False)
        embed.add_field(name='Country', value=':flag_jp:', inline=False)
        embed.add_field(name='Random Problems', value='Yes', inline=False)
        embed.add_field(name='Contest Notifications', value='Yes', inline=False)
        embed.add_field(name='Rating Roles', value='No', inline=False)
        embed.add_field(name='Account Link', value='No', inline=False)
        embed.add_field(name='Submission', value='No', inline=False)
        await ctx.send(embed=embed)
    elif oj.lower() == 'wcipeg' or oj.lower() == 'peg':
        about = 'WCIPEG, PEG Online Judge, or Woburn Collegiate Institute Programming Enrichment Group is a Canadian online \
        programming problem archive made in 2007 by students at Woburn Collegiate Institute based in Toronto. The site later \
        inspired DMOJ in 2014, and merged into DMOJ in 2020. WCIPEG held contests such as the Woburn Challenge annually. Before closing, \
        WCIPEG supported 15 programming languages. The site is in English.'
        embed = discord.Embed(title='PEG Online Judge', description=about, inline=False)
        embed.add_field(name='Country', value=':flag_ca:', inline=False)
        embed.add_field(name='Abbreviations', value='`$random wcipeg`, `$random peg`', inline=False)
        embed.add_field(name='Random Problems', value='Yes', inline=False)
        embed.add_field(name='Contest Notifications', value='N/A', inline=False)
        embed.add_field(name='Rating Roles', value='No', inline=False)
        embed.add_field(name='Account Link', value='No', inline=False)
        embed.add_field(name='Submission', value='No', inline=False)
        await ctx.send(embed=embed)
    elif oj.lower() == 'cses':
        about = 'CSES or Code Submission Evaluation System is a Finnish programming problem archive made by Antti Laaksonen and Topi Talvitie \
        in 2013 based in Helsinki. The site is most well-known for its CSES Problem Set, but also archives problems from the \
        BOI and CEOI among others. Notable users of CSES include Benjamin Qi. The site has problems available in both English and \
        Finnish. As of 2020, the CSES Problem Set contains 200 tasks with 10, 000 users.'
        embed = discord.Embed(title='CSES', description=about, inline=False)
        embed.add_field(name='Country', value=':flag_fi:', inline=False)
        embed.add_field(name='Abbreviations', value='`$random cses`', inline=False)
        embed.add_field(name='Random Problems', value='Yes', inline=False)
        embed.add_field(name='Contest Notifications', value='N/A', inline=False)
        embed.add_field(name='Rating Roles', value='N/A', inline=False)
        embed.add_field(name='Account Link', value='No', inline=False)
        embed.add_field(name='Submission', value='No', inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(ctx.message.author.mention + ' Sorry, no online judge found. Search only for online judges used by this bot (DMOJ, Codeforces, AtCoder, WCIPEG, CSES)')

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
        dblapi.setup(bot, bot_id, dbl_tokens)
    bot.run(bot_token)
