from sqlalchemy import Column, String, Integer, Table, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from flask_login import UserMixin
from utils import generate_random_color
Schema = declarative_base()


class User(UserMixin, Schema):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    hashed_password = Column(String)
    color = Column(String,default=generate_random_color())