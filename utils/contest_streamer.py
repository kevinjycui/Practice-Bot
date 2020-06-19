import discord
from time import time
import random as rand
from datetime import datetime


class Contest(object):

    def __init__(self, data):
        self.data = data

    def asdict(self):
        return self.data

    def __eq__(self, other):
        return self.data['description'] == other.data['description']

    def __str__(self):
        return str(self.data)

    def __hash__(self):
        return hash(str(self))

class NoContestsAvailableException(Exception):
    pass

class RandomContests(object):
    all_contest_embeds = []
    fetch_time = 0

    dmoj_contests = []
    cf_contests = []
    atcoder_contests = []

    dmoj_contest_titles = []
    cf_contest_titles = []
    atcoder_contest_titles = []

    contest_objects = []

    def get_random_contests(self, number):
        if len(self.all_contest_embeds) == 0:
            raise NoContestsAvailableException
        rand.shuffle(self.all_contest_embeds)
        result = []
        for i in range(min(number, len(self.all_contest_embeds))):
            result.append(self.all_contest_embeds[i])
        return result

    def reset_contest(self, oj):
        if oj == 'dmoj':
            self.dmoj_contests = []
            self.dmoj_contest_titles = []
        elif oj == 'cf':
            self.cf_contests = []
            self.cf_contest_titles = []
        elif oj == 'atcoder':
            self.atcoder_contests = []
            self.atcoder_contest_titles = []

    def set_time(self):
        self.fetch_time = time()

    def parse_dmoj_contests(self, contests):
        if contests is not None:
            for contest in range(len(contests)):
                name, details = list(contests.items())[contest]
                if datetime.strptime(details['start_time'].replace(':', ''), '%Y-%m-%dT%H%M%S%z') > datetime.now(pytz.utc):
                    spec = json_get('https://dmoj.ca/api/contest/info/' + name)
                    url = 'https://dmoj.ca/contest/' + name
                    contest_data = {
                        'title': ':trophy: %s' % details['name'],
                        'description': url,
                        'thumbnail': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/dmoj-thumbnail.png',
                        'Start Time': datetime.strptime(details['start_time'].replace(':', ''), '%Y-%m-%dT%H%M%S%z').strftime('%B %d, %Y %H:%M:%S%z'),
                        'End Time': datetime.strptime(details['end_time'].replace(':', ''), '%Y-%m-%dT%H%M%S%z').strftime('%B %d, %Y %H:%M:%S%z'),

                    }
                    if details['time_limit']:
                        contest_data['Time Limit'] = details['time_limit']
                    if len(details['labels']) > 0:
                        contest_data['Labels'] = ', '.join(details['labels'])
                    contest_data['Rated'] ='Yes' if spec['is_rated'] else 'No'
                    contest_data['Format'] = spec['format']['name']
                    if contest_data['title'] not in self.dmoj_contest_titles:
                        self.dmoj_contest_titles.append(contest_data['title'])
                        self.dmoj_contests.append(Contest(contest_data))
            self.dmoj_contests = list(set(self.dmoj_contests))

    def parse_cf_contests(self, contests):
        if contests is not None and contests['status'] == 'OK':
            for contest in range(len(contests.get('result', []))):
                details = contests['result'][contest]
                if details['phase'] == 'BEFORE':
                    url = 'https://codeforces.com/contest/' + str(details['id'])
                    contest_data = {
                        'title': ':trophy: %s' % details['name'],
                        'description': url,
                        'thumbnail': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/cf-thumbnail.png',
                        'Type': details['type'],
                        'Start Time': datetime.utcfromtimestamp(details['startTimeSeconds']).strftime('%Y-%m-%d %H:%M:%S'),
                        'Time Limit': '%s:%s:%s' % (str(details['durationSeconds']//(24*3600)).zfill(2), str(details['durationSeconds']%(24*3600)//3600).zfill(2), str(details['durationSeconds']%3600//60).zfill(2))
                    }
                    if contest_data['title'] not in self.cf_contest_titles:
                        self.cf_contest_titles.append(contest_data['title'])
                        self.cf_contests.append(Contest(contest_data))
            self.cf_contests = list(set(self.cf_contests))

    def parse_atcoder_contests(self, contests):
        if contests is not None:
            for contest in range(len(contests)):
                details = contests[contest]
                if details['startTimeSeconds'] > time():
                    url = 'https://atcoder.jp/contests/' + details['id']
                    contest_data = {
                        'title': ':trophy: %s' % details['title'].replace('\n', '').replace('\t', '').replace('◉', ''),
                        'description': url,
                        'thumbnail': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/at-thumbnail.png',
                        'Start Time': datetime.utcfromtimestamp(details['startTimeSeconds']).strftime('%Y-%m-%d %H:%M:%S'),
                        'Time Limit': '%s:%s:%s' % (str(details['durationSeconds']//(24*3600)).zfill(2), str(details['durationSeconds']%(24*3600)//3600).zfill(2), str(details['durationSeconds']%3600//60).zfill(2)),
                        'Rated Range': details['ratedRange']
                    }
                    if contest_data['title'] not in self.atcoder_contest_titles:
                        self.atcoder_contest_titles.append(contest_data['title'])
                        self.atcoder_contests.append(Contest(contest_data))
            self.atcoder_contests = list(set(self.atcoder_contests))

    def embed_contest(self, contest):
        embed = discord.Embed(title=contest['title'], description=contest['description'])
        embed.timestamp = datetime.utcnow()
        embed.set_thumbnail(url=contest['thumbnail'])
        for key in list(contest.keys()):
            if key != key.lower():
                embed.add_field(name=key, value=contest[key], inline=False)
        return embed

    def generate_stream(self):
        self.all_contest_embeds = []
        self.contest_objects = []
        for contest in self.dmoj_contests:
            self.all_contest_embeds.append(self.embed_contest(contest.asdict()))
            self.contest_objects.append(contest)
        for contest in self.cf_contests:
            self.all_contest_embeds.append(self.embed_contest(contest.asdict()))
            self.contest_objects.append(contest)
        for contest in self.atcoder_contests:
            self.all_contest_embeds.append(self.embed_contest(contest.asdict()))
            self.contest_objects.append(contest)
        self.all_contest_embeds = list(set(self.all_contest_embeds))
        self.contest_objects = list(set(self.contest_objects))
