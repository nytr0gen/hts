from flask import Flask, request, jsonify
from config import db, config
app = Flask(__name__)

# main flask api route
# /items/?subreddit=<subreddit>&from=<t1>&to=<t2>
# /items/?subreddit=<subreddit>&from=<t1>&to=<t2>&keyword=<kw>
@app.route('/items/')
def items():
    subreddit = request.args.get('subreddit')
    q_from = request.args.get('from')
    q_to = request.args.get('to')
    if (subreddit is None or len(subreddit) == 0 or
        q_from is None or q_to is None):
        data = dict(error='Invalid query')
        return jsonify(data), 400

    try:
        q_from = int(q_from)
        q_to = int(q_to)
    except ValueError:
        data = dict(error='Invalid from or to in query')
        return jsonify(data), 400

    # query filter by subreddit, q_from, q_to
    query = {
        'subreddit': subreddit,
        'created': { # am presupus [from, to]
            '$gte': q_from,
            '$lte': q_to,
        }
    }

    # add keyword to query filter
    keyword = request.args.get('keyword') # optional
    if keyword is not None:
        query['$text'] = { '$search': keyword }

    # reverse order
    c_items = db.items.find(query).sort('created', -1)

    # subreddit not found
    if c_items.count() == 0:
        data = dict(error='Query Not Found')
        return jsonify(data), 404

    '''
    Data returned by the web server should be in JSON format, sorted in reverse chronological order.
    For simplicity, all parameters are mandatory, the server should respond with an error if they're missing.
    '''

    # TODO de facut paginare
    return jsonify(list(c_items))


if __name__ == '__main__':
    app.run(debug=config['debug'])
