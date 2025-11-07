from sqlalchemy import Column, String, Integer, Table, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Schema = declarative_base()


class User_name(Schema):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    hashed_password = Column(String)