from functools import wraps

import pymongo
from flask import Flask, render_template, session, redirect
from flask_cors import CORS
from user.models import User, login_user

# default
app = Flask(__name__)
CORS(app)
app.secret_key = b'2t#!\xfe\x96\xe1\xd9\xaa&\xe1\x15\xc2\x10\xad@'  # random secret key obtained using terminal

# Database
client = pymongo.MongoClient('mongodb://commetuveux:ouiouioui@ws-01.milebits.com', 27017)
db = client.users


# Decorators
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/')

    return wrap


# Routes
@app.route('/user/')
def user():
    return render_template("index.html")


@app.route('/')
def home():
    return render_template("Accueil.html")


@app.route('/dashboard-admin/')
@login_required
def dashboard():
    return render_template("admin_components.html")


@app.route('/dashboard/')
@login_required
def new_dashboard():
    user = session["user_login"]
    if bool(user['administrator']):
        return render_template("admin_components.html")
    return render_template("dashboard2.html")


@app.route('/current-token/')
# @login_required
def get_current_token():
    return {'status': 'success', 'token': login_user().current_token()}


@app.route('/user/signup', methods=['POST'])  # must be POST
def process_signup():
    return User().signup


@app.route('/user/login', methods=['POST'])
def process_login():
    return login_user().login


@app.route('/signout')
def signout():
    return login_user().signout()


# flask running
if __name__ == '__main__':
    app.run(host='localhost', debug=True)
