from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base
from flask_login import UserMixin
from utils import generate_random_color

Schema = declarative_base()


class User(UserMixin, Schema):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    color = Column(String, default=generate_random_color())
    kills = Column(Integer, default=0)
    games = Column(Integer, default=0)
    win_hunter = Column(Integer, default=0)
    win_survivor = Column(Integer, default=0)
