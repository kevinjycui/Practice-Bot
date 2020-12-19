import bs4 as bs
import hashlib
from dmoj.language import Language
from dmoj.result import Result
from dmoj.testcase import Testcase
from utils.webclient import webc
from aiohttp import ClientError


class InvalidDMOJSessionException(Exception):
    
    def __init__(self):
        pass

class VerificationException(Exception):
    
    def __init__(self, hash):
        self.hash = hash

class Session:
    BASE_URL = 'https://dmoj.ca'
    gradingStatuses = ['QU', 'P', 'G']

    def __init__(self, token, user):
        self.token = token
        self.user = user
        self.handle = None

    async def generate(self):
        try:
            doc = await webc.webget_text(self.BASE_URL + '/edit/profile/', headers={'Authorization': 'Bearer %s' % self.token})
            soup = bs.BeautifulSoup(doc, 'lxml')
            self.handle = soup.find('span', attrs={'id' : 'user-links'}).find('b').contents[0]
            noAuthReq = await webc.webget_text(self.BASE_URL + '/user/' + self.handle)
            self.hash = hashlib.sha256((str(self.user.id) + self.handle).encode('utf-8')).hexdigest()
            if self.hash not in noAuthReq:
                raise VerificationException(self.hash)
        except:
            raise InvalidDMOJSessionException

    def __str__(self):
        return self.handle

    async def getAuthRequest(self, url):
        return await webc.webget_text(url, headers={'Authorization': 'Bearer %s' % self.token})

    async def postAuthRequest(self, url, data):
        return await webc.webpost(url, headers={'Authorization': 'Bearer %s' % self.token}, data=data)

    async def submit(self, problem, lang, code):
        global BASE_URL
        submitUrl = self.BASE_URL + '/problem/' + problem + '/submit'
        try:
            submitRes = await self.postAuthRequest(submitUrl, {'source': code, 'language': str(lang)})
            path = str(submitRes.url).split('/')
            return int(path[len(path)-1])
        except ClientError:
            raise InvalidDMOJSessionException

    async def getTestcaseStatus(self, id):
        try:
            req = await self.getAuthRequest(self.BASE_URL + '/widgets/single_submission?id=' + str(id))
        except ClientError:
            raise InvalidDMOJSessionException
        soup = bs.BeautifulSoup(req, 'lxml')
        status = soup.find_all('span', attrs={'class' : 'status'})[0].contents[0]
        time = soup.find_all('div',  attrs={'class' : 'time'})[-1].contents[0].strip()
        memory = soup.find_all('div',  attrs={'class' : 'memory'})[0].contents[0]
        done = status not in self.gradingStatuses

        if memory == '---':
            memory = None
        if time == '---':
            time = None

        problemName = soup.find_all('div',  attrs={'class' : 'name'})[0].find('a').contents[0]

        try:
            req = await self.getAuthRequest(self.BASE_URL + '/widgets/submission_testcases?id=' + str(id))
        except ClientError:
            raise InvalidDMOJSessionException
        soup = bs.BeautifulSoup(req, 'lxml')
        raw_result = soup.find('body').contents[0]

        cases = []

        try:
            caseTable = soup.find_all('table', attrs={'class': 'submissions-status-table'})[0]
        except IndexError:
            return Result(cases, raw_result, status, problemName, time, memory, done)

        for row in caseTable.find_all('tr'):
            testcase = Testcase()
            try:
                testcase.id = int(row.get('id'))
            except ValueError:
                continue
            children = row.find_all('td')
            testcase.descriptor = children[0].find('b').contents[0]
            testcase.status = children[1].find('span').contents[0]
            testcase.details = {
                'time': children[2].find('span').contents[0].replace(',', ''),
                'memory': children[3].contents[0].replace('\xa0', ' ').replace(']', ''),
                'points': children[4].contents[0]
            }
            cases.append(testcase)            

        return Result(cases, raw_result, status, problemName, time, memory, done)        
