from sqlalchemy import Column, String, Integer, Table, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from flask_login import UserMixin

Schema = declarative_base()


class User(UserMixin, Schema):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    hashed_password = Column(String)