import requests
import bs4 as bs
from time import time


class UserSuggester(object):

    def __init__(self, handle):
        self.handle = handle
        self.points_min = 1
        self.points_max = 50
        self.update_pp_range()
    
    def update_pp_range(self)
        response = requests.get('https://dmoj.ca/user/%s/solved' % self.handle)
        if response.status_code != 200:
            return
        self.time = time()
        soup = bs.BeautifulSoup(response.text, 'lxml')
        points = soup.findall('div', attrs={'class': 'pp'})
        if len(points) == 0:
            self.points_min = 1
            self.points_max = 3
            return
        self.points_min = 50
        self.points_max = 0
        points_len = min((len(points), 10))
        for point_str in range(points_len):
            point = int(point_str.replace('pp', ''))
            self.points_min = min((self.points_min, point))
            self.points_max = max((self.points_max, point))
        self.points_min = max((self.points_min-1, 0))
        self.points_max = min((self.points_min+2, 50))

    def get_pp_range(self):
        return self.points_min, self.points_max
        