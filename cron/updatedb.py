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
            submissions_count = self.fetch_subreddit(subreddit)
            print('Got %d new submissions from %s' % (submissions_count, subreddit))

    # hardcoded limit
    def fetch_subreddit(self, subreddit, limit=1024):
        submissions_list = self._reddit.subreddit(subreddit).new(limit=limit)

        submissions_count = 0
        for submission in submissions_list:
            # exista mai multe cai sa fac id-ul de mongo
            # 1. pot sa folosesc created_at din submission pentru bson object id
            # astfel incat pot sorta desc dupa _id din mongo
            # 2. pot folosi id-ul de reddit intr-un int. aparent ultimele posturi
            # ajung pe la 400,854,437 ('6mnp9h'), ceea ce e mai mic ca un int32
            # https://stackoverflow.com/questions/1181919/python-base-36-encoding
            # a doua solutie e mai viabila deoarece e usor sa evit si duplicatele cu ea

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
                    self.fetch_comments(submission.id, subreddit)
            except pymongo.errors.DuplicateKeyError as e:
                # todo: pastreaza num_comments si trage comments doar daca
                # numarul primit e mai mare decat cel din baza de date

                # in principiu daca repet un id inseamna ca toate informatiile
                # de dupa acesta le am deja in baza de date. submission_list e
                # un iterator deci va fi ok sa dau break.
                # am incercat cu parametrul 'before' de la reddit, dar nu functioneaza predictibil.
                break

            submissions_count += 1

        return submissions_count

    def fetch_comments(self, submission_id, subreddit):
        submission = self._reddit.submission(id=submission_id)
        submission.comments.replace_more(limit=0)
        # only get top level comments
        comments_count = 0
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
            
            comments_count += 1

        return comments_count


def main():
    rf = RedditFetch(db=db,
        client_id=config['reddit']['client_id'],
        client_secret=config['reddit']['client_secret'],
        user_agent=config['reddit']['user_agent'])

    print("Starting Update Db Cron")
    while True:
        rf.run(config['reddit']['subreddits'])
        sleep(10 * 60) # 10min


if __name__ == '__main__':
    main()
