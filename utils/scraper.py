import urllib
import requests
import bs4 as bs
from bs4.element import Comment

def valid(url):
    try:
        if urllib.request.urlopen(url).getcode() == 200:
            return True
        else:
            return False
    except:
        return False

def accountScrape(name):
    accounts = {}
    if valid('https://dmoj.ca/api/user/info/%s' % name):
        accounts['DMOJ'] = 'https://dmoj.ca/user/%s' % name
    cf_data = requests.get('https://codeforces.com/api/user.info?handles=%s' % name)
    if cf_data.status_code == 200 and cf_data.json()['status'] == 'OK':
        accounts['Codeforces'] = 'https://codeforces.com/profile/%s' % name
    if valid('https://atcoder.jp/users/%s' % name):
        accounts['AtCoder'] = 'https://atcoder.jp/users/%s' % name
    if valid('https://wcipeg.com/user/%s' % name):
        accounts['WCIPEG'] = 'https://wcipeg.com/user/%s' % name
    if valid('https://github.com/%s' % name):
        accounts['GitHub'] = 'https://github.com/%s' % name
    return accounts

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def wcipegScrape(name):
    if valid('http://wcipeg.com/wiki/%s' % name.replace(' ', '_')):
        try:
            url = 'http://wcipeg.com/wiki/%s' % name.replace(' ', '_')
            wiki_response = requests.get(url).text
            soup = bs.BeautifulSoup(wiki_response, 'lxml')
            scan = True
            title = soup.find('h1', attrs={'id': 'firstHeading'}).contents[0]
            texts = soup.find('div', attrs={'id': 'mw-content-text'}).find('p').findAll(text=True)
            visible_texts = filter(tag_visible, texts)  
            summary = ' '.join(t.strip() for t in visible_texts)
            return title, summary, url
        except:
            return None