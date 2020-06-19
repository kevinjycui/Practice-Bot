import discord
from discord.ext import commands, tasks
from datetime import datetime
import random as rand
import requests
import bs4 as bs


accounts = ('dmoj',)

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

class RandomProblem(object):
    global_users = None
    problems_by_points = {'dmoj':{}, 'cf':{}, 'at':{}, 'peg':{}}
    dmoj_problems = None
    cf_problems = None
    at_problems = None
    peg_problems = {}

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
        if iden is not None and oj in accounts and 'repeat' in self.global_users[iden] and not self.global_users[iden]['repeat']:
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
