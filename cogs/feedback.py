import discord
from discord.ext import commands, tasks
from time import time
from smtplib import SMTP_SSL as SMTP
from smtplib import SMTPException
from email.mime.text import MIMEText
import yaml
from datetime import datetime


try:
    config_file = open('config.yaml')
except FileNotFoundError:
    config_file = open('example_config.yaml')
finally:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
    USERNAME = config['smtp']['email']
    PASSWORD = config['smtp']['password']

class EmailCog(commands.Cog):
    suggesters = []
    suggester_times = []

    SMTPserver = 'smtp.gmail.com'

    def __init__(self, bot):
        self.bot = bot

    def send(self, author, content):
        text_subtype = 'plain'

        subject = 'Suggestion from user %s (id %d)' % (author.name, author.id)
        sender = 'interface.practice.bot@gmail.com'
        destination = ['dev.practice.bot@gmail.com']

        msg = MIMEText(content, text_subtype)
        msg['Subject'] = subject
        msg['From'] = sender
        conn = SMTP(self.SMTPserver)
        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)
        try:
            conn.sendmail(sender, destination, msg.as_string())
        finally:
            conn.quit()

    @commands.command()
    async def suggest(self, ctx, *, content):
        if ctx.message.author.id in self.suggesters and time() - self.suggester_times[self.suggesters.index(ctx.message.author.id)] < 3600:
            await ctx.send(ctx.message.author.display_name + ', Please wait %d minutes before making another suggestion!' % int((3600 - time() + self.suggester_times[self.suggesters.index(ctx.message.author.id)])//60))
            return

        user = self.bot.get_user(self.bot.owner_id)
        await user.send('```From: %s\n%s```' % (ctx.message.author.name, content))

        try:
            self.send(ctx.message.author, content)
            if ctx.message.author.id in self.suggesters:
                self.suggester_times[self.suggesters.index(ctx.message.author.id)] = time()
            else:
                self.suggesters.append(ctx.message.author.id)
                self.suggester_times.append(time())
        except SMTPException:
            pass
        finally:
            await ctx.send(ctx.message.author.display_name + ', Suggestion sent!\n```From: You\nTo: The Dev\nAt: ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + '\n' + content + '```')

def setup(bot):
    bot.add_cog(EmailCog(bot))
