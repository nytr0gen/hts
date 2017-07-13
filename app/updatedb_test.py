import unittest
from config import config, db, client
from updatedb import RedditFetch


class FetchTestCase(unittest.TestCase):
    def setUp(self):
        self.fetch = RedditFetch(db=db,
            client_id=config['reddit']['client_id'],
            client_secret=config['reddit']['client_secret'],
            user_agent=config['reddit']['user_agent'])

    def tearDown(self):
        client.close()

    # test get items for a random sub
    # test get comments

if __name__ == '__main__':
    unittest.main()
