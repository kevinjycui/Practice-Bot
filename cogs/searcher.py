import discord
from discord.ext import commands, tasks
import random as rand
import requests
import json
import urllib
import wikipedia
from time import time
import yaml
from datetime import datetime
import bs4 as bs
from bs4.element import Comment


try:
    config_file = open('config.yml')
except FileNotFoundError:
    config_file = open('example_config.yaml')
finally:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
    cat_api = config['cats']['token']
    client_id, client_secret = config['jdoodle']['client_id'], config['jdoodle']['client_secret']

def json_get(api_url):
    response = requests.get(api_url)

    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    return None

class SearcherCog(commands.Cog):

    wait_time = 0

    def __init__(self, bot):
        self.bot = bot

    def getSummary(self, name):
        try:
            if urllib.request.urlopen('https://en.wikipedia.org/wiki/'+name).getcode() != 404:
                return wikipedia.page(name), wikipedia.summary(name, sentences=5)
        except wikipedia.DisambiguationError as e:
            if len(e.options) > 0:
                return self.getSummary(e.options[0].replace(' ', '_'))
            else:
                return None, None
        except:
            return None, None

    def valid(self, url):
        try:
            if urllib.request.urlopen(url).getcode() == 200:
                return True
            else:
                return False
        except:
            return False

    def accountScrape(self, name):
        accounts = {}
        if self.valid('https://dmoj.ca/api/user/info/%s' % name):
            accounts['DMOJ'] = 'https://dmoj.ca/user/%s' % name
        cf_data = requests.get('https://codeforces.com/api/user.info?handles=%s' % name)
        if cf_data.status_code == 200 and cf_data.json()['status'] == 'OK':
            accounts['Codeforces'] = 'https://codeforces.com/profile/%s' % name
        if self.valid('https://atcoder.jp/users/%s' % name):
            accounts['AtCoder'] = 'https://atcoder.jp/users/%s' % name
        if self.valid('https://wcipeg.com/user/%s' % name):
            accounts['WCIPEG'] = 'https://wcipeg.com/user/%s' % name
        if self.valid('https://github.com/%s' % name):
            accounts['GitHub'] = 'https://github.com/%s' % name
        return accounts

    def tag_visible(self, element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    def wcipegScrape(self, name):
        if self.valid('http://wcipeg.com/wiki/%s' % name.replace(' ', '_')):
            try:
                url = 'http://wcipeg.com/wiki/%s' % name.replace(' ', '_')
                wiki_response = requests.get(url).text
                soup = bs.BeautifulSoup(wiki_response, 'lxml')
                scan = True
                title = soup.find('h1', attrs={'id': 'firstHeading'}).contents[0]
                texts = soup.find('div', attrs={'id': 'mw-content-text'}).find('p').findAll(text=True)
                visible_texts = filter(self.tag_visible, texts)  
                summary = ' '.join(t.strip() for t in visible_texts)
                return title, summary, url
            except:
                return None

    @commands.command()
    async def whatis(self, ctx, *, name=None):
        if name is None:
            prefix = await self.bot.command_prefix(self.bot, ctx.message)
            await ctx.send(ctx.message.author.display_name + ', Invalid query. Please use format `%swhatis <thing>`.' % prefix)
            return
        peg_res = self.wcipegScrape(name)
        if peg_res is not None:
            title, summary, url = peg_res
            embed = discord.Embed(title=title, description=url + ' (searched in %ss)' % str(round(self.bot.latency, 3)))
            embed.timestamp = datetime.utcnow()
            embed.add_field(name='Summary', value=summary, inline=False)
            await ctx.send(ctx.message.author.display_name + ', Here\'s what I found!', embed=embed)
            return
        page, summary = self.getSummary(name.replace(' ', '_'))
        if summary is None:
            await ctx.send(ctx.message.author.display_name + ', Sorry, I couldn\'t find anything on "%s"' % name)
            return
        embed = discord.Embed(title=page.title, description=page.url+' (searched in %ss)' % str(round(self.bot.latency, 3)))
        embed.timestamp = datetime.utcnow()
        embed.add_field(name='Summary', value=summary, inline=False)
        await ctx.send(ctx.message.author.display_name + ', Here\'s what I found!', embed=embed)

    # @commands.command()
    # async def whois(self, ctx, *, name=None):
    #     if name is None:
    #         prefix = await self.bot.command_prefix(self.bot, ctx.message)
    #         await ctx.send(ctx.message.author.display_name + ', Invalid query. Please use format `%swhois <name>`.' % prefix)
    #         return
    #     accounts = self.accountScrape(name)
    #     if len(accounts) == 0:
    #         await ctx.send(ctx.message.author.display_name + ', Sorry, found 0 results for %s' % name)
    #         return
    #     embed = discord.Embed(title=name, description=' (searched in %ss)' % str(round(self.bot.latency, 3)))
    #     embed.timestamp = datetime.utcnow()
    #     for oj, url in accounts.items():
    #         embed.add_field(name=oj, value=url, inline=False)
    #     await ctx.send(ctx.message.author.display_name + ', Found %d result(s) for `%s`' % (len(accounts), name), embed=embed)

    @commands.command()
    async def cat(self, ctx):
        if rand.randint(0, 100) == 0:
            data = [{'url':'https://media.discordapp.net/attachments/511001840071213067/660303090444140545/539233495000809475.png'}]
        else:
            data = json_get('https://api.thecatapi.com/v1/images/search?x-api-key=' + cat_api)
        await ctx.send(ctx.message.author.display_name + ', :smiley_cat: ' + data[0]['url'])

    @commands.command()
    async def run(self, ctx, lang=None, stdin=None, *, script=None):
        if lang is None or stdin is None or script is None:
            prefix = await self.bot.command_prefix(self.bot, ctx.message)
            await ctx.send(ctx.message.author.display_name + ', Invalid query. Please use format `%srun <language> "<stdin>" <script>`.' % prefix)
            return
        headers = {'Content-type':'application/json', 'Accept':'application/json'}
        credit_spent = requests.post('https://api.jdoodle.com/v1/credit-spent', json={'clientId': client_id, 'clientSecret': client_secret}, headers=headers).json()
        if 'error' not in credit_spent and credit_spent['used'] >= 200:
            await ctx.send(ctx.message.author.display_name + ', Sorry, the daily limit of compilations has been surpassed (200). Please wait until 12:00 AM UTC')
            return
        if time() - self.wait_time < 15:
            await ctx.send(ctx.message.author.display_name + ', Queue in process, please wait %d seconds' % (15 - (time() - self.wait_time)))
            return
        self.wait_time = time()
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
        response = requests.post('https://api.jdoodle.com/v1/execute', json=data, headers=headers).json()
        if 'error' in response and response['statusCode'] == 400:
            await ctx.send(ctx.message.author.display_name + ', Invalid request. Perhaps the language you\'re using is unavailable.')
        elif 'error' in response:
            await ctx.send(ctx.message.author.display_name + ', Compilation failed. The compiler may be down.')
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

def setup(bot):
    bot.add_cog(SearcherCog(bot))
