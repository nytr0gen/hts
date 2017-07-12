import praw
import pymongo
from time import sleep
from config import config, db


# TODO should handle timezone
class RedditFetch:
    TYPE_COMMENT = 1
    TYPE_LINK = 3

    def __init__(self, db, client_id, client_secret, user_agent):
        self._db = db
        self._reddit = praw.Reddit(client_id=client_id,
                                   client_secret=client_secret,
                                   user_agent=user_agent)

    def run(self, subreddits):
        for subreddit in subreddits:
            self._fetch_subreddit(subreddit)

    # hardcoded limit
    def _fetch_subreddit(self, subreddit, limit=1024):
        # get last id from db
        c_items = db.items.find({'subreddit': subreddit}).sort('-id')

        params = None
        if c_items.count() > 0:
            last_item = c_items[0]
            params = {
                # t3 is for link
                # https://www.reddit.com/dev/api/ -- type prefixes
                'before': 't3_' + last_item['id']
            }

        # before last t3_id from db
        submissions_list = self._reddit.subreddit(subreddit).new(params=params,
                                                                 limit=limit)

        submissions_count = 0
        for submission in submissions_list:
            # exista mai multe cai sa fac id-ul de mongo
            # 1. pot sa folosesc created_at din submission pentru bson object id
            # astfel incat pot sorta desc dupa _id din mongo
            # 2. pot folosi id-ul de reddit intr-un int. aparent ultimele posturi
            # ajung pe la 400,854,437 ('6mnp9h'), ceea ce e mai mic ca un int32
            # https://stackoverflow.com/questions/1181919/python-base-36-encoding
            # a doua solutie e mai viabila deoarece e usor sa evit si duplicatele cu ea

            # 'downs': 0,
            # 'hide_score': True,
            # 'likes': None,
            # 'num_comments': 0,
            # 'score': 1,
            # 'thumbnail': u'',
            # 'ups': 1,
            # 'url': u'http://www.castlebayhouse.com/cplusplus.html',

            # author may have deleted his account or just deleted his
            # connection to this post
            author_name = submission.author.name if submission.author is not None else None
            db_sub = {
                '_id': int(submission.id, 36) << 1, # avoid duplicates
                'id': submission.id, # keep base36 for convenience
                'author': author_name,
                'created': int(submission.created),
                'created_utc': int(submission.created_utc),
                'over_18': submission.over_18,
                'permalink': submission.permalink,
                'title': submission.title, # teoretic pot scapa de title deoarece deja pastrez tipul
                'text': submission.title, # duplicate for convenience for keyword search
                'num_comments': submission.num_comments,
                'subreddit': subreddit,
                'type': self.TYPE_LINK
            }

            try:
                db.items.insert_one(db_sub)
                if submission.num_comments > 0:
                    self._fetch_comments(submission.id, subreddit)
            except pymongo.errors.DuplicateKeyError as e:
                # todo: pastreaza num_comments si trage comments doar daca
                # numarul primit e mai mare decat cel din baza de date
                pass
            
            submissions_count += 1

        print('Got %d new submissions from %s' % (submissions_count, subreddit))

    def _fetch_comments(self, submission_id, subreddit):
        # get last comment from db
        # get all comments before last_comment_id
        # insert comments in db

        # 'body_html': u'<div class="md"><p>SQLAlchemy</p>\n</div>',
        # 'can_gild': True,
        # 'depth':0,
        # 'edited': False,
        # 'link_id': u't3_6mnp9h',
        # 'name': u't1_dk2xa1h',
        # 'parent_id': u't3_6mnp9h',
        # 'score': 3,
        # 'stickied': False,

        submission = self._reddit.submission(id=submission_id)
        submission.comments.replace_more(limit=0)
        # only get top level comments
        for comment in submission.comments:
            author_name = submission.author.name if submission.author is not None else None            
            db_comm = {
                '_id': int(comment.id, 36) << 1 | 1, # avoid duplicates
                'id': comment.id, # keep base36 id for convenience
                'author': author_name,
                'text': comment.body,
                'created': int(comment.created),
                'created_utc': int(comment.created_utc),
                'depth': comment.depth,
                'subreddit': subreddit,
                'type': self.TYPE_COMMENT, 
            }

            try:
                db.items.insert_one(db_comm)
            except pymongo.errors.DuplicateKeyError as e:
                # exista posibilitatea ca acest comment sa fie editat. in acest
                # caz ar trebui un update
                pass


def main():
    rf = RedditFetch(db=db,
        client_id=config['reddit']['client_id'],
        client_secret=config['reddit']['client_secret'],
        user_agent=config['reddit']['user_agent'])

    while True:
        rf.run(config['reddit']['subreddits'])
        sleep(10 * 60) # 10min


if __name__ == '__main__':
    main()
