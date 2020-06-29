import discord
from discord.ext import commands, tasks
from time import time
import random as rand
from datetime import datetime, timedelta
import json
import requests
import pytz
from backend import mySQLConnection as query


def json_get(api_url):
    response = requests.get(api_url)

    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    return None

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

class ContestCog(commands.Cog):
    all_contest_embeds = []
    fetch_time = 0

    dmoj_contests = []
    cf_contests = []
    atcoder_contests = []

    dmoj_contest_titles = []
    cf_contest_titles = []
    atcoder_contest_titles = []

    contest_objects = []

    def __init__(self, bot):
        self.bot = bot

        with open('data/contests.json', 'r', encoding='utf8', errors='ignore') as f:
            prev_contest_data = json.load(f)
            self.contest_cache = []
            for data in prev_contest_data:
                self.contest_cache.append(Contest(data))

        self.subscribed_channels = query.get_all_subs()

        self.refresh_contests.start()

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
                        'Start Time': datetime.strptime(details['start_time'].replace(':', ''), '%Y-%m-%dT%H%M%S%z').strftime('%Y-%m-%d %H:%M:%S'),
                        'End Time': datetime.strptime(details['end_time'].replace(':', ''), '%Y-%m-%dT%H%M%S%z').strftime('%Y-%m-%d %H:%M:%S'),

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

    def update_contest_cache(self):
        with open('data/contests.json', 'w') as json_file:
            prev_contest_data = []
            for contest in self.contest_cache:
                prev_contest_data.append(contest.asdict())
            json.dump(prev_contest_data, json_file)

    @commands.command(aliases=['c'])
    async def contests(self, ctx, numstr='1'):
        if numstr == 'all':
            number = len(self.all_contest_embeds)
        elif not numstr.isdigit():
            prefix = await self.bot.command_prefix(self.bot, ctx.message)
            await ctx.send(ctx.message.author.display_name + ', Invalid query. Please use format `%scontests <# of contests>`' % prefix)
        else:
            number = int(numstr)
        try:
            contestList = self.get_random_contests(number)
            await ctx.send(ctx.message.author.display_name + ', Sending %d random upcoming contest(s). Last fetched, %d minutes ago' % (len(contestList), (time()-self.fetch_time)//60))
            for contest in contestList:
                await ctx.send(embed=contest)
        except NoContestsAvailableException:
            await ctx.send(ctx.message.author.display_name + ', Sorry, there are not upcoming contests currently available.')

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def sub(self, ctx, channel: discord.TextChannel):
        if channel.id in self.subscribed_channels:
            await ctx.send(ctx.message.author.display_name + ', That channel is already subscribed to contest notifications.')
            return
        self.subscribed_channels.append(channel.id)
        query.sub_channel(channel.id)
        await ctx.send(ctx.message.author.display_name + ', ' + channel.mention + ' subscribed to contest notifications.')

    @commands.command()
    @commands.guild_only()
    async def subs(self, ctx):
        clist = ctx.message.author.display_name + ', Contest notification channels in this server:\n'
        for text_channel in ctx.message.guild.text_channels:
            if text_channel.id in self.subscribed_channels:
                clist += text_channel.mention + '\n'
        if clist == ctx.message.author.display_name + ', Contest notification channels in this server:\n':
            await ctx.send(ctx.message.author.display_name + ', There are no channels subscribed to contest notifications in this server :slight_frown:')
        else:
            await ctx.send(clist)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def unsub(self, ctx, channel: discord.TextChannel):
        if channel.id not in self.subscribed_channels:
            await ctx.send(ctx.message.author.display_name + ', That channel is already not subscribed to contest notifications.')
            return
        self.subscribed_channels.remove(channel.id)
        query.unsub_channel(channel.id)
        await ctx.send(ctx.message.author.display_name + ', ' + channel.mention + ' is no longer a contest notification channel.')

    def is_upcoming(self, contest):
        return datetime.strptime(contest.asdict()['Start Time'], '%Y-%m-%d %H:%M:%S') > datetime.now() - timedelta(days=7)

    @tasks.loop(minutes=5)
    async def refresh_contests(self):
        try:
            self.reset_contest('dmoj')
            self.parse_dmoj_contests(json_get('https://dmoj.ca/api/contest/list'))
        except:
            pass

        try:
            self.reset_contest('cf')
            self.parse_cf_contests(json_get('https://codeforces.com/api/contest.list'))
        except:
            pass

        try:
            self.reset_contest('atcoder')
            self.parse_atcoder_contests(json_get('https://atcoder-api.appspot.com/contests'))
        except:
            pass

        self.set_time()
        self.generate_stream()

        new_contests = list(set(self.contest_objects).difference(set(self.contest_cache)))

        for channel_id in self.subscribed_channels:
            try:
                channel = self.bot.get_channel(channel_id)
                for contest in new_contests:
                    await channel.send(embed=self.embed_contest(contest.asdict()))
            except:
                pass

        self.contest_cache = list(filter(self.is_upcoming, list(set(self.contest_objects).union(set(self.contest_cache)))))
        self.update_contest_cache()

    @refresh_contests.before_loop
    async def check_contests_before(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(ContestCog(bot))
