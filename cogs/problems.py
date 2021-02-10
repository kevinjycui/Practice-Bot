import discord
from discord.ext import commands, tasks
from datetime import datetime, date
import random as rand
import bs4 as bs
from dmoj.session import Session as DMOJSession
from dmoj.session import InvalidDMOJSessionException, VerificationException
from dmoj.language import Language
from dmoj.usersuggester import UserSuggester as DMOJUserSuggester
from codeforces.session import Session as CodeforcesSession
from codeforces.session import InvalidCodeforcesSessionException, NoSubmissionsException, SessionTimeoutException, PrivateSubmissionException
from codeforces.usersuggester import UserSuggester as CodeforcesUserSuggester
from connector import mySQLConnection as query
from utils.onlinejudges import OnlineJudges, NoSuchOJException
from utils.country import Country, InvalidCountryException
from utils.webclient import webc
import requests
import json
import re
from time import time


class InvalidParametersException(Exception):
    def __init__(self, cses=False, szkopul=False, leetcode=False):
        self.cses = cses
        self.szkopul = szkopul
        self.leetcode = leetcode

    def __str__(self):
        if self.cses:
            return 'Sorry, I couldn\'t find any problems with those parameters. :cry: (Note that CSES problems do not have points)'
        elif self.szkopul:
            return 'Sorry, I couldn\'t find any problems with those parameters. :cry: (Note that Szkopuł problems do not have points)'
        elif self.leetcode:
            return 'Sorry, I couldn\'t find any problems with those paramaters. :cry: (Note that LeetCode difficulty ratings are either 1, 2, or 3)'
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
    problems_by_points = {'dmoj':{}, 'codeforces':{}, 'atcoder':{}}

    dmoj_problems = {}
    cf_problems = None
    at_problems = None
    cses_problems = []
    szkopul_problems = {}
    leetcode_problems = []
    leetcode_problems_paid = []

    dmoj_sessions = {}
    cf_sessions = {}

    dmoj_user_suggests = {}
    cf_user_suggests = {}

    szkopul_page = 1
    language = Language()
    onlineJudges = OnlineJudges()

    statuses = {
        'dmoj': 0,
        'codeforces': 0,
        'atcoder': 0,
        'cses': 0,
        'szkopul': 0,
        'leetcode': 0
    }
    fetch_times = {
        'dmoj': 0,
        'codeforces': 0,
        'atcoder': 0,
        'cses': 0,
        'szkopul': 0,
        'leetcode': 0
    }

    def __init__(self, bot):
        self.bot = bot
        self.refresh_dmoj_problems.start()
        self.refresh_cf_problems.start()
        self.refresh_atcoder_problems.start()
        self.refresh_leetcode_problems.start()
        self.refresh_cses_problems.start()
        self.refresh_szkopul_problems.start()

    @commands.command()
    async def oj(self, ctx, oj: str=''):
        if oj == '':
            status_list = '```'
            for oj in self.onlineJudges.problem_judges:
                status_list += '%s status: %s. Last fetched, %d minutes ago\n' % (self.onlineJudges.formal_names[oj], 'OK' if self.statuses[oj] == 1 else 'Unable to connect', (time()-self.fetch_times[oj])//60)
            await ctx.send(status_list[:-1] + '```')
        else:
            try:
                oj = self.onlineJudges.get_oj(oj)
                if oj not in self.onlineJudges.problem_judges:
                    raise NoSuchOJException(oj)
                await ctx.send('```%s status: %s. Last fetched, %d minutes ago```' % (self.onlineJudges.formal_names[oj], 'OK' if self.statuses[oj] == 1 else 'Unable to connect', (time()-self.fetch_times[oj])//60))
            except NoSuchOJException:
                await ctx.send(ctx.message.author.display_name + ', Sorry, no online judge found. Search only for online judges used for getting problems this bot ' + self.onlineJudges.problem_judges_str())


    async def parse_dmoj_problems(self):
        try:
            problem_req = await webc.webget_json('https://dmoj.ca/api/v2/problems')
            problems = problem_req['data']['objects']
            self.statuses['dmoj'] =  1
            self.dmoj_problems = {}
            for problem in problems:
                self.dmoj_problems[problem['code']] = problem
            self.problems_by_points['dmoj'] = {}
            for name, details in self.dmoj_problems.items():
                if details['points'] not in self.problems_by_points['dmoj']:
                    self.problems_by_points['dmoj'][details['points']] = {}
                self.problems_by_points['dmoj'][details['points']][name] = details
        except Exception as e:
            self.statuses['dmoj'] = 0
            raise e

    def parse_cf_problems(self):
        try:
            problems = requests.get('https://codeforces.com/api/problemset.problems').json()
            self.statuses['codeforces'] =  1
            self.cf_problems = problems['result']['problems']
            self.problems_by_points['codeforces'] = {}
            for details in self.cf_problems:
                if 'rating' in details.keys():
                    if details['rating'] not in self.problems_by_points['codeforces']:
                        self.problems_by_points['codeforces'][details['rating']] = []
                    self.problems_by_points['codeforces'][details['rating']].append(details)
        except Exception as e:
            self.statuses['codeforces'] = 0
            raise e

    def parse_atcoder_problems(self):
        try:
            problems = requests.get('https://kenkoooo.com/atcoder/resources/merged-problems.json').json()
            self.statuses['atcoder'] =  1
            self.atcoder_problems = problems
            self.problems_by_points['atcoder'] = {}
            for details in problems:
                if details['point']:
                    if details['point'] not in self.problems_by_points['atcoder']:
                        self.problems_by_points['atcoder'][details['point']] = []
                    self.problems_by_points['atcoder'][details['point']].append(details)
        except Exception as e:
            self.statuses['atcoder'] = 0
            raise e

    def parse_cses_problems(self):
        try:
            problems = requests.get('https://cses.fi/problemset/list/').text
            self.statuses['cses'] =  1
            self.cses_problems = []
            soup = bs.BeautifulSoup(problems, 'lxml')
            task_lists = soup.find_all('ul', attrs={'class' : 'task-list'})
            task_groups = soup.find_all('h2')
            for index in range(1, len(task_groups)):
                tasks = task_lists[index].find_all('li', attrs={'class' : 'task'})
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
                    self.cses_problems.append(cses_data)
        except Exception as e:
            self.statuses['cses'] = 0
            raise e

    def parse_szkopul_problems(self):
        try:
            problems = requests.get('https://szkopul.edu.pl/problemset/?page=%d' % self.szkopul_page).text
            self.statuses['szkopul'] =  1
            soup = bs.BeautifulSoup(problems, 'lxml')
            rows = soup.find_all('tr')
            if len(rows) == 1:
                self.szkopul_problems = [p for p in self.szkopul_problems if p['updated']]
                return
            if self.szkopul_page == 1:
                for problem in self.szkopul_problems:
                    problem['updated'] = False
            for row in rows:
                data = row.find_all('td')
                if data == []:
                    continue
                id = data[0].contents[0]
                title = data[1].find('a').contents[0]
                url = 'https://szkopul.edu.pl' + data[1].find('a').attrs['href']
                tags = []
                for tag in data[2].find_all('a'):
                    tags.append(tag.contents[0])
                submitters = data[3].contents[0]
                problem_data = {
                    'id': id,
                    'title': title,
                    'url': url,
                    'tags': tags,
                    'submitters': submitters,
                    'updated': True
                }
                if int(submitters) > 0:
                    problem_data['percent_correct'] = data[4].contents[0]
                    problem_data['average'] = data[5].contents[0]
                self.szkopul_problems[id] = problem_data
            self.szkopul_page += 1
        except Exception as e:
            self.statuses['szkopul'] = 0
            raise e

    def parse_leetcode_problems(self):
        try:
            problems = requests.get('https://leetcode.com/api/problems/algorithms/').json()
            self.statuses['leetcode'] = 1
            self.leetcode_problems_paid = []
            self.leetcode_problems = []
            problemlist = problems['stat_status_pairs']
            for problem in problemlist:
                id = problem['stat']['frontend_question_id']
                title = problem['stat']['question__title']
                url = 'https://leetcode.com/problems/' + problem['stat']['question__title_slug']
                total_acs = problem['stat']['total_acs']
                total_submitted = problem['stat']['total_submitted']
                level = problem['difficulty']['level']
                paid = problem['paid_only']
                problem_data = {
                    'id': id,
                    'title': title,
                    'url': url,
                    'total_acs': total_acs,
                    'total_submitted': total_submitted,
                    'level': level,
                    'paid': paid
                }
                if paid:
                    self.leetcode_problems_paid.append(problem_data)
                else:
                    self.leetcode_problems.append(problem_data)
        except Exception as e:
            self.statuses['leetcode'] = 0
            raise e

    def embed_dmoj_problem(self, name, prob, suggested=False):
        embed = discord.Embed()
        embed.colour = self.onlineJudges.colours['dmoj']
        url = 'https://dmoj.ca/problem/' + name
        embed.set_thumbnail(url=self.onlineJudges.thumbnails['dmoj'])
        embed.add_field(name='Points', value=prob['points'], inline=False)
        embed.add_field(name='Partials', value=('Yes' if prob['partial'] else 'No'), inline=False)
        embed.add_field(name='Group', value=prob['group'], inline=False)
        embed.add_field(name='Types', value='||'+', '.join(prob['types'])+'||', inline=False)
        return ('[:thumbsup: SUGGESTED] ' if suggested else '') + prob['name'], url, embed

    def embed_cf_problem(self, prob, suggested=False):
        embed = discord.Embed()
        embed.colour = self.onlineJudges.colours['codeforces']
        url = 'https://codeforces.com/problemset/problem/' + str(prob['contestId']) + '/' + str(prob['index'])
        embed.set_thumbnail(url=self.onlineJudges.thumbnails['codeforces'])
        embed.add_field(name='Type', value=prob['type'], inline=False)
        if 'points' in prob.keys():
            embed.add_field(name='Points', value=prob['points'], inline=False)
        if 'rating' in prob.keys():
            embed.add_field(name='Rating', value=prob['rating'], inline=False)
        embed.add_field(name='Tags', value='||'+', '.join(prob['tags'])+'||', inline=False)
        return ('[:thumbsup: SUGGESTED] ' if suggested else '') + prob['name'], url, embed

    def embed_atcoder_problem(self, prob):
        embed = discord.Embed()
        embed.colour = self.onlineJudges.colours['atcoder']
        url = 'https://atcoder.jp/contests/' + prob['contest_id'] + '/tasks/' + prob['id']
        embed.set_thumbnail(url=self.onlineJudges.thumbnails['atcoder'])
        if prob['point']:
            embed.add_field(name='Points', value=prob['point'], inline=False)
        embed.add_field(name='Solver Count', value=prob['solver_count'], inline=False)
        return prob['title'], url, embed

    def embed_cses_problem(self, prob):
        embed = discord.Embed()
        embed.colour = self.onlineJudges.colours['cses']
        embed.set_thumbnail(url=self.onlineJudges.thumbnails['cses'])
        embed.add_field(name='Success Rate', value=prob['rate'], inline=False)
        embed.add_field(name='Group', value='||' + prob['group'] + '||', inline=False)
        return prob['name'], prob['url'], embed

    def embed_szkopul_problem(self, prob):
        embed = discord.Embed()
        embed.colour = self.onlineJudges.colours['szkopul']
        embed.set_thumbnail(url=self.onlineJudges.thumbnails['szkopul'])
        if len(prob['tags']) > 0:
            embed.add_field(name='Tags', value=', '.join(prob['tags']), inline=False)
        embed.add_field(name='Submitters', value=prob['submitters'], inline=False)
        if 'percent_correct' in prob:
            embed.add_field(name='% Correct', value=prob['percent_correct'], inline=False)
        if 'average' in prob:
            embed.add_field(name='Average', value=prob['average'], inline=False)
        return prob['title'], prob['url'], embed

    def embed_leetcode_problem(self, prob):
        embed = discord.Embed()
        embed.colour = self.onlineJudges.colours['leetcode']
        embed.set_thumbnail(url=self.onlineJudges.thumbnails['leetcode'])
        embed.add_field(name='Total ACs', value=prob['total_acs'], inline=False)
        embed.add_field(name='Total Submitted', value=prob['total_submitted'], inline=False)
        embed.add_field(name='Level', value=prob['level'], inline=False)
        embed.add_field(name='Paid?', value='Yes' if prob['paid'] else 'No', inline=False)
        return prob['title'], prob['url'], embed

    async def get_random_problem(self, oj=None, points=None, maximum=None, iden=None, paid=False):
        if oj is None:
            oj = rand.choice(self.onlineJudges.problem_judges)

        oj = self.onlineJudges.get_oj(oj)

        if oj == 'cses' and points is not None:
            raise InvalidParametersException(cses=True)
        elif oj == 'szkopul' and points is not None:
            raise InvalidParametersException(szkopul=True)

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
                        await self.dmoj_user_suggests[iden].update_pp_range()
                    points, maximum = self.dmoj_user_suggests[iden].get_pp_range()
                elif oj == 'codeforces':
                    if iden not in self.cf_user_suggests.keys():
                        self.cf_user_suggests[iden] = CodeforcesUserSuggester(user_data[iden]['codeforces'])
                        await self.cf_user_suggests[iden].update_pp_range()
                    points, maximum = self.cf_user_suggests[iden].get_pp_range()

            if not user_data[iden]['can_repeat']:
                if oj == 'dmoj' and user_data[iden]['dmoj'] is not None:
                    user_response = await webc.webget_json('https://dmoj.ca/api/user/info/%s' % user_data[iden]['dmoj'])
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
                    response = await webc.webget_json('https://codeforces.com/api/user.status?handle=' + user_data[iden]['codeforces'])
                    if response['status'] != 'OK':
                        return None
                    solved = []
                    for sub in response['result']:
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

            if oj != 'leetcode':
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

        elif oj == 'cses':
            prob = rand.choice(self.cses_problems)
            return self.embed_cses_problem(prob)

        elif oj == 'szkopul':
            prob = rand.choice(list(self.szkopul_problems.values()))
            return self.embed_szkopul_problem(prob)

        elif oj == 'leetcode':
            if points is not None:
                if points not in (1, 2, 3):
                    raise InvalidParametersException(leetcode=True)
                if maximum is not None:
                    if maximum not in (1, 2, 3) or maximum < points:
                        raise InvalidParametersException(leetcode=True)
                    else:
                        points = rand.randint(points, maximum)
                def is_level(prob):
                    return prob['level'] == points
                if paid:
                    prob = rand.choice(list(filter(is_level, self.leetcode_problems + self.leetcode_problems_paid)))
                else:
                    prob = rand.choice(list(filter(is_level, self.leetcode_problems)))
            elif paid:
                    prob = rand.choice(self.leetcode_problems + self.leetcode_problems_paid)
            else:
                prob = rand.choice(self.leetcode_problems)
            return self.embed_leetcode_problem(prob)

        else:
            raise NoSuchOJException(oj)

    def check_existing_user(self, user):
        query.insert_ignore_user(user.id)

    def check_existing_server(self, server):
        query.insert_ignore_server(server.id)

    @commands.command(aliases=['r'])
    @commands.bot_has_permissions(embed_links=True)
    async def random(self, ctx, oj=None, points=None, maximum=None):
        self.check_existing_user(ctx.message.author)
        if isinstance(oj, str) and (oj.lower() == 'peg' or oj.lower() == 'wcipeg'):
            await ctx.send(ctx.message.author.display_name + ', Notice: Support for WCIPEG has been discontinued as **PEG Judge shut down at the end of July 2020**\nhttps://wcipeg.com/announcement/9383')
            return
        try:
            title, description, embed = await self.get_random_problem(oj, points, maximum, ctx.message.author.id)
            embed.title = title
            embed.description = description + ' (searched in %ss)' % str(round(self.bot.latency, 3))
            embed.timestamp = datetime.utcnow()
            await ctx.send('Requested problem for ' + ctx.message.author.display_name, embed=embed)
        except IndexError:
            await ctx.send(ctx.message.author.display_name + ', No problem was found. This may be due to the bot updating the problem cache. Please wait a moment, then try again.')
        except NoSuchOJException:
            await ctx.send(ctx.message.author.display_name + ', Invalid query. The online judge must be one of the following: %s.' % self.onlineJudges.problem_judges_str())
        except InvalidParametersException as e:
            await ctx.send(ctx.message.author.display_name + ', ' + str(e))
        except OnlineJudgeHTTPException as e:
            await ctx.send(ctx.message.author.display_name + ', There seems to be a problem with %s. Please try again later :shrug:' % str(e))
        except InvalidQueryException:
            await ctx.send(ctx.message.author.display_name + ', Invalid query. Make sure your points are positive integers.')

    @commands.command(aliases=['toggleRepeat', 'tr'])
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

    @commands.command(aliases=['toggleSuggest', 'ts'])
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

    @commands.command(aliases=['toggleCountry', 'togglecountry', 'setCountry'])
    async def setcountry(self, ctx, code=''):
        try:
            country_object = Country(code)
            self.check_existing_user(ctx.message.author)
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
    @commands.bot_has_permissions(embed_links=True)
    async def user(self, ctx, user: discord.User=None):
        if user is None:
            user = ctx.message.author

        self.check_existing_user(user)
        user_data = query.get_user(user.id)

        embed = discord.Embed(title=user.display_name)
        embed.timestamp = datetime.utcnow()
        embed.colour = discord.Colour(int('0000ff', 16))

        empty = True
        if user_data[user.id]['dmoj'] is not None:
            embed.add_field(name='DMOJ', value='https://dmoj.ca/user/%s' % user_data[user.id]['dmoj'], inline=False)
            empty = False
        if user_data[user.id]['codeforces'] is not None:
            embed.add_field(name='Codeforces', value='https://codeforces.com/profile/%s' % user_data[user.id]['codeforces'], inline=False)
            empty = False
        if user_data[user.id]['country'] is not None:
            embed.add_field(name='Country', value=str(Country(user_data[user.id]['country'])), inline=False)
        if empty:
            embed.description = 'No accounts linked...'
        elif user.id == ctx.message.author.id:
            embed.add_field(name='Can repeat', value=str(user_data[user.id]['can_repeat'] == 1) + ' (If true, problems you have already solved on sites where your account is linked will show up when you request for random problems)', inline=False)
            embed.add_field(name='Can suggest', value=str(user_data[user.id]['can_suggest'] == 1) + ' (If true, suggested problems based on your points on sites where your account is linked will show up when you request for random problems)', inline=False)
        await ctx.send('Requested profile by ' + ctx.message.author.display_name, embed=embed)

    @commands.command(aliases=['si'])
    @commands.bot_has_permissions(embed_links=True)
    async def serverinfo(self, ctx):
        if ctx.message.guild is None:
            await ctx.send(ctx.message.author.display_name + ', You can only request for server info within a server!')
            return

        query.insert_ignore_server(ctx.message.guild.id)
        server_data = query.get_server(ctx.message.guild.id)

        embed = discord.Embed(title=ctx.message.guild.name)
        embed.timestamp = datetime.utcnow()
        embed.set_thumbnail(url=ctx.message.guild.icon_url)
        embed.colour = discord.Colour(int('ffd300', 16))

        embed.add_field(name='Nickname sync', value=str(server_data[ctx.message.guild.id]['nickname_sync'] == 1) + ' (If true, nicknames will be set automatically based on the sync source)', inline=False)
        embed.add_field(name='Role sync', value=str(server_data[ctx.message.guild.id]['role_sync'] == 1) + ' (If true, roles will be set automatically based on the sync source)', inline=False)
        if server_data[ctx.message.guild.id]['nickname_sync'] or server_data[ctx.message.guild.id]['role_sync']:
            embed.add_field(name='Sync source', value=server_data[ctx.message.guild.id]['sync_source'], inline=False)
        embed.add_field(name='Join message', value=str(server_data[ctx.message.guild.id]['join_message'] == 1) + ' (If true, bot will send a default join message whenever a new member joins your server)', inline=False)
        prefix = await self.bot.command_prefix(self.bot, ctx.message)
        embed.add_field(name='Server prefix', value=prefix, inline=False)
        clist = ''
        for text_channel in ctx.message.guild.text_channels:
            if query.exists('subscriptions_contests', 'channel_id', text_channel.id):
                clist += text_channel.mention + '\n'
        embed.add_field(name='Contest notification channel(s)', value='None' if clist == '' else clist, inline=False)
        await ctx.send(ctx.message.author.display_name + ', Here is your requested info!', embed=embed)

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
                f = webc.webget_text(ctx.message.attachments[0].url)
                source = f.content
            self.check_existing_user(ctx.message.author)
            user_data = query.get_user(ctx.message.author.id)
            if problem == '^' and user_data[ctx.message.author.id]['last_dmoj_problem'] is not None:
                problem = user_data[ctx.message.author.id]['last_dmoj_problem']
            id = await user_session.submit(problem, self.language.getId(lang), source)
            response = await user_session.getTestcaseStatus(id)
            responseText = str(response)
            if len(responseText) > 1950:
                responseText = responseText[1950:] + '\n(Result cut off to fit message length limit)'
            await ctx.send(ctx.message.author.display_name + ', ' + responseText + '\nTrack your submission here: https://dmoj.ca/submission/' + str(id))
        except InvalidDMOJSessionException:
            await ctx.send(ctx.message.author.display_name + ', Failed to connect, or problem not available. Make sure you are submitting to a valid problem, check your authentication, and try again.')

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if str(after.status) == 'offline' and str(before.status) != 'offline' and after.id in self.dmoj_sessions.keys():
            await after.send('Attention! You have been logged out of the account %s due to being offline (Note that your account will still be linked to your Discord account, but will now be unable to submit to problems)' % self.dmoj_sessions.pop(after.id))

    @tasks.loop(hours=23)
    async def refresh_dmoj_problems(self):
        await self.parse_dmoj_problems()
        self.fetch_times['dmoj'] = time()

    @refresh_dmoj_problems.before_loop
    async def refresh_dmoj_problems_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=25)
    async def refresh_cf_problems(self):
        self.parse_cf_problems()
        self.fetch_times['codeforces'] = time()

    @refresh_cf_problems.before_loop
    async def refresh_cf_problems_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=26)
    async def refresh_atcoder_problems(self):
        self.parse_atcoder_problems()
        self.fetch_times['atcoder'] = time()

    @refresh_atcoder_problems.before_loop
    async def refresh_atcoder_problems_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24*7)
    async def refresh_cses_problems(self):
        self.parse_cses_problems()
        self.fetch_times['cses'] = time()

    @refresh_cses_problems.before_loop
    async def refresh_cses_problems_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=1, minutes=27)
    async def refresh_szkopul_problems(self):
        self.parse_szkopul_problems()
        self.fetch_times['szkopul'] = time()

    @refresh_szkopul_problems.before_loop
    async def refresh_szkopul_problems_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=28)
    async def refresh_leetcode_problems(self):
        self.parse_leetcode_problems()
        self.fetch_times['leetcode'] = time()

    @refresh_leetcode_problems.before_loop
    async def refresh_leetcode_problems_before(self):
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
