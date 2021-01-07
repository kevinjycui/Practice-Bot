# import aiohttp
# import asyncio
import requests


class WebSession:
    # session = aiohttp.ClientSession()

    async def webget_text(self, url, headers={}):
        return requests.get(url, headers=headers).text
        # async with self.session.get(url, headers=headers) as resp:
        #     return await resp.text()

    async def webget_json(self, url, headers={}):
        return requests.get(url, headers=headers).json()
        # async with self.session.get(url, headers=headers) as resp:
        #     return await resp.json(content_type=None)

    async def webpost(self, url, data={}, headers={}):
        return requests.post(url, data=data, headers=headers, allow_redirects=True)
        # async with self.session.post(url, data=data, headers=headers) as resp:
        #     return resp

    async def webpost_text(self, url, data={}, headers={}):
        return requests.post(url, data=data, headers=headers, allow_redirects=True).text
        # async with self.session.post(url, data=data, headers=headers) as resp:
        #     return await resp.text()

    async def webpost_json(self, url, json={}, headers={}):
        return requests.post(url, json=json, headers=headers, allow_redirects=True).json()
        # async with self.session.post(url, json=json, headers=headers) as resp:
        #     return await resp.json(content_type=None)

webc = WebSession()
