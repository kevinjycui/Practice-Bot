from time import time
from cogs.problems import *

class ProblemRankingCog(ProblemCog):

    update_dmoj_index = 0
    dmoj_ratings = {
        range(3000, 4000): ('Target', discord.Colour(int('ee0000', 16))),
        range(2200, 2999): ('Grandmaster', discord.Colour(int('ee0000', 16))),
        range(1800, 2199): ('Master', discord.Colour(int('ffb100', 16))),
        range(1500, 1799): ('Candidate Master', discord.Colour(int('993399', 16))),
        range(1200, 1499): ('Expert', discord.Colour(int('5597ff', 16))),
        range(1000, 1199): ('Amateur', discord.Colour(int('4bff4b', 16))),
        range(0, 999): ('Newbie', discord.Colour(int('999999', 16))),
        (None,): ('Unrated', discord.Colour.default()),
    }
    cf_ratings = [
        ('Legendary Grandmaster', discord.Colour(int('ee0000', 16))),
        ('International Grandmaster', discord.Colour(int('ee0000', 16))),
        ('Grandmaster', discord.Colour(int('ee0000', 16))),
        ('International Master', discord.Colour(int('ffb100', 16))),
        ('Master', discord.Colour(int('ffb100', 16))),
        ('Candidate Master', discord.Colour(int('993399', 16))),
        ('Expert', discord.Colour(int('5597ff', 16))),
        ('Specialist', discord.Colour(int('03a89e', 16))),
        ('Apprentice', discord.Colour(int('4bff4b', 16))),
        ('Pupil', discord.Colour(int('88cc22', 16))),
        ('Newbie', discord.Colour(int('999999', 16))),
        ('Unrated', discord.Colour.default()),
    ]

    def __init__(self, bot):
        ProblemCog.__init__(self, bot)

        self.dmoj_server_roles = query.get_all_role_sync('dmoj')
        self.cf_server_roles = query.get_all_role_sync('codeforces')

        self.dmoj_server_nicks = query.get_all_nick_sync('dmoj')
        self.cf_server_nicks = query.get_all_nick_sync('codeforces')

        self.update_dmoj_ranks.start()
        self.update_cf_ranks.start()

    @commands.command()
    async def connect(self, ctx, site=None, token=None):
        if ctx.guild is not None:
            if site is not None and site.lower() == 'dmoj':
                await ctx.send(ctx.message.author.display_name + ', Please do not use the connect command in a server! Ensure direct messaging is on and use the command through a direct message with the bot. IF YOU JUST SHARED YOUR DMOJ API TOKEN, REGENERATE YOUR TOKEN IMMEDIATELY. Your token should remain secret, and sharing it may compromise the security of your DMOJ account.')
            else:
                await ctx.send(ctx.message.author.display_name + ', Please do not use the connect command in a server! Ensure direct messaging is on and use the command through a direct message with the bot.')
            await ctx.message.author.send('You can connect an account using one of the following commands: \n\n`$connect dmoj <dmoj-api-token>` (your DMOJ API token can be found by going to https://dmoj.ca/edit/profile/ and selecting the __Generate__ or __Regenerate__ option next to API Token)\n\n`$connect cf <codeforces-handle>`')
        elif site is None:
            prefix = await self.bot.command_prefix(self.bot, ctx.message)
            await ctx.send('Invalid query. Please use one of the following formats:\n\n`%sconnect dmoj <dmoj-api-token>` (your DMOJ API token can be found by going to https://dmoj.ca/edit/profile/ and selecting the __Generate__ or __Regenerate__ option next to API Token)\n\n`%sconnect cf <codeforces-handle>`' % (prefix, prefix))
        elif site.lower() == 'dmoj':
            if token is None:
                prefix = await self.bot.command_prefix(self.bot, ctx.message)
                await ctx.send('Invalid query. Please use format `%sconnect dmoj <dmoj-api-token>` (your DMOJ API token can be found by going to https://dmoj.ca/edit/profile/ and selecting the __Generate__ or __Regenerate__ option next to API Token).' % prefix)
            else:
                self.check_existing_user(ctx.message.author)
                try:
                    self.dmoj_sessions[ctx.message.author.id] = DMOJSession(token)
                    self.global_users[ctx.message.author.id]['dmoj'] = str(self.dmoj_sessions[ctx.message.author.id])
                    query.update_user(ctx.message.author.id, 'dmoj', self.global_users[ctx.message.author.id]['dmoj'])
                    for guild in self.bot.guilds:
                        if guild.id in self.dmoj_server_nicks:
                            for member in guild.members:
                                if member.id == ctx.message.author.id:
                                    try:
                                        await member.edit(nick=self.global_users[ctx.message.author.id]['dmoj'])
                                    except:
                                        pass
                    await ctx.send('Successfully logged in with submission permissions as %s on DMOJ! (Note that for security reasons, submission permissions will be automatically turned off after the cache resets or when you go offline. When this occurs, you will have to log in using your token again to submit, but your account will remain linked. You may delete the message containing your token now)' % self.dmoj_sessions[ctx.message.author.id])
                except InvalidSessionException:
                    await ctx.send('Token invalid, failed to log in (your DMOJ API token can be found by going to https://dmoj.ca/edit/profile/ and selecting the __Generate__ or __Regenerate__ option next to API Token).')
                
        elif site.lower() == 'cf' or site.lower() == 'codeforces':               
            self.check_existing_user(ctx.message.author)
            if token is None or (ctx.message.author.id in self.cf_sessions.keys() and token.lower() == str(self.cf_sessions[ctx.message.author.id]).lower()):
                try:
                    if ctx.message.author.id in self.cf_sessions:
                        validated = self.cf_sessions[ctx.message.author.id].validate()
                        if not validated:
                            raise NoSubmissionsException
                        query.update_user(ctx.message.author.id, 'codeforces', str(self.cf_sessions[ctx.message.author.id]))
                        self.global_users[ctx.message.author.id]['codeforces'] = str(self.cf_sessions[ctx.message.author.id])
                        for guild in self.bot.guilds:
                            if guild.id in self.cf_server_nicks:
                                for member in guild.members:
                                    if member.id == ctx.message.author.id:
                                        try:
                                            await member.edit(nick=self.global_users[ctx.message.author.id]['codeforces'])
                                        except:
                                            pass
                        await ctx.send('Successfully linked your account as %s on Codeforces!' % str(self.cf_sessions[ctx.message.author.id]))
                        self.cf_sessions.pop(ctx.message.author.id)
                    else:
                        prefix = await self.bot.command_prefix(self.bot, ctx.message)
                        await ctx.send('Sorry, no ongoing connect sessions to Codeforces. This could occur if the cache is reset due to maintenance or if you did not initialise a session. Try using command `%sconnect cf <handle>` to initialise a session.' % prefix)
                except InvalidCodeforcesSessionException:
                    await ctx.send('Failed to connect to %s. User does not exist or Codeforces may be down currently.' % token)
                except NoSubmissionsException:
                    await ctx.send('Could not find any submissions that contain the token as a comment. Submit to the a problem with the token as a comment and try again.')
                except SessionTimeoutException:
                    self.cf_sessions.pop(ctx.message.author.id)
                    prefix = await self.bot.command_prefix(self.bot, ctx.message)
                    await ctx.send('Session timed out (submit within 1 minute of using the connect command). Try initialising another session `%sconnect cf <handle>`.' % prefix)
                except PrivateSubmissionException:
                    await ctx.send('The bot was unable to access your most recent submission. Ensure that your most recent submission is on a problem with public submissions (not a problem from ACMSGURU or in an ongoing contest)')
            else:
                if self.global_users[ctx.message.author.id]['codeforces'] is not None and token.lower() == self.global_users[ctx.message.author.id]['codeforces'].lower():
                    await ctx.send('The Codeforces account %s is already connected!' % self.global_users[ctx.message.author.id]['codeforces'])
                    return
                try:
                    self.cf_sessions[ctx.message.author.id] = CodeforcesSession(token, ctx.message.author)
                    hash = self.cf_sessions[ctx.message.author.id].hash
                    prefix = await self.bot.command_prefix(self.bot, ctx.message)
                    await ctx.send('Login session for user %s initialised. Add the following token as a comment to your most recent public submission to any problem. Then, use the command `%sconnect cf` to validate.```%s```Example in C/C++/Java:```// %s```Example in Python:```# %s```' % \
                    (str(self.cf_sessions[ctx.message.author.id]), prefix, hash, hash, hash))
                except InvalidCodeforcesSessionException:
                    await ctx.send('Failed to connect to %s. User does not exist or Codeforces may be down currently.' % token)

        else:
            prefix = await self.bot.command_prefix(self.bot, ctx.message)
            await ctx.send('Invalid query. Please use one of the following formats:\n\n`%sconnect dmoj <dmoj-api-token>` (your DMOJ API token can be found by going to https://dmoj.ca/edit/profile/ and selecting the __Generate__ or __Regenerate__ option next to API Token)\n\n`%sconnect cf <codeforces-handle>`' % (prefix, prefix))

    @commands.command()
    async def disconnect(self, ctx, site=None):
        if ctx.guild is not None:
            mention = ctx.message.author.display_name + ', '
        else:
            mention = ''
        if site is None:
            prefix = await self.bot.command_prefix(self.bot, ctx.message)
            await ctx.send(mention + 'Invalid query. Please use format `%sdisconnect <site>`.' % prefix)
        elif site.lower() == 'dmoj':
            self.check_existing_user(ctx.message.author)
            if self.global_users[ctx.message.author.id]['dmoj'] is None:
                await ctx.send(mention + 'Your DMOJ account is already not connected!')
                return
            if ctx.message.author.id in self.dmoj_sessions.keys():
                self.dmoj_sessions.pop(ctx.message.author.id)
            handle = self.global_users[ctx.message.author.id]['dmoj']
            self.global_users[ctx.message.author.id]['dmoj'] = None
            query.update_user(ctx.message.author.id, 'dmoj', None)
            await ctx.send(mention + 'Successfully disconnected your DMOJ account: %s' % handle)
        elif site.lower() == 'cf' or site.lower() == 'codeforces':
            self.check_existing_user(ctx.message.author)
            if self.global_users[ctx.message.author.id]['codeforces'] is None:
                await ctx.send(mention + 'Your Codeforces account is already not connected!')
                return
            if ctx.message.author.id in self.dmoj_sessions.keys():
                self.dmoj_sessions.pop(ctx.message.author.id)
            handle = self.global_users[ctx.message.author.id]['codeforces']
            self.global_users[ctx.message.author.id]['codeforces'] = None
            query.update_user(ctx.message.author.id, 'codeforces', None)
            await ctx.send(mention + 'Successfully disconnected your Codeforces account: %s' % handle)          
        else:
            await ctx.send(mention + 'Sorry, that site does not exist or logins to that site are not available yet')

    @commands.command(aliases=['toggleSync'])
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def togglesync(self, ctx, site=None):
        self.check_existing_server(ctx.message.guild)
        if site is None:
            prefix = await self.bot.command_prefix(self.bot, ctx.message)
            await ctx.send(ctx.message.author.display_name + ', Invalid query. Please use format `%stoggleranks <sync source>` (available sync sources are DMOJ and Codeforces, or OFF to turn automatic roles off.' % prefix)
            return
        site = site.lower()
        if site == 'dmoj':
            if ctx.message.guild.id in self.dmoj_server_roles:
                await ctx.send(ctx.message.author.display_name + ', DMOJ based ranked roles already set to `ON`!')
                return
            try:
                for role in ctx.message.guild.roles:
                    if (role.name, role.colour) in self.cf_ratings:
                        await role.delete()
                names = []
                for role in ctx.message.guild.roles:
                    names.append(role.name)
                for role in list(self.dmoj_ratings.values()):
                    if role[0] not in names:
                        await ctx.message.guild.create_role(name=role[0], colour=role[1], mentionable=False)
                if ctx.message.guild.id in self.cf_server_roles:
                    self.cf_server_roles.remove(ctx.message.guild.id)
                self.dmoj_server_roles.append(ctx.message.guild.id)
                query.update_server(ctx.message.guild.id, 'role_sync', True)
                query.update_server(ctx.message.guild.id, 'sync_source', 'dmoj')
                forbidden_users = []
                for member in ctx.message.guild.members:
                    if member.id in self.global_users.keys() and self.global_users[member.id]['dmoj'] is not None:
                        try:
                            await member.edit(nick=self.global_users[member.id]['dmoj'])
                        except discord.errors.Forbidden:
                            forbidden_users.append('%s#%s' % (member.name, member.discriminator))
                self.dmoj_server_nicks.append(ctx.message.guild.id)
                query.update_server(ctx.message.guild.id, 'nickname_sync', True)
                await ctx.send(ctx.message.author.display_name + ', DMOJ based nicknames and ranked roles set to `ON`. It may take some time for all roles to fully update. Skipped changing the nickname of %d members due to having lower permissions.' % len(forbidden_users))
            except discord.errors.Forbidden:
                await ctx.send(ctx.message.author.display_name + ', Toggle failed, make sure that the bot has the Manage Roles and Manage Roles permissions and try again.')
        elif site == 'cf' or site == 'codeforces':
            if ctx.message.guild.id in self.cf_server_roles:
                await ctx.send(ctx.message.author.display_name + ', Codeforces based ranked roles already set to `ON`!')
                return
            try:
                for role in ctx.message.guild.roles:
                    if (role.name, role.colour) in self.dmoj_ratings.values():
                        await role.delete()
                names = []
                for role in ctx.message.guild.roles:
                    names.append(role.name)
                for role in self.cf_ratings:
                    if role[0] not in names:
                        await ctx.message.guild.create_role(name=role[0], colour=role[1], mentionable=False)
                if ctx.message.guild.id in self.dmoj_server_roles:
                    self.dmoj_server_roles.remove(ctx.message.guild.id)
                self.cf_server_roles.append(ctx.message.guild.id)
                query.update_server(ctx.message.guild.id, 'role_sync', True)
                query.update_server(ctx.message.guild.id, 'sync_source', 'codeforces')
                forbidden_users = []
                for member in ctx.message.guild.members:
                    if member.id in self.global_users.keys() and self.global_users[member.id]['codeforces'] is not None:
                        try:
                            await member.edit(nick=self.global_users[member.id]['codeforces'])
                        except discord.errors.Forbidden:
                            forbidden_users.append('%s#%s' % (member.name, member.discriminator))
                self.dmoj_server_nicks.append(ctx.message.guild.id)
                query.update_server(ctx.message.guild.id, 'nickname_sync', True)
                await ctx.send(ctx.message.author.display_name + ', Codeforces based nicknames and ranked roles set to `ON`. It may take some time for all roles to fully update. Skipped changing the nickname of %d members due to having lower permissions.' % len(forbidden_users))
            except discord.errors.Forbidden:
                await ctx.send(ctx.message.author.display_name + ', Toggle failed, make sure that the bot has the Manage Roles and Manage Roles permissions and try again.')
        elif site == 'off':
            if ctx.message.guild.id not in self.cf_server_roles and ctx.message.guild.id not in self.dmoj_server_roles:
                await ctx.send(ctx.message.author.display_name + ', Ranked roles already set to `OFF`!')
                return
            try:
                for role in ctx.message.guild.roles:
                    if (role.name, role.colour) in self.dmoj_ratings.values() or (role.name, role.colour) in self.cf_ratings:
                        await role.delete()
                if ctx.message.guild.id in self.dmoj_server_roles:
                    self.dmoj_server_roles.remove(ctx.message.guild.id)
                if ctx.message.guild.id in self.cf_server_roles:
                    self.cf_server_roles.remove(ctx.message.guild.id)
                query.update_server(ctx.message.guild.id, 'role_sync', False)
                if ctx.message.guild.id in self.dmoj_server_nicks:
                    self.dmoj_server_nicks.remove(ctx.message.guild.id)
                if ctx.message.guild.id in self.cf_server_nicks:
                    self.cf_server_nicks.remove(ctx.message.guild.id)
                query.update_server(ctx.message.guild.id, 'nickname_sync', False)
                await ctx.send(ctx.message.author.display_name + ', Ranked roles set to `OFF`')
            except discord.errors.Forbidden:
                await ctx.send(ctx.message.author.display_name + ', Toggle failed, make sure that the bot has the Manage Roles and Manage Roles permissions and try again.')

    @tasks.loop(minutes=5)
    async def update_dmoj_ranks(self):
        if self.update_dmoj_index >= len(self.global_users):
            self.update_dmoj_index = 0
        while self.update_dmoj_index < len(self.global_users):
            member_id = list(self.global_users.keys())[self.update_dmoj_index]
            if self.global_users[member_id]['dmoj'] is not None:
                break
            self.update_dmoj_index += 1
        if self.update_dmoj_index == len(self.global_users):
            return

        user_info = json_get('https://dmoj.ca/api/user/info/%s' % self.global_users[member_id]['dmoj'])
        current_rating = user_info['contests']['current_rating']
        for rating, role in list(self.dmoj_ratings.items()):
            if current_rating in rating:
                rating_name = role[0]
        for guild in self.bot.guilds:
            self.check_existing_server(guild)
            if int(guild.id) not in self.dmoj_server_roles:
                continue
            names = []
            for role in guild.roles:
                names.append(role.name)
            for role in list(self.dmoj_ratings.values()):
                if role[0] not in names:
                    await guild.create_role(name=role[0], colour=role[1], mentionable=False)
            try:
                for member in guild.members:
                    if member_id == member.id:
                        for rating, rolename in list(self.dmoj_ratings.items()):
                            role = discord.utils.get(guild.roles, name=rolename[0])
                            if current_rating in rating and role not in member.roles:
                                await member.add_roles(role)
                            elif current_rating not in rating and role in member.roles:
                                await member.remove_roles(role)
                        break
            except:
                pass

        self.update_dmoj_index += 1

    @update_dmoj_ranks.before_loop
    async def update_dmoj_ranks_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=5)
    async def update_cf_ranks(self):
        handles = query.get_cf_handles()
        users_info = json_get('https://codeforces.com/api/user.info?handles=%s' % ';'.join(list(handles.keys())))['result']
        for user_info in users_info:
            member_id = handles[user_info['handle']]
            for guild in self.bot.guilds:
                self.check_existing_server(guild)
                if int(guild.id) not in self.cf_server_roles:
                    continue
                names = []
                for role in guild.roles:
                    names.append(role.name)
                for role in self.cf_ratings:
                    if role[0] not in names:
                        await guild.create_role(name=role[0], colour=role[1], mentionable=False)
                try:
                    for member in guild.members:
                        if member_id == member.id:
                            if 'rank' not in user_info:
                                role = discord.utils.get(guild.roles, name='Unrated')
                                await member.add_roles(role)
                            for rolename in self.cf_ratings:
                                role = discord.utils.get(guild.roles, name=rolename[0])
                                if 'rank' in user_info and user_info['rank'].lower() == role.name.lower() and role not in member.roles:
                                    await member.add_roles(role)
                                elif ('rank' not in user_info or user_info['rank'].lower() != role.name.lower()) and role in member.roles:
                                    await member.remove_roles(role)
                            break
                except Exception as e:
                    print(e)
                    pass

    @update_cf_ranks.before_loop
    async def update_cf_ranks_before(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(ProblemRankingCog(bot))
