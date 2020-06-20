import discord
from discord.ext import commands, tasks
from auth import bot_token, dev_token, cat_api, client_id, client_secret, USERNAME, PASSWORD, dbl_token
import requests
import json
import random as rand
from time import time
from datetime import datetime, date
import pytz
import urllib
import secrets
from dmoj.session import Session, InvalidSessionException
from dmoj.language import Language
import utils.dblapi as dblapi
import utils.wiki as wiki
import utils.email as email
import utils.scraper as scraper
from utils.problem_streamer import RandomProblem, accounts, NoSuchOJException, InvalidParametersException, OnlineJudgeHTTPException, InvalidQueryException
from utils.contest_streamer import RandomContests, Contest, NoContestsAvailableException
import bs4 as bs


suggesters = []
suggester_times = []

rank_times = {}

statuses = ('implementation', 'dynamic programming', 'graph theory', 'data structures', 'trees', 'geometry', 'strings', 'optimization')
replies = ('Practice Bot believes that with enough practice, you can complete any goal!', 'Keep practicing! Practice Bot says that every great programmer starts somewhere!', 'Hey now, you\'re an All Star, get your game on, go play (and practice)!',
           'Stuck on a problem? Every logical problem has a solution. You just have to keep practicing!', ':heart:')

wait_time = 0

with open('data/daily.json', 'r', encoding='utf8', errors='ignore') as f:
    daily_problems = json.load(f)

problemUser = RandomProblem()
contestUser = RandomContests()

with open('data/contests.json', 'r', encoding='utf8', errors='ignore') as f:
    prev_contest_data = json.load(f)
    contest_cache = []
    for data in prev_contest_data:
        contest_cache.append(Contest(data))

with open('data/users.json', 'r', encoding='utf8', errors='ignore') as f:
    problemUser.global_users = json.load(f)

with open('data/subscriptions.json', 'r', encoding='utf8', errors='ignore') as f:
    subscribed_channels = list(map(int, json.load(f)))

with open('data/server_roles.json', 'r', encoding='utf8', errors='ignore') as f:
    server_roles = list(map(int, json.load(f)))

def update_daily():
    global daily_problems
    with open('data/daily.json', 'w') as json_file:
        json.dump(daily_problems, json_file)

def update_contest_cache():
    global contest_cache
    with open('data/contests.json', 'w') as json_file:
        prev_contest_data = []
        for contest in contest_cache:
            prev_contest_data.append(contest.asdict())
        json.dump(prev_contest_data, json_file)

def update_users():
    global problemUser
    with open('data/users.json', 'w') as json_file:
        json.dump(problemUser.global_users, json_file)

def update_subscribed_channels():
    global subscribed_channels
    with open('data/subscriptions.json', 'w') as json_file:
        json.dump(subscribed_channels, json_file)

def update_server_roles():
    global server_roles
    with open('data/server_roles.json', 'w') as json_file:
        json.dump(server_roles, json_file)

sessions = {}

ratings = {
    range(3000, 4000): ('Target', discord.Colour(int('ee0000', 16))),
    range(2200, 2999): ('Grandmaster', discord.Colour(int('ee0000', 16))),
    range(1800, 2199): ('Master', discord.Colour(int('ffb100', 16))),
    range(1500, 1799): ('Candidate Master', discord.Colour(int('993399', 16))),
    range(1200, 1499): ('Expert', discord.Colour(int('5597ff', 16))),
    range(1000, 1199): ('Amateur', discord.Colour(int('4bff4b', 16))),
    range(0, 999): ('Newbie', discord.Colour(int('999999', 16))),
    (None,): ('Unrated', discord.Colour.default()),
}

def json_get(api_url):
    response = requests.get(api_url)

    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    return None

def post(api_url, data, headers):
    response = requests.post(api_url, json=data, headers=headers)
    return response.json()

def checkExistingUser(user):
    global problemUser
    if str(user.id) not in problemUser.global_users:
        problemUser.global_users[str(user.id)] = {}
    else:
        return True
    update_users()
    return False    

prefix = '$'
bot = commands.Bot(command_prefix=prefix,
                   description='The all-competitive-programming-purpose Discord bot!',
                   owner_id=492435232071483392)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! (ponged in %ss)' % str(round(bot.latency, 3)))

@bot.command()
async def suggest(ctx, *, content):

    if ctx.message.author.id in suggesters and time() - suggester_times[suggesters.index(ctx.message.author.id)] < 3600:
        await ctx.send(ctx.message.author.mention + ' Please wait %d minutes before making another suggestion!' % int((3600 - time() + suggester_times[suggesters.index(ctx.message.author.id)])//60))
        return

    try:
        email.send(ctx.message.author, content)
        if ctx.message.author.id in suggesters:
            suggester_times[suggesters.index(ctx.message.author.id)] = time()
        else:
            suggesters.append(ctx.message.author.id)
            suggester_times.append(time())
        await ctx.send(ctx.message.author.mention + ' Suggestion sent!\n```From: You\nTo: The Dev\nAt: ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + '\n' + content + '```')

    except:
        await ctx.send(ctx.message.author.mention + ' Failed to send that suggestion.')

@bot.command()
async def random(ctx, oj=None, points=None, maximum=None):
    global problemUser
    iden = str(ctx.message.author.id)
    checkExistingUser(ctx.message.author)
    if isinstance(oj, str) and (oj.lower() == 'peg' or oj.lower() == 'wcipeg'):
        await ctx.send(ctx.message.author.mention + ' Notice: Starting from July 31, 2020 support for WCIPEG may be discontinued as **PEG Judge will shut down at the end of July**\nhttps://wcipeg.com/announcement/9383')
    try:
        title, description, embed = problemUser.get_random_problem(oj, points, maximum, iden)
        embed.title = title
        embed.description = description + ' (searched in %ss)' % str(round(bot.latency, 3))
        embed.timestamp = datetime.utcnow()
        await ctx.send(ctx.message.author.mention, embed=embed)
    except NoSuchOJException:
        await ctx.send(ctx.message.author.mention + ' Invalid query. The online judge must be one of the following: DMOJ (dmoj), Codeforces (codeforces/cf), AtCoder (atcoder/at), WCIPEG (wcipeg/peg).')
    except InvalidParametersException:
        await ctx.send(ctx.message.author.mention + ' Sorry, I couldn\'t find any problems with those parameters. :cry:')
    except OnlineJudgeHTTPException as e:
        await ctx.send(ctx.message.author.mention + ' There seems to be a problem with %s. Please try again later :shrug:' % str(e))
    except InvalidQueryException:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Make sure your points are positive integers.')

url_to_thumbnail = {
    'https://dmoj.ca/problem/': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/dmoj-thumbnail.png',
    'https://codeforces.com/problemset/problem/': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/cf-thumbnail.png',
    'https://atcoder.jp/contests/': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/at-thumbnail.png',
    'https://wcipeg.com/problem/': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/peg-thumbnail.png'
}

@bot.command()
async def daily(ctx):
    if str(date.today()) not in daily_problems.keys():
        title, description, embed = problemUser.get_random_problem()
        thumbnail = 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/logo.png'
        for url, tn in list(url_to_thumbnail.items()):
            if url in description:
                thumbnail = tn
                break
        daily_problems[str(date.today())] = {
            'title': title,
            'description': description,
            'thumbnail': thumbnail
        }
        update_daily()
    problem_data = daily_problems[str(date.today())]
    embed = discord.Embed(title=problem_data['title'], description=problem_data['description'])
    embed.set_thumbnail(url=problem_data['thumbnail'])
    embed.timestamp = datetime.utcnow()
    await ctx.send(ctx.message.author.mention + ' Hello! Here\'s today\'s problem of the day!', embed=embed)

@bot.command()
async def motivation(ctx):
    await ctx.send(ctx.message.author.mention + ' ' + rand.choice(replies))
    
@bot.command()
async def whatis(ctx, *, name=None):
    if name is None:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%swhatis <thing>`.' % prefix)
        return
    peg_res = scraper.wcipegScrape(name)
    if peg_res is not None:
        title, summary, url = peg_res
        embed = discord.Embed(title=title, description=url + ' (searched in %ss)' % str(round(bot.latency, 3)))
        embed.timestamp = datetime.utcnow()
        embed.add_field(name='Summary', value=summary, inline=False)
        await ctx.send(ctx.message.author.mention + ' Here\'s what I found!', embed=embed)
        return
    page, summary = wiki.getSummary(name.replace(' ', '_'))
    if summary is None:
        await ctx.send(ctx.message.author.mention + ' Sorry, I couldn\'t find anything on "%s"' % name)
        return
    embed = discord.Embed(title=page.title, description=page.url+' (searched in %ss)' % str(round(bot.latency, 3)))
    embed.timestamp = datetime.utcnow()
    embed.add_field(name='Summary', value=summary, inline=False)
    await ctx.send(ctx.message.author.mention + ' Here\'s what I found!', embed=embed)

@bot.command()
async def whois(ctx, *, name=None):
    if name is None:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%swhois <name>`.' % prefix)
        return
    accounts = scraper.accountScrape(name)
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
    if rand.randint(0, 100) == 0:
        data = [{'url':'https://media.discordapp.net/attachments/511001840071213067/660303090444140545/539233495000809475.png'}]
    else:
        data = json_get('https://api.thecatapi.com/v1/images/search?x-api-key=' + cat_api)
    await ctx.send(ctx.message.author.mention + ' :smiley_cat: ' + data[0]['url'])

@bot.command()
@commands.guild_only()
async def tea(ctx, user=None):
    global problemUser
    if user is None:
        if not checkExistingUser(ctx.message.author):
            await ctx.send(ctx.message.author.mention + ' You have 0 cups of :tea:.')
            return
        if problemUser.global_users[str(ctx.message.author.id)].get('tea', 0) == 1:
            await ctx.send(ctx.message.author.mention + ' You have 1 cup of :tea:.')
        else:
            await ctx.send(ctx.message.author.mention + ' You have ' + str(problemUser.global_users[str(ctx.message.author.id)].get('tea', 0)) + ' cups of :tea:.')
        return
    user = user.strip()
    if not user[3:-1].isdigit():
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%stea <user>`.' % prefix)
        return
    iden = int(user[3:-1])
    if iden == ctx.message.author.id:
        await ctx.send(ctx.message.author.mention + ' Sorry, cannot send :tea: to yourself!')
        return
    elif iden == bot.user.id:
        await ctx.send(ctx.message.author.mention + ' Thanks for the :tea:!')
        return
    for member in ctx.guild.members:
        if member.id == iden:
            checkExistingUser(member)
            problemUser.global_users[str(iden)]['tea'] = problemUser.global_users[str(iden)].get('tea', 0) + 1
            update_users()
            await ctx.send(ctx.message.author.mention + ' sent a cup of :tea: to ' + member.mention)
            return
    await ctx.send(ctx.message.author.mention + ' It seems like that user does not exist.')

@bot.command()
async def toggleRepeat(ctx):
    global problemUser
    checkExistingUser(ctx.message.author)
    iden = str(ctx.message.author.id)
    for account in accounts:
        if account in problemUser.global_users[iden]:
            problemUser.global_users[iden]['repeat'] = not problemUser.global_users[iden].get('repeat', True)
            update_users()
            await ctx.send(ctx.message.author.mention + ' Repeat setting for command `%srandom` set to %s.' % (prefix, ('ON' if problemUser.global_users[iden]['repeat'] else 'OFF')))
            return
    await ctx.send(ctx.message.author.mention + ' You are not linked to any accounts')

@bot.command()
@commands.guild_only()
async def profile(ctx, user: discord.User=None):
    global problemUser
    if user is None:
        user = ctx.message.author
    checkExistingUser(user)
    embed = discord.Embed(title=user.display_name, description=user.mention)
    embed.timestamp = datetime.utcnow()
    embed.add_field(name='Discord ID', value=user.id, inline=False)
    if 'dmoj' in problemUser.global_users[str(user.id)]:
        embed.add_field(name='DMOJ', value='https://dmoj.ca/user/%s' % problemUser.global_users[str(user.id)].get('dmoj', 'This user has no connected DMOJ account'), inline=False)
    await ctx.send(ctx.message.author.mention, embed=embed)

@bot.command()
async def run(ctx, lang=None, stdin=None, *, script=None):
    global wait_time
    if lang is None or stdin is None or script is None:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%srun <language> "<stdin>" <script>`.' % prefix)
        return
    headers = {'Content-type':'application/json', 'Accept':'application/json'}
    credit_spent = post('https://api.jdoodle.com/v1/credit-spent', {'clientId': client_id, 'clientSecret': client_secret}, headers)
    if 'error' not in credit_spent and credit_spent['used'] >= 200:
        await ctx.send(ctx.message.author.mention + ' Sorry, the daily limit of compilations has been surpassed (200). Please wait until 12:00 AM UTC')
        return
    if time() - wait_time < 15:
        await ctx.send(ctx.message.author.mention + ' Queue in process, please wait %d seconds' % (15 - (time() - wait_time)))
        return
    wait_time = time()
    lang = lang.lower()
    script = script.replace('`', '')
    data = {
        'clientId': client_id,
        'clientSecret': client_secret,
        'script': script,
        'stdin': stdin,
        'language': lang,
        'versionIndex': 0
        }
    response = post('https://api.jdoodle.com/v1/execute', data, headers)
    if 'error' in response and response['statusCode'] == 400:
        await ctx.send(ctx.message.author.mention + ' Invalid request. Perhaps the language you\'re using is unavailable.')
    elif 'error' in response:
        await ctx.send(ctx.message.author.mention + ' Compilation failed. The compiler may be down.')
    else:
        message = '\n'
        message += 'CPU Time: `' + ((str(response['cpuTime']) + 's') if response['cpuTime'] is not None else 'N/A') + '`\n'
        message += 'Memory: `' + ((str(response['memory']) + 'KB') if response['memory'] is not None else 'N/A') + '`\n'
        if len(message + '\n```' + response['output'] + '```') > 2000:
            with open('data/solution.txt', 'w+') as f:
                f.write(response['output'])
            await ctx.send(ctx.message.author.mention + message + '\n That\'s a really long output, I put it in this file for you.', file=discord.File('data/solution.txt', 'output.txt'))    
        else:
            if len(response['output']) > 0:
                message += '\n```' + response['output'] + '```'
            else:
                message += '\n```\n```'
            await ctx.send(ctx.message.author.mention + message)

@bot.command()
async def login(ctx, site=None, token=None):
    global sessions, problemUser
    if ctx.guild is not None:
        await ctx.send(ctx.message.author.mention + ' Please do not post your DMOJ API token on a server! Login command should be used in DMs only!')
    else:
        if site is None or token is None:
            await ctx.send('Invalid query. Please use format `%slogin <site> <token>`.' % prefix)
            return
        checkExistingUser(ctx.message.author)
        if site.lower() == 'dmoj':
            iden = str(ctx.message.author.id)
            try:
                sessions[ctx.message.author.id] = Session(token)
                problemUser.global_users[iden]['dmoj'] = str(sessions[ctx.message.author.id])
                update_users()
                await ctx.send('Successfully logged in with submission permissions as %s! (Note that for security reasons, you will be automatically logged out after the cache resets. You may delete the message containing your token now)' % sessions[ctx.message.author.id])
            except InvalidSessionException:
                await ctx.send('Token invalid, failed to log in (your DMOJ API token can be found by going to https://dmoj.ca/edit/profile/ and selecting the __Regenerate__ option next to API Token). Note: The login command will ONLY WORK IN DIRECT MESSAGE. Please do not share this token with anyone else.')
        elif site.lower() in ('cf', 'codeforces', 'atcoder'):
            await ctx.send('Sorry, logins to that site is not available yet')

language = Language()

@bot.command()
async def submit(ctx, problem=None, lang=None, *, source=None):
    global sessions, problemUser
    if ctx.message.author.id not in sessions.keys():
        await ctx.send(ctx.message.author.mention + ' You are not logged in to a DMOJ account with submission permissions (this could happen if you last logged in a long time ago). Please use command `%slogin dmoj <token>` (your DMOJ API token can be found by going to https://dmoj.ca/edit/profile/ and selecting the __Regenerate__ option next to API Token). Note: The login command will ONLY WORK IN DIRECT MESSAGE. Please do not share this token with anyone else.' % prefix)
        return
    userSession = sessions[ctx.message.author.id]
    if not language.languageExists(lang):
        await ctx.send(ctx.message.author.mention + ' That language is not available. The available languages are as followed: ```%s```' % ', '.join(language.getLanguages()))
        return
    try:
        if source is None and len(ctx.message.attachments) > 0:
            f = requests.get(ctx.message.attachments[0].url)
            source = f.content
        iden = str(ctx.message.author.id)
        checkExistingUser(ctx.message.author)
        if problem == '^' and 'last_dmoj_problem' in problemUser.global_users[iden]:
            problem = problemUser.global_users[iden]['last_dmoj_problem']
        id = userSession.submit(problem, language.getId(lang), source)
        response = userSession.getTestcaseStatus(id)
        responseText = str(response)
        if len(responseText) > 1950:
            responseText = responseText[1950:] + '\n(Result cut off to fit message length limit)'
        await ctx.send(ctx.message.author.mention + ' ' + responseText + '\nTrack your submission here: https://dmoj.ca/submission/' + str(id))
    except InvalidSessionException:
        await ctx.send(ctx.message.author.mention + ' Failed to connect, or problem not available.')
    except:
        await ctx.send(ctx.message.author.mention + ' Failed to connect, or problem not available.')

@bot.command()
async def contests(ctx, numstr='1'):
    global contestUser
    if numstr == 'all':
        number = len(contestUser.all_contest_embeds)
    else:
        number = int(numstr)
    try:
        contestList = contestUser.get_random_contests(number)
        await ctx.send(ctx.message.author.mention + ' Sending %d random upcoming contest(s). Last fetched, %d minutes ago' % (len(contestList), (time()-contestUser.fetch_time)//60))
        for contest in contestList:
            await ctx.send(embed=contest)
    except NoContestsAvailableException:
        await ctx.send(ctx.message.author.mention + ' Sorry, there are not upcoming contests currently available.')

@bot.command()
@commands.has_permissions(manage_channels=True)
@commands.guild_only()
async def sub(ctx, channel: discord.TextChannel):
    global subscribed_channels
    if channel.id in subscribed_channels:
        await ctx.send(ctx.message.author.mention + ' That channel is already subscribed to contest notifications.')
        return
    subscribed_channels.append(channel.id)
    update_subscribed_channels()
    await ctx.send(channel.mention + ' subscribed to contest notifications.')

@bot.command()
@commands.guild_only()
async def subs(ctx):
    global subscribed_channels
    clist = ctx.message.author.mention + ' Contest notification channels in this server:\n'
    for text_channel in ctx.message.guild.text_channels:
        if text_channel.id in subscribed_channels:
            clist += text_channel.mention + '\n'
    if clist == ctx.message.author.mention + ' Contest notification channels in this server:\n':
        await ctx.send(ctx.message.author.mention + ' There are no channels subscribed to contest notifications in this server :slight_frown:')
    else:
        await ctx.send(clist)

@bot.command()
@commands.has_permissions(manage_channels=True)
@commands.guild_only()
async def unsub(ctx, channel: discord.TextChannel):
    global subscribed_channels
    if int(channel.id) not in subscribed_channels:
        await ctx.send(ctx.message.author.mention + ' That channel is already not subscribed to contest notifications.')
        return
    subscribed_channels.remove(channel.id)
    update_subscribed_channels()
    await ctx.send(channel.mention + ' is no longer a contest notification channel.')

@tasks.loop(minutes=30)
async def status_change():
    await bot.change_presence(activity=discord.Game(name='with %s | %shelp' % (rand.choice(statuses), prefix)))

@status_change.before_loop
async def status_change_before():
    await bot.wait_until_ready()

@bot.command()
@commands.has_permissions(manage_roles=True)
@commands.guild_only()
async def toggleRanks(ctx):
    global server_roles
    if int(ctx.message.guild.id) not in server_roles:
        server_roles.append(int(ctx.message.guild.id))
        names = []
        for role in ctx.message.guild.roles:
            names.append(role.name)
        for role in list(ratings.values()):
            if role[0] not in names:
                await ctx.message.guild.create_role(name=role[0], colour=role[1], mentionable=False)
        await ctx.send(ctx.message.author.mention + ' DMOJ based ranked roles set to `ON`')
    else:
        server_roles.remove(int(ctx.message.guild.id))
        await ctx.send(ctx.message.author.mention + ' DMOJ based ranked roles set to `OFF`')
    update_server_roles()

@bot.command()
async def updateRank(ctx):
    global problemUser, rank_times, server_roles
    checkExistingUser(ctx.message.author)
    iden = str(ctx.message.author.id)
    if 'dmoj' not in problemUser.global_users[iden]:
        await ctx.send(ctx.message.author.mention + ' It seems that you have not logged in to DMOJ through this bot. Use `%shelp` to see the steps required to login.' % prefix)
        return
    lapsed = time() - rank_times.get(iden, 0)
    if lapsed < 24*60*60:
        wait = 24*60*60 - lapsed
        await ctx.send(ctx.message.author.mention + ' Please wait %d hours and %d minutes before requesting to update ranks again.' % (wait//(60*60), wait%(60*60)//60))
        return
    user_info = json_get('https://dmoj.ca/api/user/info/%s' % problemUser.global_users[iden]['dmoj'])
    current_rating = user_info['contests']['current_rating']
    for rating, role in list(ratings.items()):
        if current_rating in rating:
            rating_name = role[0]
    for guild in bot.guilds:
        if int(guild.id) not in server_roles:
            continue
        names = []
        for role in guild.roles:
            names.append(role.name)
        for role in list(ratings.values()):
            if role[0] not in names:
                await guild.create_role(name=role[0], colour=role[1], mentionable=False)
        try:
            for member in guild.members:
                if iden == str(member.id):
                    for rating, role in list(ratings.items()):
                        role = discord.utils.get(guild.roles, name=role[0])
                        if current_rating in rating and role not in member.roles:
                            await member.add_roles(role)
                        elif current_rating not in rating and role in member.roles:
                            await member.remove_roles(role)
                    break
        except:
            pass
    rank_times[iden] = time()
    await ctx.send(ctx.message.author.mention + ' Successfully updated your DMOJ rank to **%s** across all servers with DMOJ based ranks set to on!' % rating_name)

@tasks.loop(hours=3)
async def refresh_dmoj_problems():
    global problemUser
    problemUser.parse_dmoj_problems(json_get('https://dmoj.ca/api/problem/list'))
    
@refresh_dmoj_problems.before_loop
async def refresh_dmoj_problems_before():
    await bot.wait_until_ready()

@tasks.loop(hours=3)
async def refresh_cf_problems():
    global problemUser
    problemUser.parse_cf_problems(json_get('https://codeforces.com/api/problemset.problems'))

@refresh_cf_problems.before_loop
async def refresh_cf_problems_before():
    await bot.wait_until_ready()

@tasks.loop(hours=3)
async def refresh_atcoder_problems():
    global problemUser
    problemUser.parse_atcoder_problems(json_get('https://kenkoooo.com/atcoder/resources/merged-problems.json'))

@refresh_atcoder_problems.before_loop
async def refresh_atcoder_problems_before():
    await bot.wait_until_ready()

@tasks.loop(hours=3)
async def refresh_peg_problems():
    global problemUser
    problemUser.parse_peg_problems(requests.get('https://wcipeg.com/problems/show%3D999999'))

@refresh_peg_problems.before_loop
async def refresh_peg_problems_before():
    await bot.wait_until_ready()

@tasks.loop(minutes=5)
async def refresh_contests():
    global contestUser, contest_cache

    try:
        contestUser.reset_contest('dmoj')
        contestUser.parse_dmoj_contests(json_get('https://dmoj.ca/api/contest/list'))
    except:
        pass

    try:
        contestUser.reset_contest('cf')
        contestUser.parse_cf_contests(json_get('https://codeforces.com/api/contest.list'))
    except:
        pass

    try:
        contestUser.reset_contest('atcoder')
        contestUser.parse_atcoder_contests(json_get('https://atcoder-api.appspot.com/contests'))
    except:
        pass

    contestUser.set_time()
    contestUser.generate_stream()

    new_contests = list(set(contestUser.contest_objects).difference(set(contest_cache)))

    for channel_id in subscribed_channels:
        try:
            channel = bot.get_channel(channel_id)
            for contest in new_contests:
                await channel.send(embed=contestUser.embed_contest(contest.asdict()))
        except:
            pass

    contest_cache = list(set(contestUser.contest_objects).union(set(contest_cache)))
    update_contest_cache()

@refresh_contests.before_loop
async def check_contests_before():
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

status_change.start()
refresh_dmoj_problems.start()
refresh_cf_problems.start()
refresh_atcoder_problems.start()
refresh_peg_problems.start()
refresh_contests.start()
if bot_token != dev_token:
    dblapi.setup(bot, dbl_token)
bot.run(bot_token)
