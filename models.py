'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from typing import Dict
from cryptography.hazmat.primitives.asymmetric import dh
import sympy
import random


Base = declarative_base()

class FriendshipStatus(enum.Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'

class User(Base):
    __tablename__ = "user"
    username = Column(String, primary_key=True)
    password = Column(String)
    salt = Column(String)
    sent_requests = relationship("Friends", foreign_keys="[Friends.person1]", back_populates="requester")
    received_requests = relationship("Friends", foreign_keys="[Friends.person2]", back_populates="receiver")

class Friends(Base):
    __tablename__ = 'friends'
    connection_id = Column(Integer, primary_key=True, autoincrement=True)
    person1 = Column(String, ForeignKey('user.username'))
    person2 = Column(String, ForeignKey('user.username'))
    status = Column(Enum(FriendshipStatus))

    requester = relationship("User", foreign_keys=[person1], back_populates="sent_requests")
    receiver = relationship("User", foreign_keys=[person2], back_populates="received_requests")



# stateful counter used to generate the room id
class Counter():
    def __init__(self):
        self.counter = 0
    
    def get(self):
        self.counter += 1
        return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        # dictionary that maps the username to the room id
        # for example self.dict["John"] -> gives you the room id of 
        # the room where John is in
        self.dict: Dict[str, int] = {}
        self.num_members = 0

    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        return room_id
    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id


    def leave_room(self, user):
        if user not in self.dict.keys():
            return
        del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]

    def get_num_members(self):
        return self.num_members
