from sqlalchemy.orm import Session
from typing import Optional
import bcrypt

import pytz
from sqlalchemy.sql import func
from datetime import datetime,timedelta
from sqlalchemy import or_, and_, Date, cast
from uuid import UUID
from users.models.user_model import Users  
from users.models import user_model
from users.schemas import user_sch


def hash_password(password):
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_password.decode("utf-8")

def get_user(db: Session, username: str):
    return db.query(Users).filter(Users.username == username).first()

def get_user_byphone(db: Session, username:Optional[str]=None):
    query = db.query(Users)
    if username is not None:
        query = query.filter(Users.username == username)
    return query.first()

def user_create(db: Session, user: user_sch.UserCreate):
    hashed_password = hash_password(user.password)

    db_user = Users(
        username=user.username,
        hashed_password=hashed_password,
        name=user.name,
        phone_number=user.phone_number,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def user_update(db:Session,id:int,status:Optional[int]=None,password:Optional[str]=None,phone_number:Optional[str]=None,name:Optional[str]=None):
    db_user = db.query(Users).filter(Users.id == id).first()
    if status is not None:
        db_user.status = status
    if password is not None:
        db_user.hashed_password = hash_password(password)
    if phone_number is not None:
        db_user.phone_number = phone_number
    if name is not None:
        db_user.name = name
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session,name,id,phone_number,status):
    query = db.query(Users)
    if name is not None:
        query = query.filter(Users.name.ilike(f"%{name}%"))
    if id is not None:
        query = query.filter(Users.id == id)
    if phone_number is not None:
        query = query.filter(Users.phone_number.ilike(f"%{phone_number}%"))
    if status is not None:
        query = query.filter(Users.status == status)
    return query.all()


#create role 



