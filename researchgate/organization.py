import asyncio
import aiohttp

from rgparse import parse_member_list


MEMBER_LIST = 'member-list'


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


def get_members(name):
    urls = ['https://www.researchgate.net/institution/{}/members/{}'
            .format(name, i) for i in range(1, 18)]

    http_client = chunked_http_client(200)
    tasks = [http_client(url) for url in urls]

    members = []
    for future in asyncio.as_completed(tasks):
        data = yield from future
        members += parse_member_list(data)
    return members
