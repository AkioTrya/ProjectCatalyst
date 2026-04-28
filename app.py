from flask import Flask
from database.db import init_db

app = Flask(__name__)

@app.route('/')
def index():
    return 'projectCatalyst is running!'

if __name__ == '__main__':
    init_db()
    app.run(debug=True)