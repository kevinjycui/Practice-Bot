import aiohttp
import asyncio
import random


class WebSession:
    session = aiohttp.ClientSession()
    session_bak = aiohttp.ClientSession()

    async def webget_text(self, url, headers={}):
        headers['User-Agent'] = 'Mozilla/5.0'
        async with random.choice((self.session_bak, self.session)).get(url, headers=headers) as resp:
            return await resp.text()

    async def webget_json(self, url, headers={}):
        async with random.choice((self.session_bak, self.session)).get(url, headers=headers) as resp:
            return await resp.json(content_type=None)

    async def webpost(self, url, data={}, headers={}):
        async with random.choice((self.session_bak, self.session)).post(url, data=data, headers=headers) as resp:
            return resp

    async def webpost_text(self, url, data={}, headers={}):
        async with random.choice((self.session_bak, self.session)).post(url, data=data, headers=headers) as resp:
            return await resp.text()

    async def webpost_json(self, url, json={}, headers={}):
        async with random.choice((self.session_bak, self.session)).post(url, json=json, headers=headers) as resp:
            return await resp.json(content_type=None)

webc = WebSession()
