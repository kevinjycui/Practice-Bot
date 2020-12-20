import discord

class NoSuchOJException(Exception):
    def __init__(self, oj):
        self.oj = oj

class OnlineJudges:
    judges = ('dmoj', 'codeforces', 'atcoder', 'leetcode', 'cses', 'szkopul', 'codechef')
    contest_judges = ('dmoj', 'codeforces', 'atcoder', 'codechef')
    accounts = ('dmoj', 'codeforces')
    formal_names = {
        'dmoj': 'DMOJ',
        'codeforces': 'Codeforces',
        'atcoder': 'AtCoder',
        'cses': 'CSES',
        'szkopul': 'Szkopuł',
        'leetcode': 'Leetcode',
        'codechef': 'CodeChef'
    }
    aliases = {
        'cf': 'codeforces',
        'at': 'atcoder',
        'ac': 'atcoder',
        'szkopuł': 'szkopul',
        'lc': 'leetcode',
        'cc': 'codechef'
    }
    thumbnails = {
        'dmoj': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/dmoj-thumbnail.png',
        'codeforces': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/cf-thumbnail.png',
        'atcoder': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/at-thumbnail.png',
        'cses': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/cses-thumbnail.png',
        'szkopul': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/szkopul-thumbnail.png',
        'leetcode': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/lc-thumbnail.png',
        'codechef': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/cc-thumbnail.png'
    }
    colours = {
        'dmoj': discord.Colour(int('fcdc00', 16)),
        'codeforces': discord.Colour(int('198dcd', 16)),
        'atcoder': discord.Colour(int('f5f5f5', 16)),
        'cses': discord.Colour(int('f6e0a8', 16)),
        'szkopul': discord.Colour(int('f93800', 16)),
        'leetcode': discord.Colour(int('f89f1b', 16)),
        'codechef': discord.Colour(int('5c4435', 16))
    }
    judge_to_aliases = {}
    for judge in judges:
        judge_to_aliases[judge] = []
    for alias, judge in list(aliases.items()):
        judge_to_aliases[judge].append(alias)

    def get_oj(self, oj):
        if oj is None:
            raise NoSuchOJException(oj)
        if oj.lower() in self.judges:
            return oj.lower()
        if oj.lower() in self.aliases.keys():
            return self.aliases[oj.lower()]
        raise NoSuchOJException(oj)

    def can_sync(self, oj):
        oj_name = self.get_oj(oj)
        return oj_name == 'dmoj' or oj_name == 'codeforces'

    def oj_exists(self, oj):
        return self.get_oj(oj.lower()) in self.judges

    # def oj_to_embed(self, oj):
    #     oj = self.get_oj(oj)
    #     if oj == 'dmoj':
    #         about = 'DMOJ, DMOJ: Modern Online Judge, or Don Mills Online Judge, is a Canadian \
    #         modern contest platform and archive of programming problems made in 2014 by \
    #         Tudor Brindus and Guanzhong Chen from Don Mills Collegiate Institute and based in \
    #         Toronto. It is entirely open-source and inspired by WCIPEG, which merged with DMOJ \
    #         in 2020. DMOJ is known to have many problems from the CCC, CCO, IOI, and COCI. Notable \
    #         contests hosted by DMOJ include the DMOPC or DMOJ Monthly Open Programming Contest and \
    #         the DMPG or Don Mills Programming Gala. DMOJ contests support ICPC/IOI/AtCoder/ECOO formats. \
    #         As of 2020, DMOJ has over 50, 000 users and supports 65 programming languages. DMOJ is \
    #         primarily in English but also has translations to other languages such as Japanese, \
    #         Vietnamese, and Simplified Chinese. DMOJ has hosted national olympiads such as the MOI \
    #         (Moroccan Olympiad in Informatics) in 2017.'
    #         embed = discord.Embed(title='DMOJ: Modern Online Judge', description=about, inline=False)
    #         embed.add_field(name='Country', value=':flag_ca: Canada', inline=False)
    #         embed.add_field(name='Abbreviations', value='`$oj dmoj`', inline=False)
    #         embed.add_field(name='Random Problems', value='Yes', inline=False)
    #         embed.add_field(name='Contest Notifications', value='Yes', inline=False)
    #         embed.add_field(name='Rating Roles', value='Yes', inline=False)
    #         embed.add_field(name='Account Link', value='Yes', inline=False)
    #         embed.add_field(name='Submission', value='Yes', inline=False)
    #         return embed
    #     elif oj == 'codeforces':
    #         about = 'Codeforces is a Russian online judge and contest platform made in 2009 by students \
    #         from ITMO University led by Mikhail Mirzayanov based in St. Petersburg. As of 2018, Codeforces \
    #         has over 600, 000 users, \
    #         surpassing TopCoder in 2013. Codeforces contests include Codeforces Rounds, which are 2 hour \
    #         rounds held about once a week and Educational Rounds, held 2-3 times per month and followed by \
    #         a 24 hour hacking period. Rated contests are split into divisions, with Div 1 being the most difficult \
    #         and Div 4 being the least difficult. Notable users of Codeforces include top sport programmers like \
    #         Gennady Korotkevich, Petr Mitrichev, Benjamin Qi and Makoto Soejima. Codeforces is available in both \
    #         English and Russian. Many universities use Codeforces as a tool for teaching concepts in Competitive \
    #         Programming.'
    #         embed = discord.Embed(title='Codeforces', description=about, inline=False)
    #         embed.add_field(name='Country', value=':flag_ru: Russia', inline=False)
    #         embed.add_field(name='Abbreviations', value='`$oj codeforces`, `$oj cf`', inline=False)
    #         embed.add_field(name='Random Problems', value='Yes', inline=False)
    #         embed.add_field(name='Contest Notifications', value='Yes', inline=False)
    #         embed.add_field(name='Rating Roles', value='No', inline=False)
    #         embed.add_field(name='Account Link', value='No', inline=False)
    #         embed.add_field(name='Submission', value='No', inline=False)
    #         return embed
    #     elif oj == 'atcoder':
    #         about = 'AtCoder is a Japanese programming contest management service that specializes in the development \
    #         and administration of programming contests. It also specializes in the plan, administration of the \
    #         programming contest, and adoption support and ability judgment duties of the software engineer. AtCoder was \
    #         made in 2012 and based in Tokyo. AtCoder has 3 official contest types: AtCoder Grand Contest (AGC), which is the \
    #         most difficult, AtCoder Regular Contest (ARC), and AtCoder Beginner Contest (ABC). AGC is held about twice \
    #         a month, with other weeks consisting of both ARC and ABC. AtCoder is available in both \
    #         English and Japanese.'
    #         embed = discord.Embed(title='AtCoder', description=about, inline=False)
    #         embed.add_field(name='Abbreviations', value='`$oj atcoder`, `$oj at`, `$oj ac`', inline=False)
    #         embed.add_field(name='Country', value=':flag_jp: Japan', inline=False)
    #         embed.add_field(name='Random Problems', value='Yes', inline=False)
    #         embed.add_field(name='Contest Notifications', value='Yes', inline=False)
    #         embed.add_field(name='Rating Roles', value='No', inline=False)
    #         embed.add_field(name='Account Link', value='No', inline=False)
    #         embed.add_field(name='Submission', value='No', inline=False)
    #         return embed
    #     elif oj == 'cses':
    #         about = 'CSES or Code Submission Evaluation System is a Finnish programming problem archive made by Antti Laaksonen and Topi Talvitie \
    #         in 2013 based in Helsinki. The site is most well-known for its CSES Problem Set, but also archives problems from the \
    #         BOI and CEOI among others. Notable users of CSES include Benjamin Qi. The site has problems available in both English and \
    #         Finnish. As of 2020, the CSES Problem Set contains 200 tasks with 10, 000 users.'
    #         embed = discord.Embed(title='CSES', description=about, inline=False)
    #         embed.add_field(name='Country', value=':flag_fi: Finland', inline=False)
    #         embed.add_field(name='Abbreviations', value='`$oj cses`', inline=False)
    #         embed.add_field(name='Random Problems', value='Yes', inline=False)
    #         embed.add_field(name='Contest Notifications', value='N/A', inline=False)
    #         embed.add_field(name='Rating Roles', value='N/A', inline=False)
    #         embed.add_field(name='Account Link', value='No', inline=False)
    #         embed.add_field(name='Submission', value='No', inline=False)
    #         return embed
    #     elif oj == 'szkopul':
    #         about = 'Szkopuł is a Polish online judge and problem archive based in Warsaw containing problems from the CEOI, EJOI, IOI, \
    #         POI, OIJ, and PA. The site is available in English and Polish.'
    #         embed = discord.Embed(title='Szkopuł', description=about, inline=False)
    #         embed.add_field(name='Country', value=':flag_pl: Poland', inline=False)
    #         embed.add_field(name='Abbreviations', value='`$oj szkopul`, `$oj szkopuł`', inline=False)
    #         embed.add_field(name='Random Problems', value='Yes', inline=False)
    #         embed.add_field(name='Contest Notifications', value='No', inline=False)
    #         embed.add_field(name='Rating Roles', value='N/A', inline=False)
    #         embed.add_field(name='Account Link', value='No', inline=False)
    #         embed.add_field(name='Submission', value='No', inline=False)
    #         return embed
    #     raise NoSuchOJException(oj)

    def __str__(self):
        output = ''
        for judge, aliases in list(self.judge_to_aliases.items()):
            output += self.formal_names[judge] + ' (' + ', '.join([judge] + aliases)  + '), '
        return output
