'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *

from pathlib import Path

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, password: str):
    with Session(engine) as session:
        user = User(username=username, password=password)
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)

def get_all_user():
    with Session(engine) as session:
        q = session.query(User)
        result = q.all()
        return result

def add_friend(user: str, friend: str):
    with Session(engine) as session:
        new_friend = Friends(person1=user, person2=friend)
        session.add(new_friend)
        session.commit()

def get_friends_list():
    with Session(engine) as session:
        q = session.query(Friends)
        result = q.all()
        return result