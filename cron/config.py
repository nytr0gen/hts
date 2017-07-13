import os
import json
from pymongo import MongoClient, DESCENDING, TEXT, HASHED

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config_filepath = os.path.join(BASE_DIR, 'config.json')
with open(config_filepath) as f:
    config = json.load(f)

# maybe flask_pymongo
client = MongoClient(config['mongo']['url'])
db = client[config['mongo']['db']]

db.items.create_index([('created', DESCENDING)])
db.items.create_index([('subreddit', HASHED)])
db.items.create_index([('text', TEXT)], background=True)
