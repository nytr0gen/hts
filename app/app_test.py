import unittest
from bson.json_util import loads
from app import app
from config import config, client, db


class AppTestCase(unittest.TestCase):
    DEFAULT_SUB = 'test_sub'
    DEFAULT_ITEM = {
        'subreddit': DEFAULT_SUB,
        'testonly': True,
    }

    def setUp(self):
        app.testing = True
        self.app = app.test_client()

        self.items = []
        for i in range(10):
            item = self.DEFAULT_ITEM.copy()
            item.update({
                'id': str(i),
                'created': i,
                'text': 'test test_%d' % i
            })

            self.items.append(item)

        db.items.insert_many(self.items)

    def tearDown(self):
        # delete test data by testonly: True
        db.items.remove({'testonly': True})

        client.close()

    def test_empty_home(self):
        rv = self.app.get('/')
        assert 404 == rv.status_code

    # TODO some more tests for invalid query params
    def test_listing(self):
        path = '/items/?subreddit=%s&from=%%d&to=%%d' % self.DEFAULT_SUB
        
        rv = self.app.get(path % (self.items[0]['created'], self.items[-1]['created']))
        assert 200 == rv.status_code
        data = loads(rv.data)
        assert len(self.items) == len(data)
        assert self.items[-1]['_id'] == data[0]['_id'] # reverse cronological order
        
        # get between dates
        rv = self.app.get(path % (self.items[0]['created'], self.items[3]['created']))
        assert 200 == rv.status_code
        data = loads(rv.data)
        assert 4 == len(data)

        # not found range
        rv = self.app.get(path % (self.items[-1]['created'] + 10, self.items[-1]['created'] + 20))
        assert 404 == rv.status_code

    def test_keyword(self):
        path = '/items/?subreddit=%s&from=%d&to=%d&keyword=%%s' % (
            self.DEFAULT_SUB, 
            self.items[0]['created'], 
            self.items[-1]['created'])

        # keyword test
        rv = self.app.get(path % 'test')
        assert 200 == rv.status_code
        data = loads(rv.data)
        assert len(self.items) == len(data)

        # keyword test1
        rv = self.app.get(path % 'test_1')
        assert 200 == rv.status_code
        data = loads(rv.data)
        assert 1 == len(data)

        # keyword not found
        rv = self.app.get(path % 'test_11')
        assert 404 == rv.status_code

if __name__ == '__main__':
    unittest.main()
