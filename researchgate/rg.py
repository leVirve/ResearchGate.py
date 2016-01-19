import os
import time
import asyncio
import logging

import aiohttp

from rgparse import parse_info, parse_publications
from utils import ProgressBar


program = 'researchgate_logger'
MEMBER_LIST = 'member-list'
logger = logging.getLogger(program)
logger.setLevel(logging.DEBUG)
logging.basicConfig(filename='crawler.log', level=logging.INFO)


def chunked_http_client(num_chunks):
    semaphore = asyncio.Semaphore(num_chunks)

    @asyncio.coroutine
    def http_get(url):
        nonlocal semaphore
        with (yield from semaphore):
            response = yield from aiohttp.get(url)
            body = yield from response.text()
            yield from response.wait_for_close()
        return body
    return http_get


class Profile:

    PROFILE_FORMAT = 'http://www.researchgate.net/profile/%s'
    PUBLICATION_URL = '%s/publications' % PROFILE_FORMAT
    INFO_URL = '%s/info' % PROFILE_FORMAT

    def __init__(self, user_id, session):
        self.user_id = user_id
        self.session = session
        self._profile = {'name': user_id}

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


def all_members_of(name='National_Tsing_Hua_University'):
    urls = ['https://www.researchgate.net/institution/{}/members/{}'
            .format(name, i) for i in range(1, 18)]

    http_client = chunked_http_client(200)
    tasks = [http_client(url) for url in urls]

    def parse(resp):
        soup = BeautifulSoup(resp, 'lxml')
        return [
            a.get('href').split('/')[-1]
            for a in soup.select('.list li a.display-name')]

    members = []
    for future in asyncio.as_completed(tasks):
        data = yield from future
        members += parse(data)
    return members


def save_member_list():
    s = time.time()
    with open(MEMBER_LIST, 'w') as f:
        loop = asyncio.get_event_loop()
        members = loop.run_until_complete(all_members_of())
        f.write('\n'.join(members))
    logger.info('End in {:.9f} sec'.format(time.time() - s))


async def save_profiles(names):
    conn = aiohttp.TCPConnector(limit=50, verify_ssl=False)
    with aiohttp.ClientSession(connector=conn) as session:
        ps = [Profile(name, session) for name in names]
        futures = [asyncio.ensure_future(p.get_info()) for p in ps]
        futures += [asyncio.ensure_future(p.get_publications()) for p in ps]

        progress, step = ProgressBar(), 10
        progress.max = len(futures) // step

        for i, future in enumerate(asyncio.as_completed(futures), 1):
            if i % step == 0:
                progress.next()
            await future
        progress.finish()

    return [future.result() for future in futures]


if __name__ == '__main__':

    if os.path.exists(MEMBER_LIST) is False:
        print('Get member list...')
        save_member_list()

    names = []
    with open(MEMBER_LIST, 'r') as f:
        for name in f.readlines():
            names.append(name.strip())

    logger.info('-----({} users)-----'.format(len(names)))
    logger.info('Start crawling....')
    s = time.time()

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(save_profiles(names))
    loop.close()

    logger.info('End in {:.9f} sec'.format(time.time() - s))
