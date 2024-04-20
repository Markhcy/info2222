'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Base, User, Friends, FriendshipStatus,EncryptedMessage
from sqlalchemy.exc import SQLAlchemyError

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
def insert_user(username: str, password: str, salt:str):
    with Session(engine) as session:
        user = User(username=username, password=password, salt=salt)
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


def add_friend_request(sender_username: str, receiver_username: str):
    try:
        with Session(engine) as session:
            receiver = session.get(User, receiver_username)
            # print(receiver)
            if receiver:
                new_request = Friends(person1=sender_username, person2=receiver_username, status=FriendshipStatus.PENDING)
                session.add(new_request)
                session.commit()
                return True
            else:
                return False
    except SQLAlchemyError as e:
        print(f"Database error: {e}")  
        return False  


def get_received_friend_requests(username: str):
    with Session(engine) as session:
        return session.query(Friends).filter_by(person2=username, status=FriendshipStatus.PENDING).all()


def accept_friend_request(request_id: int):
    with Session(engine) as session:
        request = session.get(Friends, request_id)
        if request and request.status == FriendshipStatus.PENDING:
            request.status = FriendshipStatus.ACCEPTED
            session.commit()
            return True
        return False


def reject_friend_request(request_id: int):
    with Session(engine) as session:
        request = session.get(Friends, request_id)
        if request and request.status == FriendshipStatus.PENDING:
            request.status = FriendshipStatus.REJECTED
            session.commit()
            return True
        return False


def get_friends_list(username: str):
    with Session(engine) as session:
        friends = session.query(Friends).filter(
            ((Friends.person1 == username) | (Friends.person2 == username)),
            Friends.status == FriendshipStatus.ACCEPTED
        ).all()

        friend_usernames = []
        for friend in friends:
            if friend.person1 == username:
                friend_usernames.append(friend.person2)
            else:
                friend_usernames.append(friend.person1)

        return friend_usernames
    
def insert_encrypted_message(sender_username: str, receiver_username: str, encrypted_text: bytes, tag: str, salt: str):
    try:
        with Session(engine) as session:
            encrypted_message = EncryptedMessage(
                sender_username=sender_username,
                receiver_username=receiver_username,
                encrypted_text=encrypted_text,
                encryption_tag=tag,
                encryption_salt=salt
            )
            session.add(encrypted_message)
            session.commit()
            return True
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        return False

def get_encrypted_messages(username: str):
    with Session(engine) as session:
        # Retrieves messages sent by the user
        sent_messages = session.query(EncryptedMessage).filter_by(sender_username=username).all()
        # Retrieves messages received by the user
        received_messages = session.query(EncryptedMessage).filter_by(receiver_username=username).all()
        return sent_messages, received_messages
