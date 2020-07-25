import discord
from discord.ext import commands, tasks
from datetime import datetime, date
import random as rand
import requests
import bs4 as bs
from dmoj.session import Session as DMOJSession
from dmoj.session import InvalidSessionException
from dmoj.language import Language
from dmoj.usersuggester import UserSuggester as DMOJUserSuggester
from codeforces.session import Session as CodeforcesSession
from codeforces.session import InvalidCodeforcesSessionException, NoSubmissionsException, SessionTimeoutException, PrivateSubmissionException
from codeforces.usersuggester import UserSuggester as CodeforcesUserSuggester
from backend import mySQLConnection as query
from utils.onlinejudges import OnlineJudges, NoSuchOJException
from utils.country import Country, InvalidCountryException
import json
import re


def json_get(api_url):
    response = requests.get(api_url)

    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    return None

class InvalidParametersException(Exception):
    def __init__(self, cses=False, szkopul=False):
        self.cses = cses
        self.szkopul = szkopul
    
    def __str__(self):
        if self.cses:
            return 'Sorry, I couldn\'t find any problems with those parameters. :cry: (Note that CSES problems do not have points)'
        elif self.szkopul:
            return 'Sorry, I couldn\'t find any problems with those parameters. :cry: (Note that Szkopuł problems do not have points)'
        return 'Sorry, I couldn\'t find any problems with those parameters. :cry:'

class OnlineJudgeHTTPException(Exception):
    def __init__(self, oj):
        self.oj = oj

    def __str__(self):
        return self.oj

class InvalidQueryException(Exception):
    def __init__(self):
        pass

class ProblemNotFoundException(Exception):
    def __init__(self):
        self.message = ''
    
    def __str__(self):
        return self.message

class CSESProblemNotFoundException(ProblemNotFoundException):
    def __init__(self):
        ProblemNotFoundException.__init__(self)
        self.message = 'Note that only problems from the CSES Problem Set are available for CSES'

class InvalidURLException(Exception):
    def __init__(self):
        pass

class ProblemCog(commands.Cog):
    problems_by_points = {'dmoj':{}, 'codeforces':{}, 'atcoder':{}, 'peg':{}}
    dmoj_problems = None
    cf_problems = None
    at_problems = None
    cses_problems = {}
    peg_problems = {}
    szkopul_problems = {}
    dmoj_sessions = {}
    cf_sessions = {}
    dmoj_user_suggests = {}
    cf_user_suggests = {}
    szkopul_page = 1
    language = Language()
    onlineJudges = OnlineJudges()

    def __init__(self, bot):
        self.bot = bot

        with open('data/daily.json', 'r', encoding='utf8', errors='ignore') as f:
            self.daily_problems = json.load(f)

        self.refresh_dmoj_problems.start()
        self.refresh_cf_problems.start()
        self.refresh_atcoder_problems.start()
        self.refresh_cses_problems.start()
        self.refresh_peg_problems.start()
        self.refresh_szkopul_problems.start()
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
                self.problems_by_points['codeforces'] = {}
                for details in self.cf_problems:
                    if 'points' in details.keys():
                        if details['points'] not in self.problems_by_points['codeforces']:
                            self.problems_by_points['codeforces'][details['points']] = []
                        self.problems_by_points['codeforces'][details['points']].append(details)
            except KeyError:
                pass

    def parse_atcoder_problems(self, problems):
        if problems is not None:
            self.atcoder_problems = problems
            self.problems_by_points['atcoder'] = {}
            for details in problems:
                if details['point']:
                    if details['point'] not in self.problems_by_points['atcoder']:
                        self.problems_by_points['atcoder'][details['point']] = []
                    self.problems_by_points['atcoder'][details['point']].append(details)

    def parse_cses_problems(self, problems):
        if problems.status_code == 200:
            soup = bs.BeautifulSoup(problems.text, 'lxml')
            task_lists = soup.findAll('ul', attrs={'class' : 'task-list'})
            task_groups = soup.findAll('h2')
            self.cses_problems = {}
            for index in range(1, len(task_groups)):
                tasks = task_lists[index].findAll('li', attrs={'class' : 'task'})
                for task in tasks:
                    name = task.find('a').contents[0]
                    url = 'https://cses.fi' + task.find('a').attrs['href']
                    id = url.split('/')[-1]
                    rate = task.find('span', attrs={'class' : 'detail'}).contents[0]
                    group = task_groups[index].contents[0]
                    cses_data = {
                        'id': id,
                        'name': name,
                        'url': url,
                        'rate': rate,
                        'group': group
                    }
                    self.cses_problems[id] = cses_data

    def parse_peg_problems(self, problems):
        if problems.status_code == 200:
            soup = bs.BeautifulSoup(problems.text, 'lxml')
            table = soup.find('table', attrs={'class' : 'nicetable stripes'}).findAll('tr')
            self.peg_problems = {}
            self.problems_by_points['peg'] = {}
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

    def parse_szkopul_problems(self):
        problems = requests.get('https://szkopul.edu.pl/problemset/?page=%d' % self.szkopul_page)
        if problems.status_code == 200:
            soup = bs.BeautifulSoup(problems.text, 'lxml')
            rows = soup.findAll('tr')
            if self.szkopul_page == 1:
                self.szkopul_problems = {}
            if len(rows) == 1:
                return
            for row in rows:
                data = row.findAll('td')
                if data == []:
                    continue
                id = data[0].contents[0]
                title = data[1].find('a').contents[0]
                url = 'https://szkopul.edu.pl' + data[1].find('a').attrs['href']
                tags = []
                for tag in data[2].findAll('a'):
                    tags.append(tag.contents[0])
                submitters = data[3].contents[0]
                problem_data = {
                    'id': id,
                    'title': title,
                    'url': url,
                    'tags': tags,
                    'submitters': submitters
                }
                if int(submitters) > 0:
                    problem_data['percent_correct'] = data[4].contents[0]
                    problem_data['average'] = data[5].contents[0]
                self.szkopul_problems[id] = problem_data
            self.szkopul_page += 1

    def embed_dmoj_problem(self, name, prob, suggested=False):
        embed = discord.Embed()
        url = 'https://dmoj.ca/problem/' + name
        embed.set_thumbnail(url='https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/dmoj-thumbnail.png')
        embed.add_field(name='Points', value=prob['points'], inline=False)
        embed.add_field(name='Partials', value=('Yes' if prob['partial'] else 'No'), inline=False)
        embed.add_field(name='Group', value=prob['group'], inline=False)
        return ('[:thumbsup: SUGGESTED] ' if suggested else '') + prob['name'], url, embed

    def embed_cf_problem(self, prob, suggested=False):
        embed = discord.Embed()
        url = 'https://codeforces.com/problemset/problem/' + str(prob['contestId']) + '/' + str(prob['index'])
        embed.set_thumbnail(url='https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/cf-thumbnail.png')
        embed.add_field(name='Type', value=prob['type'], inline=False)
        if 'points' in prob.keys():
            embed.add_field(name='Points', value=prob['points'], inline=False)
        if 'rating' in prob.keys():
            embed.add_field(name='Rating', value=prob['rating'], inline=False)
        embed.add_field(name='Tags', value='||'+', '.join(prob['tags'])+'||', inline=False)
        return ('[:thumbsup: SUGGESTED] ' if suggested else '') + prob['name'], url, embed

    def embed_atcoder_problem(self, prob):
        embed = discord.Embed()
        url = 'https://atcoder.jp/contests/' + prob['contest_id'] + '/tasks/' + prob['id']
        embed.set_thumbnail(url='https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/at-thumbnail.png')
        if prob['point']:
            embed.add_field(name='Points', value=prob['point'], inline=False)
        embed.add_field(name='Solver Count', value=prob['solver_count'], inline=False)
        return prob['title'], url, embed

    def embed_cses_problem(self, prob):
        embed = discord.Embed()
        embed.set_thumbnail(url='https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/cses-thumbnail.png')
        embed.add_field(name='Success Rate', value=prob['rate'], inline=False)
        embed.add_field(name='Group', value='||' + prob['group'] + '||', inline=False)
        return prob['name'], prob['url'], embed

    def embed_peg_problem(self, prob):
        embed = discord.Embed()
        embed.set_thumbnail(url='https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/peg-thumbnail.png')
        embed.add_field(name='Points', value=prob['points'], inline=False)
        embed.add_field(name='Partials', value=('Yes' if prob['partial'] else 'No'), inline=False)
        embed.add_field(name='Users', value=prob['users'], inline=False)
        embed.add_field(name='AC Rate', value=prob['ac_rate'], inline=False)
        embed.add_field(name='Date Added', value=prob['date'], inline=False)
        return prob['name'], prob['url'], embed

    def embed_szkopul_problem(self, prob):
        embed = discord.Embed()
        embed.set_thumbnail(url='https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/szkopul-thumbnail.png')
        if len(prob['tags']) > 0:
            embed.add_field(name='Tags', value=', '.join(prob['tags']), inline=False)
        embed.add_field(name='Submitters', value=prob['submitters'], inline=False)
        if 'percent_correct' in prob:
            embed.add_field(name='% Correct', value=prob['percent_correct'], inline=False)
        if 'average' in prob:
            embed.add_field(name='Average', value=prob['average'], inline=False)
        return prob['title'], prob['url'], embed

    def get_problem(self, oj, contest_id=None, problem_id=None, szkopul_url=''):

        oj = self.onlineJudges.get_oj(oj)
        if oj != 'szkopul' and problem_id is None:
            raise ProblemNotFoundException
        
        if oj == 'dmoj':
            if problem_id not in self.dmoj_problems.keys():
                raise ProblemNotFoundException
            title, description, embed = self.embed_dmoj_problem(problem_id, self.dmoj_problems[problem_id])
            embed.title = title
            embed.description = description + ' (searched in %ss)' % str(round(self.bot.latency, 3))
            embed.timestamp = datetime.utcnow()
            return embed
        
        elif oj == 'codeforces':
            if contest_id is None:
                raise ProblemNotFoundException
            def is_problem(prob):
                return prob['contestId'] == int(contest_id) and prob['index'] == problem_id
            problist = list(filter(is_problem, self.cf_problems))
            if len(problist) == 0:
                raise ProblemNotFoundException
            title, description, embed = self.embed_cf_problem(problist[0])
            embed.title = title
            embed.description = description + ' (searched in %ss)' % str(round(self.bot.latency, 3))
            embed.timestamp = datetime.utcnow()
            return embed

        elif oj == 'atcoder':
            if contest_id is None:
                raise ProblemNotFoundException
            def is_problem(prob):
                return prob['contest_id'] == contest_id and prob['id'] == problem_id
            problist = list(filter(is_problem, self.atcoder_problems))
            if len(problist) == 0:
                raise ProblemNotFoundException
            title, description, embed = self.embed_atcoder_problem(problist[0])
            embed.title = title
            embed.description = description + ' (searched in %ss)' % str(round(self.bot.latency, 3))
            embed.timestamp = datetime.utcnow()
            return embed

        elif oj == 'peg':
            def is_problem(prob):
                return prob['url'] == 'https://wcipeg.com/problem/' + problem_id
            problist = list(filter(is_problem, list(self.peg_problems.values())))
            if len(problist) == 0:
                raise ProblemNotFoundException
            title, description, embed = self.embed_peg_problem(problist[0])
            embed.title = title
            embed.description = description + ' (searched in %ss)' % str(round(self.bot.latency, 3))
            embed.timestamp = datetime.utcnow()
            return embed

        elif oj == 'cses':
            if problem_id not in self.cses_problems.keys():
                raise CSESProblemNotFoundException
            title, description, embed = self.embed_cses_problem(self.cses_problems[problem_id])
            embed.title = title
            embed.description = description + ' (searched in %ss)' % str(round(self.bot.latency, 3))
            embed.timestamp = datetime.utcnow()
            return embed

        elif oj == 'szkopul':
            if szkopul_url == '':
                raise ProblemNotFoundException
            def is_problem(prob):
                return prob['url'] == szkopul_url
            problist = list(filter(is_problem, list(self.szkopul_problems.values())))
            if len(problist) == 0:
                raise ProblemNotFoundException
            title, description, embed = self.embed_szkopul_problem(problist[0])
            embed.title = title
            embed.description = description + ' (searched in %ss)' % str(round(self.bot.latency, 3))
            embed.timestamp = datetime.utcnow()
            return embed

    def get_problem_from_url(self, url):
        components = url.split('/')
        if url[:24] == 'https://dmoj.ca/problem/' and len(components) == 5:
            return self.get_problem('dmoj', problem_id=components[4])
        elif url[:42] == 'https://codeforces.com/problemset/problem/' and len(components) == 7:
            return self.get_problem('codeforces', components[5], components[6])
        elif url[:28] == 'https://atcoder.jp/contests/' and len(components) == 7 and components[5] == 'tasks':
            return self.get_problem('atcoder', components[4], components[6])
        elif url[:27] == 'https://wcipeg.com/problem/' and len(components) == 5:
            return self.get_problem('peg', problem_id=components[4])
        elif url[:32] == 'https://cses.fi/problemset/task/' and len(components) == 6:
            return self.get_problem('cses', problem_id=components[5])
        elif url[:42] == 'https://szkopul.edu.pl/problemset/problem/':
            return self.get_problem('szkopul', szkopul_url=url)
        else:
            raise InvalidURLException

    def get_random_problem(self, oj=None, points=None, maximum=None, iden=None):
        if oj is None:
            oj = rand.choice(self.onlineJudges.judges)

        oj = self.onlineJudges.get_oj(oj)
        
        if oj == 'cses' and points is not None:
            raise InvalidParametersException(cses=True)

        temp_dmoj_problems = {}
        temp_cf_problems = []
        user_data = query.get_user(iden)
        suggestions_on = False

        if iden is not None:
            suggestions_on = user_data[iden]['can_suggest'] and points is None and ((
                    oj == 'dmoj' and user_data[iden]['dmoj'] is not None
                ) or (
                    oj == 'codeforces' and user_data[iden]['codeforces'] is not None
                ))
            if suggestions_on:
                if oj == 'dmoj':
                    if iden not in self.dmoj_user_suggests.keys():
                        self.dmoj_user_suggests[iden] = DMOJUserSuggester(user_data[iden]['dmoj'])
                    points, maximum = self.dmoj_user_suggests[iden].get_pp_range()
                elif oj == 'codeforces':
                    if iden not in self.cf_user_suggests.keys():
                        self.cf_user_suggests[iden] = CodeforcesUserSuggester(user_data[iden]['codeforces'])
                    points, maximum = self.cf_user_suggests[iden].get_pp_range()
                
            if not user_data[iden]['can_repeat']:
                if oj == 'dmoj' and user_data[iden]['dmoj'] is not None:
                    user_response = json_get('https://dmoj.ca/api/user/info/%s' % user_data[iden]['dmoj'])
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
                            raise InvalidParametersException()
                elif oj == 'codeforces' and user_data[iden]['codeforces'] is not None:
                    response = requests.get('https://codeforces.com/api/user.status?handle=' + user_data[iden]['codeforces'])
                    if response.status_code != 200 or response.json()['status'] != 'OK':
                        return None
                    solved = []
                    for sub in response.json()['result']:
                        if sub['verdict'] == 'OK':
                            if 'contestId' in sub['problem']:
                                solved.append((sub['problem']['contestId'], sub['problem']['index']))
                            elif 'problemsetName' in sub['problem']:
                                solved.append((sub['problem']['problemsetName'], sub['problem']['index']))
                    if points is None:
                        temp_cf_problems = list(filter(lambda prob: (prob.get('contestId', prob.get('problemsetName')), prob['index']) not in solved, self.cf_problems))
                    else:
                        temp_cf_problems = {'codeforces': {}}
                        for point in list(self.problems_by_points['codeforces']):
                            temp_cf_problems['codeforces'][point] = list(filter(lambda prob: (prob['contestId'], prob['index']) not in solved, self.problems_by_points['codeforces'][point]))
                    if temp_cf_problems == [] or (type(temp_cf_problems) is dict and temp_cf_problems['codeforces'] == {}):
                        raise InvalidParametersException()

        if temp_dmoj_problems != {}:
            problem_list = temp_dmoj_problems
        elif temp_cf_problems != []:
            problem_list = temp_cf_problems
        elif points is None:
            if oj == 'dmoj':
                problem_list = self.dmoj_problems
            elif oj == 'codeforces':
                problem_list = self.cf_problems
        else:
            problem_list = self.problems_by_points
                                    
        if points is not None:
            if not points.isdigit():
                raise InvalidQueryException()
            points = int(points)

        if maximum is not None:
            if not maximum.isdigit():
                raise InvalidQueryException()
            maximum = int(maximum)
            possibilities = []
            for point in list(problem_list[oj].keys()):
                if point >= points and point <= maximum:
                    possibilities.append(point)
            if len(possibilities) == 0:
                if suggestions_on and oj == 'dmoj':
                    while len(possibilities) == 0:
                        self.dmoj_user_suggests[iden].expand_pp_range()
                        points, maximum = map(int, self.dmoj_user_suggests[iden].get_pp_range())
                        for point in list(problem_list[oj].keys()):
                            if point >= points and point <= maximum:
                                possibilities.append(point)
                        if points <= 1 and maximum >= 50 and len(possibilities) == 0:
                            raise InvalidParametersException()
                elif suggestions_on and oj == 'codeforces':
                    while len(possibilities) == 0:
                        self.cf_user_suggests[iden].expand_pp_range()
                        points, maximum = map(int, self.cf_user_suggests[iden].get_pp_range())
                        for point in list(problem_list[oj].keys()):
                            if point >= points and point <= maximum:
                                possibilities.append(point)
                        if points <= 1 and maximum >= 50 and len(possibilities) == 0:
                            raise InvalidParametersException()
                else:
                    raise InvalidParametersException()
            points = rand.choice(possibilities)
            
        if oj == 'dmoj':
            if not self.dmoj_problems:
                raise OnlineJudgeHTTPException('DMOJ')
                
            if points is None:
                name, prob = rand.choice(list(problem_list.items()))
            elif points in problem_list['dmoj'] and len(problem_list['dmoj'][points]) > 0:
                name, prob = rand.choice(list(problem_list['dmoj'][points].items()))
            else:
                raise InvalidParametersException()
            if iden is not None:
                user_data[iden]['last_dmoj_problem'] = name
                query.update_user(iden, 'last_dmoj_problem', name)
            return self.embed_dmoj_problem(name, prob, suggestions_on)
            
        elif oj == 'codeforces':
            if not self.cf_problems:
                raise OnlineJudgeHTTPException('Codeforces')
                return
            if points is None:
                prob = rand.choice(problem_list)
            elif points in problem_list['codeforces']:
                prob = rand.choice(problem_list['codeforces'][points])
            else:
                raise InvalidParametersException()
            return self.embed_cf_problem(prob, suggestions_on)

        elif oj == 'atcoder':
            if not self.atcoder_problems:
                raise OnlineJudgeHTTPException('AtCoder')

            if points is None:
                prob = rand.choice(self.atcoder_problems)
            elif points in self.problems_by_points['atcoder']:
                prob = rand.choice(self.problems_by_points['atcoder'][points])
            else:
                raise InvalidParametersException()
            return self.embed_atcoder_problem(prob)

        elif oj == 'peg':
            if not self.peg_problems:
                raise OnlineJudgeHTTPException('WCIPEG')
            if points is None:
                prob = rand.choice(list(self.peg_problems.values()))
            elif points in self.problems_by_points['peg']:
                prob = rand.choice(list(self.problems_by_points['peg'][points]))
            else:
                raise InvalidParametersException()
            return self.embed_peg_problem(prob)

        elif oj == 'cses':
            prob = rand.choice(list(self.cses_problems.values()))
            return self.embed_cses_problem(prob)

        elif oj == 'szkopul':
            prob = rand.choice(list(self.szkopul_problems.values()))
            return self.embed_szkopul_problem(prob)
        
        else:
            raise NoSuchOJException(oj)

    def update_daily(self):
        with open('data/daily.json', 'w') as json_file:
            json.dump(self.daily_problems, json_file)

    def check_existing_user(self, user):
        query.insert_ignore_user(user.id)

    def check_existing_server(self, server):
        query.insert_ignore_server(server.id)

    @commands.command(aliases=['p'])
    async def problem(self, ctx, url: str):
        prefix = await self.bot.command_prefix(self.bot, ctx.message)
        await ctx.send(ctx.message.author.display_name + ', This command is no longer supported. To request for it again, feel free to leave a suggestion using the  `%ssuggest <suggestion>` command.' % prefix)

    # @commands.command(aliases=['p'])
    # async def problem(self, ctx, url: str):
    #     try:
    #         embed = self.get_problem_from_url(url)
    #         await ctx.send('Requested problem for ' + ctx.message.author.display_name, embed=embed)
    #     except InvalidURLException:
    #         await ctx.send(ctx.message.author.display_name + ', Sorry, the problem URL was not recognised.')
    #     except ProblemNotFoundException as e:
    #         await ctx.send(ctx.message.author.display_name + ', Sorry, the problem was not found. ' + str(e))

    @commands.command(aliases=['r'])
    async def random(self, ctx, oj=None, points=None, maximum=None):
        self.check_existing_user(ctx.message.author)
        if isinstance(oj, str) and (oj.lower() == 'peg' or oj.lower() == 'wcipeg'):
            await ctx.send(ctx.message.author.display_name + ', Notice: Starting from July 31, 2020 support for WCIPEG may be discontinued as **PEG Judge will shut down at the end of July**\nhttps://wcipeg.com/announcement/9383')
        try:
            title, description, embed = self.get_random_problem(oj, points, maximum, ctx.message.author.id)
            embed.title = title
            embed.description = description + ' (searched in %ss)' % str(round(self.bot.latency, 3))
            embed.timestamp = datetime.utcnow()
            if rand.randint(0, 10) == 0 and (oj.lower() == 'dmoj' or oj.lower() == 'codeforces' or oj.lower() == 'cf'):
                prefix = await self.bot.command_prefix(self.bot, ctx.message)
                await ctx.send('Pro tip: Try out the new command, `%stogglesuggest` to turn on personalised suggested problems for DMOJ and Codeforces!' % prefix)
            await ctx.send('Requested problem for ' + ctx.message.author.display_name, embed=embed)
        except IndexError:
            await ctx.send(ctx.message.author.display_name + ', No problem was found. This may be due to the bot updating the problem cache. Please wait a moment, then try again.')
        except NoSuchOJException:
            await ctx.send(ctx.message.author.display_name + ', Invalid query. The online judge must be one of the following: %s.' % str(self.onlineJudges))
        except InvalidParametersException as e:
            await ctx.send(ctx.message.author.display_name + ', ' + str(e))
        except OnlineJudgeHTTPException as e:
            await ctx.send(ctx.message.author.display_name + ', There seems to be a problem with %s. Please try again later :shrug:' % str(e))
        except InvalidQueryException:
            await ctx.send(ctx.message.author.display_name + ', Invalid query. Make sure your points are positive integers.')

    @commands.command(aliases=['d'])
    async def daily(self, ctx):
        prefix = await self.bot.command_prefix(self.bot, ctx.message)
        await ctx.send(ctx.message.author.display_name + ', This command is no longer supported. To request for it again, feel free to leave a suggestion using the  `%ssuggest <suggestion>` command.' % prefix)
    
    # @commands.command(aliases=['d'])
    # async def daily(self, ctx):
    #     if str(date.today()) not in self.daily_problems.keys():
    #         try:
    #             title, description, embed = self.get_random_problem()
    #         except IndexError:
    #             await ctx.send(ctx.message.author.display_name + ', No problem was found. This may be due to the bot updating the problem cache. Please wait a moment, then try again.')
    #         thumbnail = 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/logo.png'
    #         for url, tn in list(self.onlineJudges.url_to_thumbnail.items()):
    #             if url in description:
    #                 thumbnail = tn
    #                 break
    #         self.daily_problems[str(date.today())] = {
    #             'title': title,
    #             'description': description,
    #             'thumbnail': thumbnail
    #         }
    #         self.update_daily()
    #     problem_data = self.daily_problems[str(date.today())]
    #     embed = self.get_problem_from_url(problem_data['description'])
    #     await ctx.send(ctx.message.author.display_name + ', Hello! Here\'s today\'s problem of the day!', embed=embed)

    @commands.command(aliases=['toggleRepeat'])
    async def togglerepeat(self, ctx):
        self.check_existing_user(ctx.message.author)
        user_data = query.get_user(ctx.message.author.id)
        for account in self.onlineJudges.accounts:
            if user_data[ctx.message.author.id][account] is not None:
                user_data[ctx.message.author.id]['can_repeat'] = not user_data[ctx.message.author.id]['can_repeat']
                query.update_user(ctx.message.author.id, 'can_repeat', user_data[ctx.message.author.id]['can_repeat'])
                prefix = await self.bot.command_prefix(self.bot, ctx.message)
                if user_data[ctx.message.author.id]['can_repeat']:
                    await ctx.send(ctx.message.author.display_name + ', random problems will now contain already solved problems')
                else:
                    await ctx.send(ctx.message.author.display_name + ', random problems will no longer contain already solved problems')
                return
        await ctx.send(ctx.message.author.display_name + ', You are not linked to any accounts')

    @commands.command(aliases=['toggleSuggest'])
    async def togglesuggest(self, ctx):
        self.check_existing_user(ctx.message.author)
        user_data = query.get_user(ctx.message.author.id)
        for account in self.onlineJudges.accounts:
            if user_data[ctx.message.author.id][account] is not None:
                user_data[ctx.message.author.id]['can_suggest'] = not user_data[ctx.message.author.id]['can_suggest']
                query.update_user(ctx.message.author.id, 'can_suggest', user_data[ctx.message.author.id]['can_suggest'])
                prefix = await self.bot.command_prefix(self.bot, ctx.message)
                if user_data[ctx.message.author.id]['can_suggest']:
                    await ctx.send(ctx.message.author.display_name + ', random problems will now be suggested based on your existing solves')
                else:
                    await ctx.send(ctx.message.author.display_name + ', random problems will no longer be suggested based on your existing solves')
                return
        await ctx.send(ctx.message.author.display_name + ', You are not linked to any accounts')
        
    @commands.command(aliases=['toggleCountry'])
    async def togglecountry(self, ctx, code=''):
        try:
            country_object = Country(code)
            user_data = query.get_user(ctx.message.author.id)
            prev_country = user_data[ctx.message.author.id]['country']
            user_data[ctx.message.author.id]['country'] = country_object.country
            query.update_user(ctx.message.author.id, 'country', user_data[ctx.message.author.id]['country'])
            if prev_country is not None and prev_country != country_object.country:
                await ctx.send(ctx.message.author.display_name + ', Changed your country from %s to %s.' % (str(Country(prev_country)), str(country_object)))
            else:
                await ctx.send(ctx.message.author.display_name + ', Set your country to %s.' % str(country_object))
        except InvalidCountryException:
            prefix = await self.bot.command_prefix(self.bot, ctx.message)
            await ctx.send(ctx.message.author.display_name + ', Sorry, could not find that country. Search for a country using the name (e.g. `%stogglecountry Finland`, `%stogglecountry "United States"`) or the 2 character ISO code (e.g. `%stogglecountry FI`))' % (prefix, prefix, prefix))

    @commands.command(aliases=['u', 'profile', 'whois'])
    async def user(self, ctx, user: discord.User=None):
        if user is None:
            user = ctx.message.author
        self.check_existing_user(user)
        user_data = query.get_user(user.id)
        embed = discord.Embed(title=user.display_name)
        embed.timestamp = datetime.utcnow()
        empty = True
        if user_data[user.id]['dmoj'] is not None:
            embed.add_field(name='DMOJ', value='https://dmoj.ca/user/%s' % user_data[user.id]['dmoj'], inline=False)
            empty = False
        if user_data[user.id]['codeforces'] is not None:
            embed.add_field(name='Codeforces', value='https://codeforces.com/profile/%s' % user_data[user.id]['codeforces'], inline=False)
            empty = False
        if user_data[user.id]['country'] is not None:
            embed.add_field(name='Country', value=str(Country(user_data[user.id]['country'])), inline=False)
            empty = False
        if empty:
            embed.description = 'No accounts linked...'
        await ctx.send('Requested profile by ' + ctx.message.author.display_name, embed=embed)

    @commands.command(aliases=['s'])
    async def submit(self, ctx, problem, lang, *, source=None):
        if ctx.message.author.id not in self.dmoj_sessions.keys():
            prefix = await self.bot.command_prefix(self.bot, ctx.message)
            await ctx.send(ctx.message.author.display_name + ', You are not logged in to a DMOJ account with submission permissions (this could happen if you last logged in a long time ago or have recently gone offline). Please use command `%sconnect dmoj <token>` (your DMOJ API token can be found by going to https://dmoj.ca/edit/profile/ and selecting the __Generate__ or __Regenerate__ option next to API Token). Note: The connect command will ONLY WORK IN DIRECT MESSAGE. Please do not share this token with anyone else.' % prefix)
            return
        user_session = self.dmoj_sessions[ctx.message.author.id]
        if not self.language.languageExists(lang):
            await ctx.send(ctx.message.author.display_name + ', That language is not available. The available languages are as followed: ```%s```' % ', '.join(self.language.getLanguages()))
            return
        try:
            if source is None and len(ctx.message.attachments) > 0:
                f = requests.get(ctx.message.attachments[0].url)
                source = f.content
            self.check_existing_user(ctx.message.author)
            user_data = query.get_user(ctx.message.author.id)
            if problem == '^' and user_data[ctx.message.author.id]['last_dmoj_problem'] is not None:
                problem = user_data[ctx.message.author.id]['last_dmoj_problem']
            id = user_session.submit(problem, self.language.getId(lang), source)
            response = user_session.getTestcaseStatus(id)
            responseText = str(response)
            if len(responseText) > 1950:
                responseText = responseText[1950:] + '\n(Result cut off to fit message length limit)'
            await ctx.send(ctx.message.author.display_name + ', ' + responseText + '\nTrack your submission here: https://dmoj.ca/submission/' + str(id))
        except InvalidSessionException:
            await ctx.send(ctx.message.author.display_name + ', Failed to connect, or problem not available. Make sure you are submitting to a valid problem, check your authentication, and try again.')
        except:
            await ctx.send(ctx.message.author.display_name + ', Error submitting to the problem. Report this using command `$suggest Submission to DMOJ failed`.')

    @tasks.loop(seconds=30)
    async def logout_offline(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id in self.dmoj_sessions.keys() and member.status == discord.Status.offline:
                    await member.send('Attention! You have been logged out of the account %s due to being offline (Note that your account will still be linked to your Discord account, but will now be unable to submit to problems)' % self.dmoj_sessions.pop(member.id))

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
    async def refresh_cses_problems(self):
        self.parse_cses_problems(requests.get('https://cses.fi/problemset/list/'))

    @refresh_cses_problems.before_loop
    async def refresh_cses_problems_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=3)
    async def refresh_peg_problems(self):
        self.parse_peg_problems(requests.get('https://wcipeg.com/problems/show%3D999999'))

    @refresh_peg_problems.before_loop
    async def refresh_peg_problems_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=3)
    async def refresh_szkopul_problems(self):
        self.parse_szkopul_problems()

    @refresh_szkopul_problems.before_loop
    async def refresh_szkopul_problems_before(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @commands.guild_only()
    async def tea(self, ctx, user: discord.User=None):
        if user is None:
            self.check_existing_user(ctx.message.author)
            user_data = query.get_user(ctx.message.author.id)
            if user_data[ctx.message.author.id]['tea'] == 1:
                await ctx.send(ctx.message.author.display_name + ', You have 1 cup of :tea:.')
            else:
                await ctx.send(ctx.message.author.display_name + ', You have ' + str(user_data[ctx.message.author.id]['tea']) + ' cups of :tea:.')
            return
        if user.id == ctx.message.author.id:
            await ctx.send(ctx.message.author.display_name + ', Sorry, cannot send :tea: to yourself!')
            return
        elif user.id == self.bot.user.id:
            await ctx.send(ctx.message.author.display_name + ', Thanks for the :tea:!')
            return
        self.check_existing_user(user)
        user_data = query.get_user(user.id)
        query.update_user(user.id, 'tea', user_data[user.id]['tea']+1)
        await ctx.send(ctx.message.author.display_name + ', sent a cup of :tea: to ' + user.mention)
        
def setup(bot):
    bot.add_cog(ProblemCog(bot))
