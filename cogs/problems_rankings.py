from time import time
from cogs.problems import *

class ProblemRankingCog(ProblemCog):

    update_index = 0
    ratings = {
        range(3000, 4000): ('Target', discord.Colour(int('ee0000', 16))),
        range(2200, 2999): ('Grandmaster', discord.Colour(int('ee0000', 16))),
        range(1800, 2199): ('Master', discord.Colour(int('ffb100', 16))),
        range(1500, 1799): ('Candidate Master', discord.Colour(int('993399', 16))),
        range(1200, 1499): ('Expert', discord.Colour(int('5597ff', 16))),
        range(1000, 1199): ('Amateur', discord.Colour(int('4bff4b', 16))),
        range(0, 999): ('Newbie', discord.Colour(int('999999', 16))),
        (None,): ('Unrated', discord.Colour.default()),
    }

    def __init__(self, bot):
        ProblemCog.__init__(self, bot)

        with open('data/server_roles.json', 'r', encoding='utf8', errors='ignore') as f:
            self.server_roles = list(map(int, json.load(f)))

        self.update_ranks.start()

    def update_server_roles(self):
        with open('data/server_roles.json', 'w') as json_file:
            json.dump(self.server_roles, json_file)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def toggleRanks(self, ctx):
        if int(ctx.message.guild.id) not in self.server_roles:
            self.server_roles.append(int(ctx.message.guild.id))
            names = []
            for role in ctx.message.guild.roles:
                names.append(role.name)
            for role in list(self.ratings.values()):
                if role[0] not in names:
                    await ctx.message.guild.create_role(name=role[0], colour=role[1], mentionable=False)
            await ctx.send(ctx.message.author.mention + ' DMOJ based ranked roles set to `ON`')
        else:
            self.server_roles.remove(int(ctx.message.guild.id))
            await ctx.send(ctx.message.author.mention + ' DMOJ based ranked roles set to `OFF`')
        self.update_server_roles()

    @tasks.loop(minutes=5)
    async def update_ranks(self):

        if self.update_index >= len(self.global_users):
            self.update_index = 0
        while self.update_index < len(self.global_users):
            member_id = list(self.global_users.keys())[self.update_index]
            if 'dmoj' in self.global_users[member_id]:
                break
            self.update_index += 1
        if self.update_index == len(self.global_users):
            return

        user_info = json_get('https://dmoj.ca/api/user/info/%s' % self.global_users[member_id]['dmoj'])
        current_rating = user_info['contests']['current_rating']
        for rating, role in list(self.ratings.items()):
            if current_rating in rating:
                rating_name = role[0]
        for guild in self.bot.guilds:
            if int(guild.id) not in self.server_roles:
                continue
            names = []
            for role in guild.roles:
                names.append(role.name)
            for role in list(self.ratings.values()):
                if role[0] not in names:
                    await guild.create_role(name=role[0], colour=role[1], mentionable=False)
            try:
                for member in guild.members:
                    if member_id == str(member.id):
                        for rating, role in list(self.ratings.items()):
                            role = discord.utils.get(guild.roles, name=role[0])
                            if current_rating in rating and role not in member.roles:
                                await member.add_roles(role)
                            elif current_rating not in rating and role in member.roles:
                                await member.remove_roles(role)
                        break
            except:
                pass

        self.update_index += 1

    @update_ranks.before_loop
    async def update_ranks_before(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(ProblemRankingCog(bot))
