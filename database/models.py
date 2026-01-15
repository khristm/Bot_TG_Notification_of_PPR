from sqlalchemy import Column, Integer, ForeignKey, String
from database.database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, unique=True, autoincrement=True,primary_key=True)
    phone_number= Column(String, unique=True)
    tg_id=Column(String, unique=True)
    chat_id=Column(String)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, unique=True, autoincrement=True,primary_key=True)
    user_id= Column(Integer, ForeignKey('users.id'))
    adress=Column(String)
    month=Column(String)
    date_time=Column(String)
    number=Column(Integer)
    workers=Column(String)
    type=Column(String)