import discord
from discord.ext import commands, tasks
from auth import bot_token
import requests
import json
import random as rand
from time import time
from datetime import datetime
import wikipedia
import urllib

statuses = ('implementation', 'dynamic programming', 'graph theory', 'data structures', 'trees', 'geometry', 'strings', 'optimization')
replies = ('Practice Bot believes that with enough practice, you can complete any goal!', 'Keep practicing! Practice Bot says that every great programmer starts somewhere!', 'Hey now, you\'re an All Star, get your game on, go play (and practice)!',
           'Stuck on a problem? Every logical problem has a solution. You just have to keep practicing!', ':heart:')
contest_channels = [511001840071213067, 691115746843033683] # contest notification channel ids

dmoj_problems = None
cf_problems = None
at_problems = None

def get(api_url):
    response = requests.get(api_url)

    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    return None

bot = commands.Bot(command_prefix='!')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command()
async def random(ctx, oj=None):
    global dmoj_problems, cf_problems, at_problems
    start = time()
    
    if oj is None:
        oj = rand.choice(('dmoj', 'cf', 'at'))
        
    if oj.lower() == 'dmoj':
        if not dmoj_problems:
            await ctx.send(ctx.message.author.mention + ' There seems to be a problem with the DMOJ API. Please try again later :shrug:')
            return    
        name, prob = rand.choice(list(dmoj_problems.items()))
        url = 'https://dmoj.ca/problem/' + name
        embed = discord.Embed(title=prob['name'], description=url +' (searched in '+str(round((time()-start), 3))+'s)')
        embed.timestamp = datetime.utcnow()
        embed.add_field(name='Points', value=prob['points'], inline=False)
        embed.add_field(name='Partials', value=('Yes' if prob['partial'] else 'No'), inline=False)
        embed.add_field(name='Group', value=prob['group'], inline=False)
        await ctx.send(ctx.message.author.mention, embed=embed)
        
    elif oj.lower() == 'cf' or oj.lower() == 'codeforces':
        if not cf_problems:
            await ctx.send(ctx.message.author.mention + ' There seems to be a problem with the Codeforces API. Please try again later :shrug:')
            return
        prob = rand.choice(cf_problems)
        url = 'https://codeforces.com/problemset/problem/' + str(prob['contestId']) + '/' + str(prob['index'])
        embed = discord.Embed(title=prob['name'], description=url +' (searched in '+str(round((time()-start), 3))+'s)')
        embed.timestamp = datetime.utcnow()
        embed.add_field(name='Type', value=prob['type'], inline=False)
        if 'points' in prob.keys():
            embed.add_field(name='Points', value=prob['points'], inline=False)
        embed.add_field(name='Rating', value=prob['rating'], inline=False)
        embed.add_field(name='Tags', value='||'+', '.join(prob['tags'])+'||', inline=False)
        await ctx.send(ctx.message.author.mention, embed=embed)

    elif oj.lower() == 'atcoder' or oj.lower() == 'at':
        if not at_problems:
            await ctx.send(ctx.message.author.mention + ' There seems to be a problem with the AtCoder API. Please try again later :shrug:')
            return
        prob = rand.choice(at_problems)
        url = 'https://atcoder.jp/contests/' + prob['contest_id'] + '/tasks/' + prob['id']
        embed = discord.Embed(title=prob['title'], description=url +' (searched in '+str(round((time()-start), 3))+'s)')
        embed.timestamp = datetime.utcnow()
        if prob['point']:
            embed.add_field(name='Points', value=prob['point'], inline=False)
        embed.add_field(name='Solver Count', value=prob['solver_count'], inline=False)
        await ctx.send(ctx.message.author.mention, embed=embed)

    else:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `!random <online judge>` (dmoj/codeforces/atcoder).')

@bot.command()
async def motivation(ctx):
    await ctx.send(ctx.message.author.mention + ' ' + rand.choice(replies))

def getSummary(name):
    try:
        if urllib.request.urlopen('https://en.wikipedia.org/wiki/'+name).getcode() != 404:
            return wikipedia.page(name), wikipedia.summary(name, sentences=5)
    except wikipedia.DisambiguationError as e:
        if len(e.options) > 0:
            return getSummary(e.options[0].replace(' ', '_'))
        else:
            return None, None
    except:
        return None, None

@bot.command()
async def whatis(ctx, name=None):
    start = time()
    if name is None:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `!whatis <thing>`.')
        return
    page, summary = getSummary(name.replace(' ', '_'))
    if summary is None:
        await ctx.send(ctx.message.author.mention + ' Sorry, I couldn\'t find anything on "%s"' % name)
        return
    embed = discord.Embed(title=page.title, description=page.url+' (searched in '+str(round((time()-start), 3))+'s)')
    embed.timestamp = datetime.utcnow()
    embed.add_field(name='Summary', value=summary, inline=False)
    await ctx.send(ctx.message.author.mention + ' Here\'s what I found!', embed=embed)

##@bot.command()
##@commands.has_permissions(administrator=True)
##async def set(ctx, setting, channel):
##    if setting == 'notify':
##        contest_channels.append(channel[2:1])
##        ctx.send(discord.get_channel(channel[2:-1]).mention + ' set to contest notification channel.')            
##
##@set.error
##async def set_error(error, ctx):
##    if isinstance(error, commands.CheckFailure):
##        ctx.send(ctx.message.author.mention +' Sorry, you don\'t have permissions to set a contest notification channel.')
##
##@bot.command()
##@commands.has_permissions(administrator=True)
##async def remove(ctx, setting, channel):
##    if setting == 'notify':
##        if channel[2:-1] in contest_channels:
##            contest_channels.remove(channel[2:-1])
##            ctx.send(discord.get_channel(channel[2:-1]).mention + ' is no longer a contest notification channel.')
##        else:
##            ctx.send('That channel is not a contest notification channel.')
##       
##@remove.error
##async def remove_error(error, ctx):
##    if isinstance(error, commands.CheckFailure):
##        ctx.send(ctx.message.author.mention +' Sorry, you don\'t have permissions to remove a contest notification channel.')
        
@tasks.loop(minutes=30)
async def status_change():
    await bot.change_presence(activity=discord.Game(name=' with %s' % rand.choice(statuses)))

@status_change.before_loop
async def status_change_before():
    await bot.wait_until_ready()

@tasks.loop(hours=3)
async def refresh_problems():
    global dmoj_problems, cf_problems, at_problems
    problems = get('https://dmoj.ca/api/problem/list')
    if problems is not None:
        dmoj_problems = problems
    cf_data = get('https://codeforces.com/api/problemset.problems')
    if cf_data is not None:
        try:
            cf_problems = cf_data['result']['problems']
        except KeyError:
            pass
    problems = get('https://kenkoooo.com/atcoder/resources/merged-problems.json')
    if problems is not None:
        at_problems = problems

@refresh_problems.before_loop
async def refresh_problems_before():
    await bot.wait_until_ready()

@tasks.loop(minutes=5)
async def check_contests():
    contests = get('https://dmoj.ca/api/contest/list')
    if contests is not None:
        with open('dmoj_contests.json') as f:
            prev_contests = json.load(f)
        for contest in range(max(len(prev_contests), len(contests)-5), len(contests)):
            name, details = list(contests.items())[contest]
            spec = get('https://dmoj.ca/api/contest/info/' + name)
            url = 'https://dmoj.ca/contest/' + name
            embed = discord.Embed(title=(':trophy: %s' % details['name']), description=url)
            embed.timestamp = datetime.utcnow()
            embed.add_field(name='Start Time', value=datetime.strptime(details['start_time'].replace(':', ''), '%Y-%m-%dT%H%M%S%z').strftime('%B %d, %Y %H:%M:%S%z'), inline=False)
            embed.add_field(name='End Time', value=datetime.strptime(details['end_time'].replace(':', ''), '%Y-%m-%dT%H%M%S%z').strftime('%B %d, %Y %H:%M:%S%z'), inline=False)
            if details['time_limit']:
                embed.add_field(name='Time Limit', value=details['time_limit'], inline=False)
            if len(details['labels']) > 0:
                embed.add_field(name='Labels', value=', '.join(details['labels']), inline=False)
            embed.add_field(name='Rated', value='Yes' if spec['is_rated'] else 'No', inline=False)
            embed.add_field(name='Format', value=spec['format']['name'], inline=False)
            for channel_id in contest_channels:
                ctx = bot.get_channel(channel_id)
                await ctx.send(embed=embed)
        with open('dmoj_contests.json', 'w') as json_file:
            json.dump(contests, json_file)
    
            
@check_contests.before_loop
async def check_contests_before():
    await bot.wait_until_ready()

bot.remove_command('help')

@bot.command()
async def help(ctx):
    embed = discord.Embed(title='Practice Bot', description='The all-competitive-programming-purpose Discord bot!', color=0xeee657)
    embed.add_field(name='!help', value='Sends you a list of my commands (obviously)', inline=False)
    embed.add_field(name='!random <online judge>', value='Gets a random problem from DMOJ, Codeforces, or AtCoder', inline=False)
    embed.add_field(name='!whatis <query>', value='Searches for something on Wikipedia', inline=False)
    embed.add_field(name='!motivation', value='Sends you some (emotional) support :smile:', inline=False)
    embed.add_field(name='!ping', value='Checks my ping to the Discord server', inline=False)
    ctx.message.author.send(embed=embed)
    ctx.send(ctx.message.author.mention + ' I\'ve sent you a list of my commands to your DM!')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

status_change.start()
refresh_problems.start()
check_contests.start()
bot.run(bot_token)
