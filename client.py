import discord
from discord.ext import commands, tasks
from auth import bot_token, cat_api
import requests
import json
import random as rand
from time import time
from datetime import datetime
import pytz
import wikipedia
import urllib
from sympy.parsing.sympy_parser import parse_expr

statuses = ('implementation', 'dynamic programming', 'graph theory', 'data structures', 'trees', 'geometry', 'strings', 'optimization')
replies = ('Practice Bot believes that with enough practice, you can complete any goal!', 'Keep practicing! Practice Bot says that every great programmer starts somewhere!', 'Hey now, you\'re an All Star, get your game on, go play (and practice)!',
           'Stuck on a problem? Every logical problem has a solution. You just have to keep practicing!', ':heart:')
with open('data/notification_channels.json', 'r', encoding='utf8', errors='ignore') as f:
    data = json.load(f)
contest_channels = data['contest_channels']
input_index = 0

dmoj_problems = None
cf_problems = None
at_problems = None

problems_by_points = {'dmoj':{}, 'cf':{}, 'at':{}}

def get(api_url):
    response = requests.get(api_url)

    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    return None

prefix = '!'
bot = commands.Bot(command_prefix=prefix)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! (ponged in %ss)' % str(round(bot.latency, 3)))

@bot.command()
async def random(ctx, oj=None, points=None, maximum=None):
    global problems_by_points, dmoj_problems, cf_problems, at_problems
    start = time()
    
    if oj is None:
        oj = rand.choice(('dmoj', 'cf', 'at'))
    if points is not None:
        if not points.isdigit():
            await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%srandom <online judge> <points>` (dmoj/codeforces/atcoder).' % prefix)
            return
        points = int(points)

    if maximum is not None:
        if not maximum.isdigit():
            await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%srandom <online judge> <minimum> <maximum>` (dmoj/codeforces/atcoder).' % prefix)
            return
        maximum = int(maximum)
        possibilities = []
        for point in list(problems_by_points[oj].keys()):
            if point >= points and point <= maximum:
                possibilities.append(point)
        if len(possibilities) == 0:
            await ctx.send(ctx.message.author.mention + ' Sorry, I couldn\'t find any problems with those parameters. :cry:')
            return
        points = rand.choice(possibilities)
        
    if oj.lower() == 'dmoj':
        if not dmoj_problems:
            await ctx.send(ctx.message.author.mention + ' There seems to be a problem with the DMOJ API. Please try again later :shrug:')
            return
        if points is None:
            name, prob = rand.choice(list(dmoj_problems.items()))
        elif points in problems_by_points['dmoj']:
            name, prob = rand.choice(list(problems_by_points['dmoj'][points].items()))
        else:
            await ctx.send(ctx.message.author.mention + ' Sorry, I couldn\'t find any problems with those parameters. :cry:')
            return
        url = 'https://dmoj.ca/problem/' + name
        embed = discord.Embed(title=prob['name'], description=url +' (searched in %ss)' % str(round(bot.latency, 3)))
        embed.timestamp = datetime.utcnow()
        embed.add_field(name='Points', value=prob['points'], inline=False)
        embed.add_field(name='Partials', value=('Yes' if prob['partial'] else 'No'), inline=False)
        embed.add_field(name='Group', value=prob['group'], inline=False)
        await ctx.send(ctx.message.author.mention, embed=embed)
        
    elif oj.lower() == 'cf' or oj.lower() == 'codeforces':
        if not cf_problems:
            await ctx.send(ctx.message.author.mention + ' There seems to be a problem with the Codeforces API. Please try again later :shrug:')
            return
        if points is None:
            prob = rand.choice(cf_problems)
        elif points in problems_by_points['cf']:
            prob = rand.choice(problems_by_points['cf'][points])
        else:
            await ctx.send(ctx.message.author.mention + ' Sorry, I couldn\'t find any problems with those parameters. :cry:')
            return
        url = 'https://codeforces.com/problemset/problem/' + str(prob['contestId']) + '/' + str(prob['index'])
        embed = discord.Embed(title=prob['name'], description=url +' (searched in %ss)' % str(round(bot.latency, 3)))
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
        if points is None:
            prob = rand.choice(at_problems)
        elif points in problems_by_points['at']:
            prob = rand.choice(problems_by_points['at'][points])
        else:
            await ctx.send(ctx.message.author.mention + ' Sorry, I couldn\'t find any problems with those parameters. :cry:')
            return
        url = 'https://atcoder.jp/contests/' + prob['contest_id'] + '/tasks/' + prob['id']
        embed = discord.Embed(title=prob['title'], description=url +' (searched in %ss)' % str(round(bot.latency, 3)))
        embed.timestamp = datetime.utcnow()
        if prob['point']:
            embed.add_field(name='Points', value=prob['point'], inline=False)
        embed.add_field(name='Solver Count', value=prob['solver_count'], inline=False)
        await ctx.send(ctx.message.author.mention, embed=embed)

    else:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%srandom <online judge> <points>` (dmoj/codeforces/atcoder).' % prefix)

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
async def whatis(ctx, *, name=None):
    start = time()
    if name is None:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%swhatis <thing>`.' % prefix)
        return
    page, summary = getSummary(name.replace(' ', '_'))
    if summary is None:
        await ctx.send(ctx.message.author.mention + ' Sorry, I couldn\'t find anything on "%s"' % name)
        return
    embed = discord.Embed(title=page.title, description=page.url+' (searched in %ss)' % str(round(bot.latency, 3)))
    embed.timestamp = datetime.utcnow()
    embed.add_field(name='Summary', value=summary, inline=False)
    await ctx.send(ctx.message.author.mention + ' Here\'s what I found!', embed=embed)

def valid(url):
    try:
        if urllib.request.urlopen(url).getcode() == 200:
            return True
        else:
            return False
    except:
        return False

@bot.command()
async def whois(ctx, *, name=None):
    start = time()
    if name is None:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%swhois <name>`.' % prefix)
        return
    accounts = {}
    if valid('https://dmoj.ca/api/user/info/%s' % name):
        accounts['DMOJ'] = 'https://dmoj.ca/user/%s' % name
    cf_data = get('https://codeforces.com/api/user.info?handles=%s' % name)
    if cf_data is not None and cf_data['status'] == 'OK':
        accounts['Codeforces'] = 'https://codeforces.com/profile/%s' % name
    if valid('https://atcoder.jp/users/%s' % name):
        accounts['AtCoder'] = 'https://atcoder.jp/users/%s' % name
    if valid('https://wcipeg.com/user/%s' % name):
        accounts['WCIPEG'] = 'https://wcipeg.com/user/%s' % name
    if valid('https://github.com/%s' % name):
        accounts['GitHub'] = 'https://github.com/%s' % name
    if len(accounts) == 0:
        await ctx.send(ctx.message.author.mention + ' Sorry, found 0 results for %s' % name)
        return
    embed = discord.Embed(title=name, description=' (searched in %ss)' % str(round(bot.latency, 3)))
    embed.timestamp = datetime.utcnow()
    for oj, url in accounts.items():
        embed.add_field(name=oj, value=url, inline=False)
    await ctx.send(ctx.message.author.mention + ' Found %d result(s) for `%s`' % (len(accounts), name), embed=embed)

@bot.command()
async def cat(ctx):
    data = get('https://api.thecatapi.com/v1/images/search?x-api-key=' + cat_api)
    await ctx.send(ctx.message.author.mention + ' :smiley_cat: ' + data[0]['url'])

@bot.command()
@commands.has_permissions(administrator=True)
async def notify(ctx, channel=None):
    global contest_channels
    if channel is None:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%snotify <channel>`.' % prefix)
        return
    iden = int(channel[2:-1])
    if iden in contest_channels:
        await ctx.send(ctx.message.author.mention + ' That channel is already a contest notification channel.')
        return
    for chan in ctx.guild.text_channels:
        if chan.id == iden:
            contest_channels.append(iden)
            with open('data/notification_channels.json', 'w') as json_file:
                json.dump({'contest_channels':contest_channels}, json_file)
            await ctx.send(chan.mention + ' set to a contest notification channel.')
            return
    await ctx.send(ctx.message.author.mention + ' It seems like that channel does not exist.')

@notify.error
async def notify_error(error, ctx):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(ctx.message.author.mention +' Sorry, you don\'t have permissions to set a contest notification channel.')

@bot.command()
@commands.has_permissions(administrator=True)
async def unnotify(ctx, channel=None):
    global contest_channels
    if channel is None:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%sunnotify <channel>`.' % prefix)
        return
    iden = int(channel[2:-1])
    if iden in contest_channels:
        for chan in ctx.guild.text_channels:
            if chan.id == iden:
                contest_channels.remove(iden)
                with open('data/notification_channels.json', 'w') as json_file:
                    json.dump({'contest_channels':contest_channels}, json_file)
                await ctx.send(chan.mention + ' is no longer a contest notification channel.')
                return
    else:
        await ctx.send('That channel either does not exist or is not a contest notification channel.')
       
@unnotify.error
async def unnotify_error(error, ctx):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(ctx.message.author.mention +' Sorry, you don\'t have permissions to remove a contest notification channel.')

@bot.command()
async def calc(ctx, *, expression):
    try:
        solution = str(parse_expr(expression))
        await ctx.send(ctx.message.author.mention + ' `' + solution + '`')
    except:
        await ctx.send(ctx.message.author.mention + ' There seems to be an error with that expression.')
                    
@tasks.loop(minutes=30)
async def status_change():
    await bot.change_presence(activity=discord.Game(name='with %s' % rand.choice(statuses)))

@status_change.before_loop
async def status_change_before():
    await bot.wait_until_ready()

@tasks.loop(hours=3)
async def refresh_problems():
    global dmoj_problems, cf_problems, at_problems
    problems = get('https://dmoj.ca/api/problem/list')
    if problems is not None:
        dmoj_problems = problems
        problems_by_points['dmoj'] = {}
        for name, details in problems.items():
            if details['points'] not in problems_by_points['dmoj']:
                problems_by_points['dmoj'][details['points']] = {}
            problems_by_points['dmoj'][details['points']][name] = details
    cf_data = get('https://codeforces.com/api/problemset.problems')
    if cf_data is not None:
        try:
            cf_problems = cf_data['result']['problems']
            for details in cf_problems:
                if 'points' in details.keys():
                    if details['points'] not in problems_by_points['cf']:
                        problems_by_points['cf'][details['points']] = []
                    problems_by_points['cf'][details['points']].append(details)
        except KeyError:
            pass
    problems = get('https://kenkoooo.com/atcoder/resources/merged-problems.json')
    if problems is not None:
        at_problems = problems
        for details in problems:
            if details['point']:
                if details['point'] not in problems_by_points['at']:
                    problems_by_points['at'][details['point']] = []
                problems_by_points['at'][details['point']].append(details)

@refresh_problems.before_loop
async def refresh_problems_before():
    await bot.wait_until_ready()

@tasks.loop(minutes=5)
async def check_contests():
    contests = get('https://dmoj.ca/api/contest/list')
    if contests is not None:
        with open('data/dmoj_contests.json', 'r', encoding='utf8', errors='ignore') as f:
            prev_contests = json.load(f)
        for contest in range(max(len(prev_contests), len(contests)-5), len(contests)):
            name, details = list(contests.items())[contest]
            if datetime.strptime(details['start_time'].replace(':', ''), '%Y-%m-%dT%H%M%S%z') > datetime.now(pytz.utc):
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
        with open('data/dmoj_contests.json', 'w') as json_file:
            json.dump(contests, json_file)

    contests = get('https://codeforces.com/api/contest.list')
    if contests is not None and contests['status'] == 'OK':
        with open('data/cf_contests.json', 'r', encoding='utf8', errors='ignore') as f:
            prev_contests = json.load(f)
        for contest in range(min(5, len(contests['result'])-len(prev_contests['result']))):
            details = contests['result'][contest]
            if details['phase'] != 'FINISHED':
                url = 'https://codeforces.com/contest/' + str(details['id'])
                embed = discord.Embed(title=(':trophy: %s' % details['name']), description=url)
                embed.add_field(name='Type', value=details['type'], inline=False)
                embed.add_field(name='Start Time', value=datetime.utcfromtimestamp(details['startTimeSeconds']).strftime('%Y-%m-%d %H:%M:%S'), inline=False)
                embed.add_field(name='Time Limit', value='%s:%s:%s' % (str(details['durationSeconds']//(24*3600)).zfill(2), str(details['durationSeconds']%(24*3600)//3600).zfill(2), str(details['durationSeconds']%3600//60).zfill(2)), inline=False)
                for channel_id in contest_channels:
                    ctx = bot.get_channel(channel_id)
                    await ctx.send(embed=embed)
        with open('data/cf_contests.json', 'w') as json_file:
            json.dump(contests, json_file)

    contests = get('https://atcoder-api.appspot.com/contests')
    if contests is not None:
        with open('data/at_contests.json', 'r', encoding='utf8', errors='ignore') as f:
            prev_contests = json.load(f)
        for contest in range(max(len(prev_contests), len(contests)-5), len(contests)):
            details = contests[contest]
            if details['startTimeSeconds'] > time():
                url = 'https://atcoder.jp/contests/' + details['id']
                embed = discord.Embed(title=(':trophy: %s' % details['title'].replace('\n', '').replace('\t', '').replace('◉', '')), description=url)
                embed.add_field(name='Start Time', value=datetime.utcfromtimestamp(details['startTimeSeconds']).strftime('%Y-%m-%d %H:%M:%S'), inline=False)
                embed.add_field(name='Time Limit', value='%s:%s:%s' % (str(details['durationSeconds']//(24*3600)).zfill(2), str(details['durationSeconds']%(24*3600)//3600).zfill(2), str(details['durationSeconds']%3600//60).zfill(2)), inline=False)
                embed.add_field(name='Rated Range', value=details['ratedRange'], inline=False)
                for channel_id in contest_channels:
                    ctx = bot.get_channel(channel_id)
                    await ctx.send(embed=embed)
        with open('data/at_contests.json', 'w') as json_file:
            json.dump(contests, json_file)
            
@check_contests.before_loop
async def check_contests_before():
    await bot.wait_until_ready()

bot.remove_command('help')

@bot.command()
async def help(ctx):
    embed = discord.Embed(title='Practice Bot', description='The all-competitive-programming-purpose Discord bot!', color=0xeee657)
    embed.add_field(name='%shelp' % prefix, value='Sends you a list of my commands (obviously)', inline=False)
    embed.add_field(name='%srandom' % prefix, value='Gets a random problem from DMOJ, Codeforces, or AtCoder', inline=False)
    embed.add_field(name='%srandom <online judge>' % prefix, value='Gets a random problem from a specific online judge (DMOJ, Codeforces, or AtCoder)', inline=False)
    embed.add_field(name='%srandom <online judge> <points>' % prefix, value='Gets a random problem from a specific online judge (DMOJ, Codeforces, or AtCoder) with a specific number of points', inline=False)
    embed.add_field(name='%srandom <online judge> <minimum> <maximum>' % prefix, value='Gets a random problem from a specific online judge (DMOJ, Codeforces, or AtCoder) with a specific point range', inline=False)
    embed.add_field(name='%swhois <name>' % prefix, value='Searches for a user on 4 online judges (DMOJ, Codeforces, AtCoder, WCIPEG) and GitHub', inline=False)
    embed.add_field(name='%swhatis <query>' % prefix, value='Searches for something on Wikipedia', inline=False)
    embed.add_field(name='%snotify <channel>' % prefix, value='Sets a channel as a contest notification channel (requires admin)', inline=False)
    embed.add_field(name='%sunnotify <channel> % prefix', value='Sets a channel to be no longer a contest notification channel (requires admin)', inline=False)
    embed.add_field(name='%smotivation' % prefix, value='Sends you some (emotional) support :smile:', inline=False)
    embed.add_field(name='%scat' % prefix, value='Gets a random cat image', inline=False)
    embed.add_field(name='%sping' % prefix, value='Checks my ping to the Discord server', inline=False)
    await ctx.message.author.send(embed=embed)
    await ctx.send(ctx.message.author.mention + ' I\'ve sent you a list of my commands to your DM!')

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
