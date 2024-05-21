from datetime import datetime, timedelta
import pytz
from jose import jwt
from passlib.context import CryptContext
import bcrypt
import random
import string

from sqlalchemy.orm import Session
from typing import Union, Any
from fastapi import (
    Depends,
    HTTPException,
    status,
)
import smtplib
from database import engine, SessionLocal
from pydantic import ValidationError
from fastapi.security import OAuth2PasswordBearer
import xml.etree.ElementTree as ET
import os
from users.schemas import user_sch
#from schemas import user_schema
#from queries import user_query as crud
from dotenv import load_dotenv
import requests
from users.queries import query

load_dotenv()

import pandas as pd



ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")  # should be kept secret
JWT_REFRESH_SECRET_KEY = os.environ.get("JWT_REFRESH_SECRET_KEY") # should be kept secret
ALGORITHM = os.environ.get("ALGORITHM")


VERIFIX_URL=os.environ.get("VERIFIX_URL")
VERIFIX_USERNAME=os.environ.get("VERIFIX_USERNAME")
VERIFIX_PASSWORD=os.environ.get("VERIFIX_PASSWORD")

smtp_port = 587


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
reuseable_oauth = OAuth2PasswordBearer(tokenUrl="/login", scheme_name="JWT")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=REFRESH_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
    return encoded_jwt



async def get_current_user(
    token: str = Depends(reuseable_oauth), db: Session = Depends(get_db)
) -> user_sch.User:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        expire_date = payload.get("exp")
        sub = payload.get("sub")
        if datetime.fromtimestamp(expire_date) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user: Union[dict[str, Any], None] = query.get_user(db, sub)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )
    return user

def verify_refresh_token(refresh_token: str) -> Union[str, None]:
    try:
        payload = jwt.decode(refresh_token, JWT_REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        expire_date = payload.get("exp")
        sub = payload.get("sub")
        if datetime.fromtimestamp(expire_date) < datetime.now():
            return None
    except (jwt.JWTError, ValidationError):
        return None
    return sub



def generate_random_filename(length=30):
    # Define the characters you want to use in the random filename
    characters = string.ascii_letters + string.digits
    # Generate a random filename of the specified length
    random_filename = "".join(random.choice(characters) for _ in range(length))

    return random_filename


def get_virifix_divisions(cursor):
    url = f"{VERIFIX_URL}/b/vhr/api/v1/core/division$list"

    response = requests.get(url, auth=(VERIFIX_USERNAME, VERIFIX_PASSWORD),headers={'cursor':str(cursor)})
    return response.json()



def get_verifix_schedules(cursor):
    url = f"{VERIFIX_URL}/b/vhr/api/v1/core/schedule$list"

    response = requests.get(url, auth=(VERIFIX_USERNAME, VERIFIX_PASSWORD),headers={'cursor':str(cursor)})
    return response.json()

     

def get_verifix_timesheets(fromdate, todate, cursor):
    url = f"{VERIFIX_URL}/b/vhr/api/v1/core/timesheet$export"
    body = {
        "period_begin_date": fromdate,
        "period_end_date": todate,
        "division_ids": [],
        "employee_ids": []
    }
    headers = {
        'Content-Type': 'application/json',  # Ensure the content type is set to application/json
        'cursor': str(cursor)  # Cursor can be part of the headers if that's expected by the API
    }

    # Switch to using POST if the API is expected to receive JSON data in the body
    response = requests.post(url, auth=(VERIFIX_USERNAME, VERIFIX_PASSWORD), json=body, headers=headers)

    try:
        return response.json()
    except ValueError:  # More specific exception handling
        return False
    


    



def excell_generate(data,divisions_dict):
    data_frame = {'№':[],'Отдел':[],"Норма Выхода":[],"Штатка":[]}
    for i in data:
        data_frame['№'].append(i.id)
        data_frame['Отдел'].append(i.name)
        if i.name == None:  
            data_frame['Норма Выхода'].append(' ')
        else:
            data_frame['Норма Выхода'].append(i.limit)
        data_frame['Штатка'].append(divisions_dict[str(i.id)])
    df = pd.DataFrame(data_frame)
    df.to_excel('files/output.xlsx',index=False)
    return 'output.xlsx'


def get_verifix_workers(cursor:1):
    url = f"{VERIFIX_URL}/b/vhr/api/v1/pro/employee$list"

    response = requests.get(url, auth=(VERIFIX_USERNAME, VERIFIX_PASSWORD),headers={'cursor':str(cursor)})
    return response.json()


def get_verifix_staff(staff_id):    
    url = f"{VERIFIX_URL}/b/vhr/api/v1/pro/employee$list"
    body = {
        "staff_ids":[staff_id]
    }
    response = requests.get(url, auth=(VERIFIX_USERNAME, VERIFIX_PASSWORD),json=body)
    return response.json()


def sort_list_with_keys_at_end(data, keys_list):
    # Separate the keys that need to be moved to the end
    keys_to_move = [item for item in data if item.name in keys_list]
    other_items = [item for item in data if item.name not in keys_list]

    # Sort the other items

    # Concatenate the sorted items with the keys to move
    final_sorted_list = other_items + keys_to_move

    return final_sorted_list


