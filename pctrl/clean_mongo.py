import os
from StringIO import StringIO
import globs
from pymongo import MongoClient

client = MongoClient(globs.MONGODB_HOST, globs.MONGODB_PORT)
client.drop_database('demo')
