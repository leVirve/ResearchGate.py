import os
import time
import asyncio
import logging

import aiohttp

from profile import Profile
from organization import get_members, MEMBER_LIST
from utils import ProgressBar


program = 'researchgate_logger'
logger = logging.getLogger(program)
logger.setLevel(logging.DEBUG)
logging.basicConfig(filename='crawler.log', level=logging.INFO)


def save_member_list(name):
    s = time.time()
    with open(MEMBER_LIST, 'w') as f:
        loop = asyncio.get_event_loop()
        members = loop.run_until_complete(get_members(name))
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
        save_member_list('National_Tsing_Hua_University')

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
