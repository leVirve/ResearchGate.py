import asyncio
import logging

import aiohttp

from rgparse import parse_info, parse_publications

program = 'researchgate_logger'
logger = logging.getLogger(program)


class Profile:

    PROFILE_FORMAT = 'http://www.researchgate.net/profile/%s'
    PUBLICATION_URL = '%s/publications' % PROFILE_FORMAT
    INFO_URL = '%s/info' % PROFILE_FORMAT

    def __init__(self, user_id, session):
        self.user_id = user_id
        self.session = session

    async def get(self, url):
        try:
            async with self.session.get(url) as r:
                body = await r.text()
            return body
        except:
            logger.info('{} fails'.format(url))

    async def get_info(self):
        body = await self.get(self.INFO_URL % self.user_id)
        if body is None:
            return
        parse_info.delay(self.user_id, body)
        return '{} info'.format(self.user_id)

    async def get_publications(self):
        body = await self.get(self.PUBLICATION_URL % self.user_id)
        if body is None:
            return
        parse_publications.delay(self.user_id, body)
        return '{} publications'.format(self.user_id)
