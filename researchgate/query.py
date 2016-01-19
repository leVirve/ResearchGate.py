import os
from pymongo import MongoClient

uri = 'mongodb://{}:27017'.format(os.environ.get('IP'))

client = MongoClient(uri)

db = client['rg']
info = db['info']
pubs = db['pubs']

print('In database are:')
print('\tinfo => %d' % info.count())
print('\tpubs => %d' % pubs.count())
