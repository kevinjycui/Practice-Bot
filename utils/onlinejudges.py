import discord

class NoSuchOJException(Exception):
    def __init__(self, oj):
        self.oj = oj

class OnlineJudges:
    judges = ('dmoj', 'codeforces', 'atcoder', 'leetcode', 'cses', 'szkopul', 'codechef', 'topcoder')
    problem_judges = ('dmoj', 'codeforces', 'atcoder', 'leetcode', 'cses', 'szkopul')
    contest_judges = ('dmoj', 'codeforces', 'atcoder', 'leetcode', 'codechef', 'topcoder')
    accounts = ('dmoj', 'codeforces')
    formal_names = {
        'dmoj': 'DMOJ',
        'codeforces': 'Codeforces',
        'atcoder': 'AtCoder',
        'cses': 'CSES',
        'szkopul': 'Szkopuł',
        'leetcode': 'LeetCode',
        'codechef': 'CodeChef',
        'topcoder': 'TopCoder'
    }
    aliases = {
        'cf': 'codeforces',
        'at': 'atcoder',
        'ac': 'atcoder',
        'szkopuł': 'szkopul',
        'lc': 'leetcode',
        'leet': 'leetcode',
        'cc': 'codechef',
        'chef': 'codechef',
        'tc': 'topcoder',
        'top': 'topcoder'
    }
    thumbnails = {
        'dmoj': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/dmoj-thumbnail.png',
        'codeforces': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/cf-thumbnail.png',
        'atcoder': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/at-thumbnail.png',
        'cses': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/cses-thumbnail.png',
        'szkopul': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/szkopul-thumbnail.png',
        'leetcode': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/lc-thumbnail.png',
        'codechef': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/cc-thumbnail.png',
        'topcoder': 'https://raw.githubusercontent.com/kevinjycui/Practice-Bot/master/assets/tc-thumbnail.png'
    }
    colours = {
        'dmoj': discord.Colour(int('fcdc00', 16)),
        'codeforces': discord.Colour(int('198dcd', 16)),
        'atcoder': discord.Colour(int('f5f5f5', 16)),
        'cses': discord.Colour(int('f6e0a8', 16)),
        'szkopul': discord.Colour(int('f93800', 16)),
        'leetcode': discord.Colour(int('f89f1b', 16)),
        'codechef': discord.Colour(int('5c4435', 16)),
        'topcoder': discord.Colour(int('8cc543', 16))
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

    def __str__(self):
        output = ''
        for judge, aliases in list(self.judge_to_aliases.items()):
            output += self.formal_names[judge] + ' (' + ', '.join([judge] + aliases)  + '), '
        return output

    def problem_judges_str(self):
        output = ''
        for judge in self.problem_judges:
            output += self.formal_names[judge] + ' (' + ', '.join([judge] + self.judge_to_aliases[judge])  + '), '
        return output[:-1]

    def contest_judges_str(self):
        output = ''
        for judge in self.contest_judges:
            output += self.formal_names[judge] + ' (' + ', '.join([judge] + self.judge_to_aliases[judge])  + '), '
        return output[:-1]
