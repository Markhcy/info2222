'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, redirect, flash
from flask_socketio import SocketIO
import db
import secrets
from jinja2 import utils
import cherrypy
from models import User, Friends, FriendshipStatus

import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)



app = Flask(__name__)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes


# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

@app.route("/friends")
def friends():
    username = request.args.get("username")
    if not username:
        flash("Username is required to view friends.")
        return redirect(url_for('login'))
    
    raw_friends_list = db.get_friends_list(username)
    friends_list = [friend for friend in raw_friends_list if friend] 
    return render_template("friends.jinja", friends_list=friends_list, username=username)


@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")

    user =  db.get_user(username)
    if user is None:
        return "Error: User does not exist!"

    if user.password != password:
        return "Error: Password does not match!"

    return url_for('home', username=request.json.get("username"))

# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)
    # XSS prevention by sanitising on server-side using built-in Jinja function
    username = request.json.get("username")
    password = request.json.get("password")
    username = xss_prevention(username)
    password = xss_prevention(password)

    print(username)

    if db.get_user(username) is None:
        db.insert_user(username, password)
        return url_for('home', username=username)
    return "Error: User already exists!"

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# friends page, the initial landing page after logging in.
user_list = db.get_all_user()

@app.route("/home", methods=['GET', 'POST'])
def home():
    username = request.args.get("username")
    if not username:
        abort(404)
    
    user_list = db.get_all_user()
    friends_list = db.get_friends_list(username)

    if request.method == 'POST':
        friend_name = request.form.get("enter_value")
        if db.get_user(friend_name):
            if not db.are_already_friends_or_pending(username, friend_name):
                db.add_friend_request(username, friend_name)
                flash("Friend request sent!")
            else:
                flash("You are already friends or a friend request is pending.")
        else:
            flash("Friend does not exist!")

    return render_template("friends.jinja", username=username, users=user_list, friends=friends_list)

def are_already_friends_or_pending(user1, user2):
    existing = db.get_received_friend_requests(user2)
    for request in existing:
        if (request.person1 == user1 or request.person2 == user1) and \
           (request.status == FriendshipStatus.PENDING or request.status == FriendshipStatus.ACCEPTED):
            return True
    return False

def search_friend(friend):
    user_list = db.get_all_user()  # Update to fetch user list dynamically
    for i in user_list:
        if friend == i.username:
            return True
    return False

def get_friend(user):
    friends_list = db.get_friends_list(user)  # Update to fetch friend list dynamically
    list_of_friends = []
    for connection in friends_list:
        list_of_friends.append(connection)
    return list_of_friends

def xss_prevention(string):
    bad_chars = '$*+.-/"<>'
    for char in bad_chars:
        string = string.replace(char, "")
    return string

if __name__ == '__main__':
    socketio.run(app)

