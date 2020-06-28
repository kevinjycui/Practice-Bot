import requests
import bs4 as bs
import hashlib
from time import time
import random as rand


class InvalidCodeforcesSessionException(Exception):
    
    def __init__(self, code):
        self.code = code

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
        response = requests.get(self.BASE_URL + '/profile/' + account)
        if response.status_code != 200:
            raise InvalidCodeforcesSessionException(response.status_code)
        soup = bs.BeautifulSoup(response.text, 'lxml')
        try:
            self.handle = soup.find('h1').find('a').contents[0]
        except AttributeError:
            raise InvalidCodeforcesSessionException(404)
        self.time = time()
        self.hash = hashlib.sha256((str(user.id) + self.handle + str(self.time) + str(rand.getrandbits(256))).encode('utf-8')).hexdigest()

    def __str__(self):
        return self.handle

    def validate(self):
        if time() - self.time > 60:
            raise SessionTimeoutException(self.time)
        response = requests.get('https://codeforces.com/api/user.status?handle=' + self.handle)
        if response.status_code != 200 and response.json()['status'] == 'OK':
            raise InvalidCodeforcesSessionException(response.status_code)
        submission_data = response.json()['result']
        if len(submission_data) == 0:
            return NoSubmissionsException
        if 'contestId' in submission_data[0]:
            response = requests.get('https://codeforces.com/contest/' + str(submission_data[0]['contestId']) + '/submission/' + str(submission_data[0]['id']))
        elif 'problemsetName' in submission_data[0]['problem']:
            response = requests.get('https://codeforces.com/problemsets/' + submission_data[0]['problem']['problemsetName'] + '/submission/99999/' + str(submission_data[0]['id']))
        if response.status_code != 200:
            raise InvalidCodeforcesSessionException(response.status_code)
        soup = bs.BeautifulSoup(response.text, 'lxml')
        if soup.find('title').contents[0] == 'Codeforces':
            raise PrivateSubmissionException
        source = soup.find('body').find('pre').contents[0]
        return self.hash in source

if __name__ == '__main__':
    class User:
        id = 1234
    session = Session('ManchurioX', User())
    session.token = '93a0cd0a9e572f50321bfe7dc9b1cea25f820567131a6ba49baac4acf8cd444e'
    session.validate()
