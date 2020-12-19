import bs4 as bs
from time import time
from utils.webclient import webc


class UserSuggester(object):

    def __init__(self, handle):
        self.handle = handle
        self.points_min = 1
        self.points_max = 50
        self.expand_up = True
    
    async def update_pp_range(self):
        response = await webc.webget_json('https://codeforces.com/api/user.status?handle=%s&from=1&count=100' % self.handle)
        if response['status'] != 'OK':
            return
        self.time = time()
        submissions = response['result']
        points = []
        for submission in submissions:
            try:
                points.append(submission['problem']['rating'])
            except KeyError:
                pass
        if len(points) == 0:
            self.points_min = 0
            self.points_max = 500
            return
        points.sort()
        points_len = min(len(points), 100)

        self.points_max = 2*sum(points[0:points_len//2])//points_len
        self.points_min = 2*sum(points[points_len//2:points_len])//points_len

    def get_pp_range(self):
        return tuple(map(str, (self.points_min, self.points_max)))

    def expand_pp_range(self):
        if self.points_max != 50 and self.expand_up:
            self.points_max = min(self.points_max+500, 4000)
            self.expand_up = False
        else:
            self.points_min = max(0, self.points_min-250)
            self.expand_up = True
