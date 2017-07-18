import unittest
from pymongo import DESCENDING
from config import config, db, client
from updatedb import RedditFetch


class FetchTestCase(unittest.TestCase):
    SUBREDDIT = 'bitcoin'

    def setUp(self):
        self.fetch = RedditFetch(db=db,
            client_id=config['reddit']['client_id'],
            client_secret=config['reddit']['client_secret'],
            user_agent=config['reddit']['user_agent'])

    def tearDown(self):
        # daca subredditul testat nu se afla in config
        # as putea sterge toate datele de pe acela

        client.close()

    def _get_last_item(self):
        c_last_item = db.items.find({
            'subreddit': self.SUBREDDIT,
            'type': RedditFetch.TYPE_LINK
        }).sort('created', DESCENDING)
        if c_last_item.count() > 0:
            last_item = c_last_item[0]
        else:
            last_item = None

        return last_item

    def test_fetch(self):
        # test get items for a random sub
        last_item = self._get_last_item()
        last_id = last_item['_id'] if last_item else None
        limit = 5
        submissions_count = self.fetch.fetch_subreddit(self.SUBREDDIT, limit)
        assert limit >= submissions_count

        q = {
            'subreddit': self.SUBREDDIT,
            'type': RedditFetch.TYPE_LINK
        }
        if last_id is not None:
            q['_id'] = {'$gt': last_id}

        db_count = db.items.find(q).count()
        assert submissions_count <= db_count

        # test get comments
        last_reddit_id = self._get_last_item()['id']
        limit = 5
        comments_count = self.fetch.fetch_comments(last_reddit_id, self.SUBREDDIT, limit)
        assert limit >= comments_count

        db_count = db.items.find({
            'subreddit': self.SUBREDDIT,
            'type': RedditFetch.TYPE_COMMENT,
        })
        assert comments_count <= db_count


if __name__ == '__main__':
    unittest.main()
