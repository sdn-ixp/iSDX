from pymongo import MongoClient

import globs

client = MongoClient(globs.MONGODB_HOST, globs.MONGODB_PORT)
client.drop_database('demo')
