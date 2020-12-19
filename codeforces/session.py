import bs4 as bs
import hashlib
from time import time
import random as rand
from utils.webclient import webc
from aiohttp import ClientError


class InvalidCodeforcesSessionException(Exception):
    
    def __init__(self):
        pass

class NoSubmissionsException(Exception):
    
    def __init__(self):
        pass

class SessionTimeoutException(Exception):

    def __init__(self, time):
        self.time = time

class PrivateSubmissionException(Exception):

    def __init__(self):
        pass

class Session:
    BASE_URL = 'https://codeforces.com'

    def __init__(self, account, user):
        self.account = account
        self.user = user
        self.handle = None

    async def generate(self):
        try:
            response = await webc.webget_text(self.BASE_URL + '/profile/' + self.account)
            soup = bs.BeautifulSoup(response, 'lxml')
            if soup.find('h1').find('a').find('span') is not None:
                self.handle = soup.find('h1').find('a').contents[0].contents[0] + soup.find('h1').find('a').contents[1]
            else:
                self.handle = soup.find('h1').find('a').contents[0]
        except ClientError:
            raise InvalidCodeforcesSessionException
        except AttributeError:
            raise InvalidCodeforcesSessionException
        self.time = time()
        self.hash = hashlib.sha256((str(self.user.id) + self.handle + str(self.time) + str(rand.getrandbits(256))).encode('utf-8')).hexdigest()

    def __str__(self):
        return self.handle

    async def validate(self):
        if time() - self.time > 180:
            raise SessionTimeoutException(self.time)
        try:
            response = await webc.webget_json('https://codeforces.com/api/user.status?handle=' + self.handle)
        except ClientError:
            raise InvalidCodeforcesSessionException
        submission_data = response['result']
        if len(submission_data) == 0:
            return NoSubmissionsException
        try:
            if 'contestId' in submission_data[0]:
                response = await webc.webget_text('https://codeforces.com/contest/' + str(submission_data[0]['contestId']) + '/submission/' + str(submission_data[0]['id']))
            elif 'problemsetName' in submission_data[0]['problem']:
                response = await webc.webget_text('https://codeforces.com/problemsets/' + submission_data[0]['problem']['problemsetName'] + '/submission/99999/' + str(submission_data[0]['id']))
        except ClientError:
            raise InvalidCodeforcesSessionException
        soup = bs.BeautifulSoup(response, 'lxml')
        if soup.find('title').contents[0] == 'Codeforces':
            raise PrivateSubmissionException
        source = soup.find('body').find('pre').contents[0]
        return self.hash in source
