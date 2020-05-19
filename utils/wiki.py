import urllib, wikipedia

def getSummary(name):
    try:
        if urllib.request.urlopen('https://en.wikipedia.org/wiki/'+name).getcode() != 404:
            return wikipedia.page(name), wikipedia.summary(name, sentences=5)
    except wikipedia.DisambiguationError as e:
        if len(e.options) > 0:
            return getSummary(e.options[0].replace(' ', '_'))
        else:
            return None, None
    except:
        return None, None