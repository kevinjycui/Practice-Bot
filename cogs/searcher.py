import discord
from discord.ext import commands, tasks
import random as rand
import json
import urllib
import wikipedia
from time import time
import yaml
from datetime import datetime
import bs4 as bs
from bs4.element import Comment
from utils.webclient import webc


try:
    config_file = open('config.yml')
except FileNotFoundError:
    config_file = open('example_config.yml')
finally:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
    cat_api = config['cats']['token']
    client_id, client_secret = config['jdoodle']['client_id'], config['jdoodle']['client_secret']

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

    def tag_visible(self, element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    async def wcipegScrape(self, name):
        if self.valid('http://wcipeg.com/wiki/%s' % name.replace(' ', '_')):
            try:
                url = 'http://wcipeg.com/wiki/%s' % name.replace(' ', '_')
                wiki_response = await webc.webget_text(url)
                soup = bs.BeautifulSoup(wiki_response, 'lxml')
                scan = True
                title = soup.find('h1', attrs={'id': 'firstHeading'}).contents[0]
                texts = soup.find('div', attrs={'id': 'mw-content-text'}).find('p').find_all(text=True)
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
        peg_res = await self.wcipegScrape(name)
        if peg_res is not None:
            title, summary, url = peg_res
            embed = discord.Embed(title=title, description=url + ' (searched in %ss)' % str(round(self.bot.latency, 3)))
            embed.timestamp = datetime.utcnow()
            embed.add_field(name='Summary', value=summary[-1024:], inline=False)
            await ctx.send(ctx.message.author.display_name + ', Here\'s what I found!', embed=embed)
            return
        page, summary = self.getSummary(name.replace(' ', '_'))
        if summary is None:
            await ctx.send(ctx.message.author.display_name + ', Sorry, I couldn\'t find anything on "%s"' % name)
            return
        embed = discord.Embed(title=page.title, description=page.url+' (searched in %ss)' % str(round(self.bot.latency, 3)))
        embed.timestamp = datetime.utcnow()
        embed.add_field(name='Summary', value=summary[-1024:], inline=False)
        await ctx.send(ctx.message.author.display_name + ', Here\'s what I found!', embed=embed)

    @commands.command()
    async def cat(self, ctx):
        if rand.randint(0, 100) == 0:
            data = [{'url':'https://bit.ly/3jiPSzb'}]
        else:
            data = await webc.webget_json('https://api.thecatapi.com/v1/images/search?x-api-key=' + cat_api)
        await ctx.send(ctx.message.author.display_name + ', :smiley_cat: ' + data[0]['url'])

    @commands.command()
    async def run(self, ctx, lang=None, stdin=None, *, script=None):
        if lang is None or stdin is None or script is None:
            prefix = await self.bot.command_prefix(self.bot, ctx.message)
            await ctx.send(ctx.message.author.display_name + ', Invalid query. Please use format `%srun <language> "<stdin>" <script>`.' % prefix)
            return
        headers = {'Content-type':'application/json', 'Accept':'application/json'}
        credit_spent = await webc.webpost_json('https://api.jdoodle.com/v1/credit-spent', json={'clientId': client_id, 'clientSecret': client_secret}, headers=headers)
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
        response = await webc.webpost_json('https://api.jdoodle.com/v1/execute', json=data, headers=headers)
        if 'error' in response and response['statusCode'] == 400:
            await ctx.send(ctx.message.author.display_name + ', Invalid request. Perhaps the language you\'re using is unavailable. See languages here: https://docs.jdoodle.com/compiler-api/compiler-api#what-languages-and-versions-supported')
        elif 'error' in response:
            await ctx.send(ctx.message.author.display_name + ', Compilation failed. The compiler may be down.')
        else:
            message = '\n'
            message += 'CPU Time: `' + ((str(response['cpuTime']) + 's') if response['cpuTime'] is not None else 'N/A') + '`\n'
            message += 'Memory: `' + ((str(response['memory']) + 'KB') if response['memory'] is not None else 'N/A') + '`\n'
            try:
                output_message = ''
                if len(response['output']) > 0:
                    output_message += '\n```' + response['output'] + '```'
                else:
                    output_message += '\n```\n```'
                await ctx.send(ctx.message.author.display_name + message + output_message)

            except discord.errors.HTTPException:
                with open('data/solution.txt', 'w+') as f:
                    f.write(response['output'])
                await ctx.send(ctx.message.author.display_name + message + '\n That\'s a really long output, I put it in this file for you.', file=discord.File('data/solution.txt', 'output.txt'))    


def setup(bot):
    bot.add_cog(SearcherCog(bot))
