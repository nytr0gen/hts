import os
import json
from pymongo import MongoClient

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open('config.json') as f:
    config = json.load(f)

client = MongoClient(config['mongo_url'])
db = client[config['mongo_db']]
