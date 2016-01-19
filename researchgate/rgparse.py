import os

from bs4 import BeautifulSoup
from celery import Celery
from pymongo import MongoClient


uri = 'mongodb://{}:27017'.format(os.environ.get('IP'))

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'


app = Celery('tasks', broker=BROKER_URL, backend=CELERY_RESULT_BACKEND)
client = MongoClient(uri)

db = client['rg']
info = db['info']
pubs = db['pubs']


@app.task
def parse_info(user_id, body):

    soup = BeautifulSoup(body, 'lxml')
    kws = soup.select('.keyword-list-container a.keyword-list-token-text')
    exps = soup.select('.profile-experience-list li')

    info.insert_one({
        'name': user_id,
        'topics': [kw.text.strip() for kw in kws],
        'experiences':  [
            '{position}, {school}'.format(
            **{'position': exp.find('h5').text,
              'school': exp.select_one('h5 + div').text}) for exp in exps
            ]
        })


@app.task
def parse_publications(user_id, body):

    soup = BeautifulSoup(body, 'lxml')
    for pub in soup.select('.profile-publications li'):
        tiltle_meta = pub.find('h5').find('a')
        authors_meta = pub.select_one('.authors')
        abstract_meta = pub.select_one('.abstract .full')
        pub_meta = pub.select_one('.publication-meta').text.split('·')
        i = len('[Hide abstract] ABSTRACT: ')
        abstract = abstract_meta.text.replace('\n', ' ').strip()[i:]

        pubs.insert_one({
            '_name': user_id,
            'title': tiltle_meta.text.strip(),
            'authors': [au.strip() for au in authors_meta.text.split('·')],
            'abstract': abstract,
            'info': pub_meta[0].strip(),
            'type': pub_meta[1].strip(),
            'time': pub_meta[2].strip(),
        })
