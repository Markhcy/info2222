'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, redirect, flash, jsonify,session
from flask_socketio import SocketIO
import db
import secrets
from jinja2 import utils
import cherrypy
from models import User, Friends, FriendshipStatus
from hashlib import sha256

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

@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")
    hashedPassword = (sha256(password.encode('utf-8')).hexdigest())


    user =  db.get_user(username)
    if user is None:
        return "Error: User does not exist!"

    if user.password != hashedPassword:
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

    # SHA256 hashing of password on server-side
    hashedPassword = (sha256(password.encode('utf-8')).hexdigest())


    if db.get_user(username) is None:
        db.insert_user(username, hashedPassword)
        return url_for('login', username=username)
    return "Error: User already exists!"

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404


user_list = db.get_all_user()
# Home page (friends_list page), the initial landing page after logging in.
@app.route("/home", methods=['GET', 'POST'])
def home():
    username = request.args.get("username")
    if not username:
        flash("Username is required to view friends.")
        return redirect(url_for('login'))

    user_list = db.get_all_user()
    friends_list = db.get_friends_list(username)
    return render_template("friends.jinja", username=username, users=user_list, friends_list=friends_list)


# Room page when a user wants to chat with a friend
@app.route("/room", methods=['GET', 'POST'])
def room():
    username = request.args.get("username")
    return render_template("room.jinja", username=username)

@app.route('/home/fetch_friend_requests', methods=['GET'])
def fetch_friend_requests():
    # username = session.get("username")

    username = request.args.get("username")
    # print(username)
    if not username:
        return jsonify({"error": "You must be logged in to view friend requests"}), 401

    friend_requests = db.get_received_friend_requests(username)
    requests_data = [{'fromUser': req.person1, 'id': req.connection_id} for req in friend_requests]
    
    return jsonify({"requests": requests_data}), 200


@app.route('/home/send_fr', methods=['POST'])
def send_friend_request():
    if not request.is_json:
        return jsonify({"message": "Invalid request"}), 400

    data = request.get_json()
    sender_username = data.get('sender')
    receiver_username = data.get('receiver')

    if not all([sender_username, receiver_username]):
        return jsonify({"message": "Missing data"}), 400

    try:
        if are_already_friends_or_pending(sender_username, receiver_username):
            return jsonify({"message": "Already friends or request pending"}), 409
        # print(sender_username, receiver_username)
        success = db.add_friend_request(sender_username, receiver_username)
        if success:
            return jsonify({"message": "Friend request sent"}), 200
        else:
            return jsonify({"message": "Receiver does not exist"}), 404  
    except Exception as e:
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500


@app.route('/accept-friend-request/<int:request_id>', methods=['POST'])
def accept_friend_request(request_id):
    if db.accept_friend_request(request_id):
        return jsonify({"message": "Friend request accepted"}), 200
    else:
        return jsonify({"message": "Could not accept friend request"}), 500


@app.route('/reject-friend-request/<int:request_id>', methods=['POST'])
def reject_friend_request(request_id):
    if db.reject_friend_request(request_id):
        return jsonify({"message": "Friend request rejected"}), 200
    else:
        return jsonify({"message": "Could not reject friend request"}), 500



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
