'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, redirect, flash
from flask_socketio import SocketIO
import db
import secrets
import cherrypy

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
    return render_template("friends.jinja")

# handles a post request when the user clicks the log in button
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
    username = request.json.get("username")
    password = request.json.get("password")

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
friends_list = db.get_friends_list()

@app.route("/home", methods=['GET', 'POST'])
def home():
    username = request.args.get("username")
    if request.method == 'POST':
        friend_name = request.form["enter_value"]
        if search_friend(friend_name):
            #check if they are already friends
            for connections in friends_list:
                friend1 = connections.person1
                friend2 = connections.person2
                if friend1 == username and friend2 == friend_name or friend2 == username and friend1 == friend_name:
                    flash("Error: you are already friends!")
                    return redirect(url_for('home', username=username))
                else:
                    db.add_friend(username, friend_name)
        else:
            flash("Error: friend does not exist!")
            return redirect(url_for('home', username=username))

    if request.args.get("username") is None:
        abort(404)
    return render_template("friends.jinja", username=request.args.get("username"), users=get_friend(username))


def search_friend(friend):
    for i in user_list:
        user = i.username
        if friend == user:
            return True
    return False

def get_friend(user):
    list_of_friends = []
    for connections in friends_list:
        if user == connections.person1:
            list_of_friends.append(connections.person2)
    print(list_of_friends)
    return list_of_friends

if __name__ == '__main__':
    socketio.run(app)
    # cherrypy.quickstart(app)
