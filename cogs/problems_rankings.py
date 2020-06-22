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

        with open('data/server_nicks.json', 'r', encoding='utf8', errors='ignore') as f:
            self.server_nicks = list(map(int, json.load(f)))

        self.update_ranks.start()

    def update_server_roles(self):
        with open('data/server_roles.json', 'w') as json_file:
            json.dump(self.server_roles, json_file)

    def update_server_nicks(self):
        with open('data/server_nicks.json', 'w') as json_file:
            json.dump(self.server_nicks, json_file)

    @commands.command()
    async def login(self, ctx, site=None, token=None):
        if ctx.guild is not None:
            await ctx.send(ctx.message.author.mention + ' Please do not post your DMOJ API token on a server! Login command should be used in DMs only!')
        else:
            if site is None or token is None:
                await ctx.send('Invalid query. Please use format `%slogin <site> <token>`.' % prefix)
                return
            self.checkExistingUser(ctx.message.author)
            if site.lower() == 'dmoj':
                iden = str(ctx.message.author.id)
                if ctx.message.author.id in self.sessions:
                    prev = 'logged out of %s and ' % self.sessions.pop(ctx.message.author.id)
                else:
                    prev = ''
                try:
                    self.sessions[ctx.message.author.id] = Session(token)
                    self.global_users[iden]['dmoj'] = str(self.sessions[ctx.message.author.id])
                    for guild in self.bot.guilds:
                        if guild.id in self.server_nicks:
                            for member in guild.members:
                                if member.id == ctx.message.author.id:
                                    try:
                                        await member.edit(nick=self.global_users[iden]['dmoj'])
                                    except:
                                        pass
                    self.update_users()
                    await ctx.send('Successfully ' + prev + 'logged in with submission permissions as %s! (Note that for security reasons, you will be automatically logged out after the cache resets or when you go offline. You may delete the message containing your token now)' % self.sessions[ctx.message.author.id])
                except InvalidSessionException:
                    await ctx.send('Token invalid, failed to log in (your DMOJ API token can be found by going to https://dmoj.ca/edit/profile/ and selecting the __Generate__ or __Regenerate__ option next to API Token). Note: The login command will ONLY WORK IN DIRECT MESSAGE. Please do not share this token with anyone else.')
            else:
                await ctx.send('Sorry, that site does not exist or logins to that site are not available yet')

    @commands.command()
    async def logout(self, ctx, site=None):
        if ctx.guild is not None:
            mention = ctx.message.author.mention + ' '
        else:
            mention = ''
        if site is None:
            await ctx.send(mention + 'Invalid query. Please use format `%slogout <site>`.' % prefix)
        elif site.lower() == 'dmoj':
            if ctx.message.author.id not in self.sessions.keys():
                await ctx.send(mention + 'You are already not logged in!')
                return
            await ctx.send(mention + 'Successfully logged out of submission permissions from %s! (Note that your account will still be linked to your Discord account, but will now be unable to submit to problems)' % self.sessions.pop(ctx.message.author.id))
        else:
            await ctx.send(mention + 'Sorry, that site does not exist or logins to that site are not available yet')

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

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def toggleNicks(self, ctx):
        if int(ctx.message.guild.id) not in self.server_nicks:
            self.server_nicks.append(int(ctx.message.guild.id))
            for member in ctx.message.guild.members:
                if str(member.id) in self.global_users.keys() and 'dmoj' in self.global_users[str(member.id)]:
                    try:
                        await member.edit(nick=self.global_users[str(member.id)]['dmoj'])
                    except discord.errors.Forbidden:
                        await ctx.send('Failed to change nickname of user %s#%s, insufficient permissions' % (member.name, member.discriminator))
            await ctx.send(ctx.message.author.mention + ' DMOJ based nicknames set to `ON`')
        else:
            self.server_nicks.remove(int(ctx.message.guild.id))
            await ctx.send(ctx.message.author.mention + ' DMOJ based nicknames set to `OFF`')
        self.update_server_nicks()

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
