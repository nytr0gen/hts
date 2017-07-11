from flask import Flask
from config import config, db
app = Flask(__name__)


@app.route('/')
def hello():
    print(db)
    print(db.test)
    o = db.test.find_one()
    print(o)
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=config['debug'])
