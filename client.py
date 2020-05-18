import discord
from discord.ext import commands, tasks
from auth import bot_token, dev_token, cat_api, client_id, client_secret, USERNAME, PASSWORD, dbl_token
import requests
import json
import random as rand
from time import time
from datetime import datetime
import pytz
import wikipedia
import urllib
import secrets
from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText
from dmoj.session import Session, InvalidSessionException
from dmoj.language import Language
import utils.dblapi as dblapi
import bs4 as bs

SMTPserver = 'smtp.gmail.com'
suggesters = []
suggester_times = []

statuses = ('implementation', 'dynamic programming', 'graph theory', 'data structures', 'trees', 'geometry', 'strings', 'optimization')
replies = ('Practice Bot believes that with enough practice, you can complete any goal!', 'Keep practicing! Practice Bot says that every great programmer starts somewhere!', 'Hey now, you\'re an All Star, get your game on, go play (and practice)!',
           'Stuck on a problem? Every logical problem has a solution. You just have to keep practicing!', ':heart:')
with open('data/notification_channels.json', 'r', encoding='utf8', errors='ignore') as f:
    data = json.load(f)
contest_channels = data['contest_channels']
wait_time = 0
accounts = ('dmoj', 'codeforces', 'cf')

wcipeg_begin = '''Jump to:					<a href="#mw-head">navigation</a>, 					<a href="#p-search">search</a>
				</div>
				<div id="mw-content-text" lang="en" dir="ltr" class="mw-content-ltr"><p>'''

wcipeg_end = '''</p>
<div id="toc" class="toc"><div id="toctitle"><h2>Contents</h2></div>'''

head_begin = '''<h1 id="firstHeading" class="firstHeading" lang="en">'''
head_end = '''</h1>
						<div id="bodyContent" class="mw-body-content">
									<div id="siteSub">From PEGWiki</div>
								<div id="contentSub"></div>
												<div id="jump-to-nav" class="mw-jump">'''

with open('data/users.json', 'r', encoding='utf8', errors='ignore') as f:
    global_users = json.load(f)
    
dmoj_problems = None
cf_problems = None
at_problems = None
peg_problems = {}

problems_by_points = {'dmoj':{}, 'cf':{}, 'at':{}, 'peg':{}}

sessions = {}

ratings = {range(3000, 4000): ('Target', discord.Colour(int('ee0000', 16))),
           range(2200, 2999): ('Grandmaster', discord.Colour(int('ee0000', 16))),
           range(1800, 2199): ('Master', discord.Colour(int('ffb100', 16))),
           range(1500, 1799): ('Candidate Master', discord.Colour(int('993399', 16))),
           range(1200, 1499): ('Expert', discord.Colour(int('5597ff', 16))),
           range(1000, 1199): ('Amateur', discord.Colour(int('4bff4b', 16))),
           range(0, 999): ('Newbie', discord.Colour(int('999999', 16))),
           (None,): ('Unrated', discord.Colour.default()),
           }

def get(api_url):
    response = requests.get(api_url)

    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    return None

def post(api_url, data, headers):
    response = requests.post(api_url, json=data, headers=headers)
    return response.json()

def wget(url):
    response = requests.get(url)
    return response.text

def updateUsers():
    global global_users
    with open('data/users.json', 'w') as json_file:
        json.dump(global_users, json_file)

def checkExistingUser(user):
    global global_users
    if str(user.id) not in global_users:
        global_users[str(user.id)] = {}
    else:
        return True
    updateUsers()
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
        await ctx.send(ctx.message.author.mention + ' Please wait ' + str(int((3600 - time() + suggester_times[suggesters.index(ctx.message.author.id)])//60)) + ' minutes before making another suggestion!')
        return
    
    text_subtype = 'plain'

    subject = 'Suggestion from user %s (id %d)' % (ctx.message.author.display_name, ctx.message.author.id)
    sender = 'interface.practice.bot@gmail.com'
    destination = ['dev.practice.bot@gmail.com']

    try:
        msg = MIMEText(content, text_subtype)
        msg['Subject'] = subject
        msg['From'] = sender
        conn = SMTP(SMTPserver)
        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)
        try:
            conn.sendmail(sender, destination, msg.as_string())
        finally:
            conn.quit()
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
    global problems_by_points, dmoj_problems, cf_problems, at_problems, peg_problems, global_users
    start = time()
    
    if oj is None:
        oj = rand.choice(('dmoj', 'cf', 'at', 'peg'))

    iden = str(ctx.message.author.id)
    checkExistingUser(ctx.message.author)
    temp_dmoj_problems = {}
    if oj in accounts and 'repeat' in global_users[iden] and not global_users[iden]['repeat']:
        if oj == 'dmoj':
            user_response = get('https://dmoj.ca/api/user/info/%s' % global_users[iden]['dmoj'])
            if user_response is not None:
                if points is None:
                    for name, prob in list(dmoj_problems.items()):
                        if name not in user_response['solved_problems']:
                            temp_dmoj_problems[name] = prob
                else:
                    temp_dmoj_problems['dmoj'] = {}
                    for point in list(problems_by_points['dmoj']):
                        temp_dmoj_problems['dmoj'][point] = {}
                        for name, prob in list(problems_by_points['dmoj'][point].items()):
                            if name not in user_response['solved_problems']:
                                temp_dmoj_problems['dmoj'][point][name] = prob
                if temp_dmoj_problems == {}:
                    await ctx.send(ctx.message.author.mention + ' Sorry, I couldn\'t find any problems with those parameters. :cry:')
                    return
                
    if temp_dmoj_problems != {}:
        problem_list = temp_dmoj_problems
    elif points is None:
        problem_list = dmoj_problems
    else:
        problem_list = problems_by_points
                                
    if points is not None:
        if not points.isdigit():
            await ctx.send(ctx.message.author.mention + ' Invalid query. Make sure your points is a positive integer.')
            return
        points = int(points)

    if maximum is not None:
        if not maximum.isdigit():
            await ctx.send(ctx.message.author.mention + ' Invalid query. Make sure your points is a positive integer.')
            return
        maximum = int(maximum)
        possibilities = []
        if oj.lower() == 'codeforces':
            oj = 'cf'
        elif oj.lower() == 'atcoder':
            oj = 'at'
        elif oj.lower() == 'wcipeg':
            oj = 'peg'
        for point in list(problem_list[oj].keys()):
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
            name, prob = rand.choice(list(problem_list.items()))
        elif points in problem_list['dmoj'] and len(problem_list['dmoj'][points]) > 0:
            name, prob = rand.choice(list(problem_list['dmoj'][points].items()))
        else:
            await ctx.send(ctx.message.author.mention + ' Sorry, I couldn\'t find any problems with those parameters. :cry:')
            return
        global_users[iden]['last_dmoj_problem'] = name
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

    elif oj.lower() == 'wcipeg' or oj.lower() == 'peg':
        if not peg_problems:
            await ctx.send(ctx.message.author.mention + ' There seems to be a problem with WCIPEG. Please try again later :shrug:')
            return
        if points is None:
            prob = rand.choice(list(peg_problems.values()))
        elif points in problems_by_points['peg']:
            prob = rand.choice(list(problems_by_points['peg'][points]))
        else:
            await ctx.send(ctx.message.author.mention + ' Sorry, I couldn\'t find any problems with those parameters. :cry:')
            return
        embed = discord.Embed(title=prob['name'], description=prob['url'] +' (searched in %ss)' % str(round(bot.latency, 3)))
        embed.timestamp = datetime.utcnow()
        embed.add_field(name='Points', value=prob['points'], inline=False)
        embed.add_field(name='Partials', value=('Yes' if prob['partial'] else 'No'), inline=False)
        embed.add_field(name='Users', value=prob['users'], inline=False)
        embed.add_field(name='AC Rate', value=prob['ac_rate'], inline=False)
        embed.add_field(name='Date Added', value=prob['date'], inline=False)
        await ctx.send(ctx.message.author.mention, embed=embed)

    else:
        await ctx.send(ctx.message.author.mention + ' Invalid query. The online judge must be one of the following: DMOJ (dmoj), Codeforces (codeforces/cf), AtCoder (atcoder/at), WCIPEG (wcipeg/peg).')

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

def valid(url):
    try:
        if urllib.request.urlopen(url).getcode() == 200:
            return True
        else:
            return False
    except:
        return False
    
@bot.command()
async def whatis(ctx, *, name=None):
    start = time()
    if name is None:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%swhatis <thing>`.' % prefix)
        return
    if valid('http://wcipeg.com/wiki/%s' % name.replace(' ', '_')):
        try:
            url = 'http://wcipeg.com/wiki/%s' % name.replace(' ', '_')
            wiki_response = wget(url)
            scan = True
            title = wiki_response[wiki_response.index(head_begin) + len(head_begin): wiki_response.index(head_end)]
            summary = ''
            for index in range(wiki_response.index(wcipeg_begin) + len(wcipeg_begin), wiki_response.index(wcipeg_end)):
                if wiki_response[index] == '<':
                    scan = False
                if scan:
                    summary += wiki_response[index]
                if wiki_response[index] == '>':
                    scan = True
            embed = discord.Embed(title=title, description=url + ' (searched in %ss)' % str(round(bot.latency, 3)))
            embed.timestamp = datetime.utcnow()
            embed.add_field(name='Summary', value=summary, inline=False)
            await ctx.send(ctx.message.author.mention + ' Here\'s what I found!', embed=embed)
            return
        except:
            pass
    page, summary = getSummary(name.replace(' ', '_'))
    if summary is None:
        await ctx.send(ctx.message.author.mention + ' Sorry, I couldn\'t find anything on "%s"' % name)
        return
    embed = discord.Embed(title=page.title, description=page.url+' (searched in %ss)' % str(round(bot.latency, 3)))
    embed.timestamp = datetime.utcnow()
    embed.add_field(name='Summary', value=summary, inline=False)
    await ctx.send(ctx.message.author.mention + ' Here\'s what I found!', embed=embed)

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
    if rand.randint(0, 100) == 0:
        data = [{'url':'https://media.discordapp.net/attachments/511001840071213067/660303090444140545/539233495000809475.png'}]
    else:
        data = get('https://api.thecatapi.com/v1/images/search?x-api-key=' + cat_api)
    await ctx.send(ctx.message.author.mention + ' :smiley_cat: ' + data[0]['url'])

@bot.command()
@commands.guild_only()
async def tea(ctx, user=None):
    global global_users
    if user is None:
        if not checkExistingUser(ctx.message.author):
            await ctx.send(ctx.message.author.mention + ' You have 0 cups of :tea:.')
            return
        if global_users[str(ctx.message.author.id)].get('tea', 0) == 1:
            await ctx.send(ctx.message.author.mention + ' You have 1 cup of :tea:.')
        else:
            await ctx.send(ctx.message.author.mention + ' You have ' + str(global_users[str(ctx.message.author.id)].get('tea', 0)) + ' cups of :tea:.')
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
            global_users[str(iden)]['tea'] = global_users[str(iden)].get('tea', 0) + 1
            updateUsers()
            await ctx.send(ctx.message.author.mention + ' sent a cup of :tea: to ' + member.mention)
            return
    await ctx.send(ctx.message.author.mention + ' It seems like that user does not exist.')

@bot.command()
async def toggleRepeat(ctx):
    global global_users
    checkExistingUser(ctx.message.author)
    iden = str(ctx.message.author.id)
    for account in accounts:
        if account in global_users[iden]:
            global_users[iden]['repeat'] = not global_users[iden].get('repeat', True)
            updateUsers()
            await ctx.send(ctx.message.author.mention + ' Repeat setting for command `%srandom` set to %s.' % (prefix, ('ON' if global_users[iden]['repeat'] else 'OFF')))
            return
    await ctx.send(ctx.message.author.mention + ' You are not linked to any accounts')

@bot.command()
@commands.guild_only()
async def profile(ctx, user=None):
    global global_users
    if user is None:
        iden = str(ctx.message.author.id)
    elif user[3:-1].isdigit():
        iden = user[3:-1]
    else:
        await ctx.send(ctx.message.author.mention + ' Invalid query. Please use format `%sprofile <user>`.' % prefix)
        return
    
    for member in ctx.guild.members:
        if member.id == int(iden):
            checkExistingUser(member)
            embed = discord.Embed(title=member.display_name, description=member.mention)
            embed.timestamp = datetime.utcnow()
            embed.add_field(name='Discord ID', value=member.id, inline=False)
            embed.add_field(name='Joined on', value=member.joined_at.strftime('%B %d, %Y'), inline=False)
            if 'dmoj' in global_users[iden]:
                embed.add_field(name='DMOJ', value='https://dmoj.ca/user/%s' % global_users[iden]['dmoj'], inline=False)
            await ctx.send(ctx.message.author.mention, embed=embed)
            return
    await ctx.send(ctx.message.author.mention + ' It seems like that user does not exist.')

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
    global sessions, global_users
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
                global_users[iden]['dmoj'] = str(sessions[ctx.message.author.id])
                updateUsers()
                await ctx.send('Successfully logged in with submission permissions as %s! (Note that for security reasons, you will be automatically logged out after the cache resets. You may delete the message containing your token now)' % sessions[ctx.message.author.id])
            except InvalidSessionException:
                await ctx.send('Token invalid, failed to log in (your DMOJ API token can be found by going to https://dmoj.ca/edit/profile/ and selecting the __Regenerate__ option next to API Token). Note: The login command will ONLY WORK IN DIRECT MESSAGE. Please do not share this token with anyone else.')
        elif site.lower() in ('cf', 'codeforces', 'atcoder'):
            await ctx.send('Sorry, logins to that site is not available yet')

language = Language()

@bot.command()
async def submit(ctx, problem=None, lang=None, *, source=None):
    global sessions, global_users
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
        if problem == '^' and 'last_dmoj_problem' in global_users[iden]:
            problem = global_users[iden]['last_dmoj_problem']
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
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def notify(ctx, channel=None):
    global contest_channels
    if channel is None:
        clist = 'Contest notification channels in this server:\n'
        for text_channel in ctx.message.guild.text_channels:
            if text_channel.id in contest_channels:
                clist += text_channel.mention + '\n'
        await ctx.send(clist)
        return
    if not channel[2:-1].isdigit():
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
@commands.guild_only()
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
        
@tasks.loop(minutes=30)
async def status_change():
    await bot.change_presence(activity=discord.Game(name='with %s' % rand.choice(statuses)))

@status_change.before_loop
async def status_change_before():
    await bot.wait_until_ready()

@tasks.loop(minutes=20)
async def update_ranks():
    global global_users
    for guild in bot.guilds:
        names = []
        try:
            for role in guild.roles:
                names.append(role.name)
            for role in list(ratings.values()):
                if role[0] not in names:
                    await guild.create_role(name=role[0], colour=role[1])
            for member in guild.members:
                iden = str(member.id)
                if iden in global_users and 'dmoj' in global_users[iden]:
                    user_info = get('https://dmoj.ca/api/user/info/%s' % global_users[iden]['dmoj'])
                    if user_info is not None:
                        current_rating = user_info['contests']['current_rating']
                        for rating, role in list(ratings.items()):
                            role = discord.utils.get(guild.roles, name=role[0])
                            if current_rating in rating and role not in member.roles:
                                await member.add_roles(role)
                            elif current_rating not in rating and role in member.roles:
                                await member.remove_roles(role)
        except:
            pass
        
@update_ranks.before_loop
async def update_ranks_before():
    await bot.wait_until_ready()

@tasks.loop(hours=3)
async def refresh_problems():
    global dmoj_problems, cf_problems, at_problems, peg_problems
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
    problems = requests.get('https://wcipeg.com/problems/show%3D999999')
    if problems.status_code == 200:
        soup = bs.BeautifulSoup(problems.text, 'lxml')
        table = soup.find('table', attrs={'class' : 'nicetable stripes'}).findAll('tr')
        for prob in range(1, len(table)):
            values = table[prob].findAll('td')
            name = values[0].find('a').contents[0]
            url = 'https://wcipeg.com/problem/' + values[1].contents[0]
            points_value = values[2].contents[0]
            partial = 'p' in points_value
            points = int(points_value.replace('p', ''))
            p_users = values[3].find('a').contents[0]
            ac_rate = values[4].contents[0]
            date = values[5].contents[0]
            peg_data = {
                'name': name,
                'url': url,
                'partial': partial,
                'points': points,
                'users': p_users,
                'ac_rate': ac_rate,
                'date': date
            }
            peg_problems[name] = peg_data
            if points not in problems_by_points['peg']:
                problems_by_points['peg'][points] = []
            problems_by_points['peg'][points].append(peg_data)

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
    await ctx.send(ctx.message.author.mention + ' Here is a full list of my commands! https://github.com/kevinjycui/Practice-Bot/blob/master/COMMANDS.md')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

status_change.start()
refresh_problems.start()
check_contests.start()
update_ranks.start()
if bot_token != dev_token:
    dblapi.setup(bot, dbl_token)
bot.run(bot_token)
