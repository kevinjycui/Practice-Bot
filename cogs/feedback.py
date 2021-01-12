import discord
from discord.ext import commands, tasks
from time import time
from datetime import datetime


class FeedbackCog(commands.Cog):
    suggesters = []
    suggester_times = []

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['feedback, fb'])
    async def suggest(self, ctx, *, content):
        if ctx.message.author.id in self.suggesters and time() - self.suggester_times[self.suggesters.index(ctx.message.author.id)] < 3600:
            await ctx.send(ctx.message.author.display_name + ', Please wait %d minutes before making another suggestion!' % int((3600 - time() + self.suggester_times[self.suggesters.index(ctx.message.author.id)])//60))
            return

        user = self.bot.get_user(self.bot.owner_id)
        await user.send('```From: %s\n%s```' % (ctx.message.author.name, content))
        content = content.replace('`', '')
        await ctx.send(ctx.message.author.display_name + ', Suggestion sent!\n```From: You\nTo: The Dev\nAt: ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + '\n' + content + '```\n_If you want to add more to your suggestion, consider submitting an issue (this will allow the developer to interact with you but you will no longer be anonymous)_\n<https://github.com/kevinjycui/Practice-Bot/issues>')

def setup(bot):
    bot.add_cog(FeedbackCog(bot))
