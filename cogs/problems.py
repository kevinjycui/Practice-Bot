import discord
from discord.ext import commands, tasks
from datetime import datetime, date
import random as rand
import requests
import bs4 as bs
from dmoj.session import Session, InvalidSessionException
from dmoj.language import Language
from backend import mySQLConnection as query
import json


def json_get(api_url):
    response = requests.get(api_url)

    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    return None

class NoSuchOJException(Exception):
    def __init__(self, oj):
        self.oj = oj

class InvalidParametersException(Exception):
    def __init__(self):
        pass

class OnlineJudgeHTTPException(Exception):
    def __init__(self, oj):
        self.oj = oj

    def __str__(self):
        return self.oj

class InvalidQueryException(Exception):
    def __init__(self):
        pass

class ProblemCog(commands.Cog):
    problems_by_points = {'dmoj':{}, 'cf':{}, 'at':{}, 'peg':{}}
    dmoj_problems = None
    cf_problems = None
    at_problems = None
    peg_problems = {}
    accounts = ('dmoj',)
    sessions = {}
    language = Language()
    url_to_thumbnail = {
        'https://dmoj.ca/problem/': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/dmoj-thumbnail.png',
        'https://codeforces.com/problemset/problem/': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/cf-thumbnail.png',
        'https://atcoder.jp/contests/': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/at-thumbnail.png',
        'https://wcipeg.com/problem/': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/peg-thumbnail.png'
    }

    def __init__(self, bot):
        self.bot = bot

        with open('data/daily.json', 'r', encoding='utf8', errors='ignore') as f:
            self.daily_problems = json.load(f)

        self.global_users = query.read_users()

        self.refresh_dmoj_problems.start()
        self.refresh_cf_problems.start()
        self.refresh_atcoder_problems.start()
        self.refresh_peg_problems.start()
        self.logout_offline.start()

    def parse_dmoj_problems(self, problems):
        if problems is not None:
            self.dmoj_problems = problems
            self.problems_by_points['dmoj'] = {}
            for name, details in problems.items():
                if details['points'] not in self.problems_by_points['dmoj']:
                    self.problems_by_points['dmoj'][details['points']] = {}
                self.problems_by_points['dmoj'][details['points']][name] = details

    def parse_cf_problems(self, cf_data):
        if cf_data is not None:
            try:
                self.cf_problems = cf_data['result']['problems']
                for details in self.cf_problems:
                    if 'points' in details.keys():
                        if details['points'] not in self.problems_by_points['cf']:
                            self.problems_by_points['cf'][details['points']] = []
                        self.problems_by_points['cf'][details['points']].append(details)
            except KeyError:
                pass

    def parse_atcoder_problems(self, problems):
        if problems is not None:
            self.at_problems = problems
            for details in problems:
                if details['point']:
                    if details['point'] not in self.problems_by_points['at']:
                        self.problems_by_points['at'][details['point']] = []
                    self.problems_by_points['at'][details['point']].append(details)

    def parse_peg_problems(self, problems):
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
                self.peg_problems[name] = peg_data
                if points not in self.problems_by_points['peg']:
                    self.problems_by_points['peg'][points] = []
                self.problems_by_points['peg'][points].append(peg_data)

    def embed_dmoj_problem(self, name, prob):
        embed = discord.Embed()
        url = 'https://dmoj.ca/problem/' + name
        embed.set_thumbnail(url='https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/dmoj-thumbnail.png')
        embed.add_field(name='Points', value=prob['points'], inline=False)
        embed.add_field(name='Partials', value=('Yes' if prob['partial'] else 'No'), inline=False)
        embed.add_field(name='Group', value=prob['group'], inline=False)
        return prob['name'], url, embed

    def embed_cf_problem(self, prob):
        embed = discord.Embed()
        url = 'https://codeforces.com/problemset/problem/' + str(prob['contestId']) + '/' + str(prob['index'])
        embed.set_thumbnail(url='https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/cf-thumbnail.png')
        embed.add_field(name='Type', value=prob['type'], inline=False)
        if 'points' in prob.keys():
            embed.add_field(name='Points', value=prob['points'], inline=False)
        embed.add_field(name='Rating', value=prob['rating'], inline=False)
        embed.add_field(name='Tags', value='||'+', '.join(prob['tags'])+'||', inline=False)
        return prob['name'], url, embed

    def embed_atcoder_problem(self, prob):
        embed = discord.Embed()
        url = 'https://atcoder.jp/contests/' + prob['contest_id'] + '/tasks/' + prob['id']
        embed.set_thumbnail(url='https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/at-thumbnail.png')
        if prob['point']:
            embed.add_field(name='Points', value=prob['point'], inline=False)
        embed.add_field(name='Solver Count', value=prob['solver_count'], inline=False)
        return prob['title'], url, embed

    def embed_peg_problem(self, prob):
        embed = discord.Embed()
        embed.set_thumbnail(url='https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/peg-thumbnail.png')
        embed.add_field(name='Points', value=prob['points'], inline=False)
        embed.add_field(name='Partials', value=('Yes' if prob['partial'] else 'No'), inline=False)
        embed.add_field(name='Users', value=prob['users'], inline=False)
        embed.add_field(name='AC Rate', value=prob['ac_rate'], inline=False)
        embed.add_field(name='Date Added', value=prob['date'], inline=False)
        return prob['name'], prob['url'], embed

    def get_random_problem(self, oj=None, points=None, maximum=None, iden=None):
        if oj is None:
            oj = rand.choice(('dmoj', 'cf', 'at', 'peg'))

        temp_dmoj_problems = {}
        if iden is not None and oj in self.accounts and self.global_users[iden]['dmoj'] is not None and not self.global_users[iden]['can_repeat']:
            if oj == 'dmoj':
                user_response = json_get('https://dmoj.ca/api/user/info/%s' % self.global_users[iden]['dmoj'])
                if user_response is not None:
                    if points is None:
                        for name, prob in list(self.dmoj_problems.items()):
                            if name not in user_response['solved_problems']:
                                temp_dmoj_problems[name] = prob
                    else:
                        temp_dmoj_problems['dmoj'] = {}
                        for point in list(self.problems_by_points['dmoj']):
                            temp_dmoj_problems['dmoj'][point] = {}
                            for name, prob in list(self.problems_by_points['dmoj'][point].items()):
                                if name not in user_response['solved_problems']:
                                    temp_dmoj_problems['dmoj'][point][name] = prob
                    if temp_dmoj_problems == {}:
                        raise InvalidParametersException
                    
        if temp_dmoj_problems != {}:
            problem_list = temp_dmoj_problems
        elif points is None:
            problem_list = self.dmoj_problems
        else:
            problem_list = self.problems_by_points
                                    
        if points is not None:
            if not points.isdigit():
                raise InvalidQueryException
            points = int(points)

        if maximum is not None:
            if not maximum.isdigit():
                raise InvalidQueryException
            maximum = int(maximum)
            possibilities = []
            if oj.lower() == 'codeforces':
                oj = 'cf'
            elif oj.lower() == 'atcoder' or oj.lower() == 'ac':
                oj = 'at'
            elif oj.lower() == 'wcipeg':
                oj = 'peg'
            for point in list(problem_list[oj].keys()):
                if point >= points and point <= maximum:
                    possibilities.append(point)
            if len(possibilities) == 0:
                raise InvalidParametersException
            points = rand.choice(possibilities)
            
        if oj.lower() == 'dmoj':
            if not self.dmoj_problems:
                raise OnlineJudgeHTTPException('DMOJ')
                
            if points is None:
                name, prob = rand.choice(list(problem_list.items()))
            elif points in problem_list['dmoj'] and len(problem_list['dmoj'][points]) > 0:
                name, prob = rand.choice(list(problem_list['dmoj'][points].items()))
            else:
                raise InvalidParametersException
            if iden is not None:
                self.global_users[iden]['last_dmoj_problem'] = name
                query.update_user(iden, 'last_dmoj_problem', name)
            return self.embed_dmoj_problem(name, prob)
            
        elif oj.lower() == 'cf' or oj.lower() == 'codeforces':
            if not self.cf_problems:
                raise OnlineJudgeHTTPException('Codeforces')
                return
            if points is None:
                prob = rand.choice(self.cf_problems)
            elif points in self.problems_by_points['cf']:
                prob = rand.choice(self.problems_by_points['cf'][points])
            else:
                raise InvalidParametersException
            return self.embed_cf_problem(prob)

        elif oj.lower() == 'atcoder' or oj.lower() == 'at' or oj.lower() == 'ac':
            if not self.at_problems:
                raise OnlineJudgeHTTPException('AtCoder')

            if points is None:
                prob = rand.choice(self.at_problems)
            elif points in self.problems_by_points['at']:
                prob = rand.choice(self.problems_by_points['at'][points])
            else:
                raise InvalidParametersException
            return self.embed_atcoder_problem(prob)

        elif oj.lower() == 'wcipeg' or oj.lower() == 'peg':
            if not self.peg_problems:
                raise OnlineJudgeHTTPException('WCIPEG')
            if points is None:
                prob = rand.choice(list(self.peg_problems.values()))
            elif points in self.problems_by_points['peg']:
                prob = rand.choice(list(self.problems_by_points['peg'][points]))
            else:
                raise InvalidParametersException
            return self.embed_peg_problem(prob)
        
        else:
            raise NoSuchOJException(oj)

    def update_daily(self):
        with open('data/daily.json', 'w') as json_file:
            json.dump(self.daily_problems, json_file)

    def check_existing_user(self, user):
        query.insert_ignore_user(user.id)
    
    @commands.command()
    async def random(self, ctx, oj=None, points=None, maximum=None):
        self.check_existing_user(ctx.message.author)
        if isinstance(oj, str) and (oj.lower() == 'peg' or oj.lower() == 'wcipeg'):
            await ctx.send(ctx.message.author.mention + ' Notice: Starting from July 31, 2020 support for WCIPEG may be discontinued as **PEG Judge will shut down at the end of July**\nhttps://wcipeg.com/announcement/9383')
        try:
            title, description, embed = self.get_random_problem(oj, points, maximum, ctx.message.author.id)
            embed.title = title
            embed.description = description + ' (searched in %ss)' % str(round(self.bot.latency, 3))
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

    @commands.command()
    async def daily(self, ctx):
        if str(date.today()) not in self.daily_problems.keys():
            title, description, embed = self.get_random_problem()
            thumbnail = 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/logo.png'
            for url, tn in list(self.url_to_thumbnail.items()):
                if url in description:
                    thumbnail = tn
                    break
            self.daily_problems[str(date.today())] = {
                'title': title,
                'description': description,
                'thumbnail': thumbnail
            }
            self.update_daily()
        problem_data = self.daily_problems[str(date.today())]
        embed = discord.Embed(title=problem_data['title'], description=problem_data['description'])
        embed.set_thumbnail(url=problem_data['thumbnail'])
        embed.timestamp = datetime.utcnow()
        await ctx.send(ctx.message.author.mention + ' Hello! Here\'s today\'s problem of the day!', embed=embed)

    @commands.command()
    async def toggleRepeat(self, ctx):
        self.check_existing_user(ctx.message.author)
        for account in self.accounts:
            if self.global_users[ctx.message.author.id][account] is not None:
                self.global_users[ctx.message.author.id]['can_repeat'] = not self.global_users[ctx.message.author.id]['can_repeat']
                query.update_user(ctx.message.author.id, 'can_repeat', self.global_users[ctx.message.author.id]['can_repeat'])
                await ctx.send(ctx.message.author.mention + ' Repeat setting for command `%srandom` set to %s.' % (self.bot.command_prefix, ('ON' if self.global_users[ctx.message.author.id]['can_repeat'] else 'OFF')))
                return
        await ctx.send(ctx.message.author.mention + ' You are not linked to any accounts')

    @commands.command()
    @commands.guild_only()
    async def profile(self, ctx, user: discord.User=None):
        if user is None:
            user = ctx.message.author
        self.check_existing_user(user)
        embed = discord.Embed(title=user.display_name, description=user.mention)
        embed.timestamp = datetime.utcnow()
        embed.add_field(name='Discord ID', value=user.id, inline=False)
        if self.global_users[user.id]['dmoj'] is not None:
            embed.add_field(name='DMOJ', value='https://dmoj.ca/user/%s' % self.global_users[user.id]['dmoj'], inline=False)
        await ctx.send(ctx.message.author.mention, embed=embed)

    @commands.command()
    async def submit(self, ctx, problem, lang, *, source=None):
        if ctx.message.author.id not in self.sessions.keys():
            await ctx.send(ctx.message.author.mention + ' You are not logged in to a DMOJ account with submission permissions (this could happen if you last logged in a long time ago or have recently gone offline). Please use command `%slogin dmoj <token>` (your DMOJ API token can be found by going to https://dmoj.ca/edit/profile/ and selecting the __Generate__ or __Regenerate__ option next to API Token). Note: The login command will ONLY WORK IN DIRECT MESSAGE. Please do not share this token with anyone else.' % self.bot.command_prefix)
            return
        user_session = self.sessions[ctx.message.author.id]
        if not self.language.languageExists(lang):
            await ctx.send(ctx.message.author.mention + ' That language is not available. The available languages are as followed: ```%s```' % ', '.join(self.language.getLanguages()))
            return
        try:
            if source is None and len(ctx.message.attachments) > 0:
                f = requests.get(ctx.message.attachments[0].url)
                source = f.content
            self.check_existing_user(ctx.message.author)
            if problem == '^' and self.global_users[ctx.message.author.id]['last_dmoj_problem'] is not None:
                problem = self.global_users[ctx.message.author.id]['last_dmoj_problem']
            id = user_session.submit(problem, self.language.getId(lang), source)
            response = user_session.getTestcaseStatus(id)
            responseText = str(response)
            if len(responseText) > 1950:
                responseText = responseText[1950:] + '\n(Result cut off to fit message length limit)'
            await ctx.send(ctx.message.author.mention + ' ' + responseText + '\nTrack your submission here: https://dmoj.ca/submission/' + str(id))
        except InvalidSessionException:
            await ctx.send(ctx.message.author.mention + ' Failed to connect, or problem not available. Make sure you are submitting to a valid problem, check your authentication, and try again.')
        except:
            await ctx.send(ctx.message.author.mention + ' Error submitting to the problem. Report this using command `$suggest Submission to DMOJ failed`.')

    @tasks.loop(seconds=30)
    async def logout_offline(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id in self.sessions.keys() and member.status == discord.Status.offline:
                    await member.send('Attention! You have been logged out of the account %s due to being offline (Note that your account will still be linked to your Discord account, but will now be unable to submit to problems)' % self.sessions.pop(member.id))

    @logout_offline.before_loop
    async def logout_offline_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=3)
    async def refresh_dmoj_problems(self):
        self.parse_dmoj_problems(json_get('https://dmoj.ca/api/problem/list'))
        
    @refresh_dmoj_problems.before_loop
    async def refresh_dmoj_problems_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=3)
    async def refresh_cf_problems(self):
        self.parse_cf_problems(json_get('https://codeforces.com/api/problemset.problems'))

    @refresh_cf_problems.before_loop
    async def refresh_cf_problems_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=3)
    async def refresh_atcoder_problems(self):
        self.parse_atcoder_problems(json_get('https://kenkoooo.com/atcoder/resources/merged-problems.json'))

    @refresh_atcoder_problems.before_loop
    async def refresh_atcoder_problems_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=3)
    async def refresh_peg_problems(self):
        self.parse_peg_problems(requests.get('https://wcipeg.com/problems/show%3D999999'))

    @refresh_peg_problems.before_loop
    async def refresh_peg_problems_before(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @commands.guild_only()
    async def tea(self, ctx, user: discord.User=None):
        if user is None:
            if not self.check_existing_user(ctx.message.author):
                await ctx.send(ctx.message.author.mention + ' You have 0 cups of :tea:.')
                return
            if self.global_users[ctx.message.author.id]['tea'] == 1:
                await ctx.send(ctx.message.author.mention + ' You have 1 cup of :tea:.')
            else:
                await ctx.send(ctx.message.author.mention + ' You have ' + str(self.global_users[ctx.message.author.id]['tea']) + ' cups of :tea:.')
            return
        if user.id == ctx.message.author.id:
            await ctx.send(ctx.message.author.mention + ' Sorry, cannot send :tea: to yourself!')
            return
        elif user.id == self.bot.user.id:
            await ctx.send(ctx.message.author.mention + ' Thanks for the :tea:!')
            return
        self.check_existing_user(user)
        self.global_users[user.id]['tea'] += 1
        query.update_user(user.id, 'tea', self.global_users[user.id]['tea'])
        await ctx.send(ctx.message.author.mention + ' sent a cup of :tea: to ' + user.mention)
        
def setup(bot):
    bot.add_cog(ProblemCog(bot))
