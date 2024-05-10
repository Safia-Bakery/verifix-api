from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi_pagination import paginate, Page, add_pagination
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from uuid import UUID
import random
from services import (
    create_access_token,
    create_refresh_token,
    get_db,
    get_current_user,
    verify_password,
    verify_refresh_token,
)
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from typing import Union, Any
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import engine, SessionLocal

from dotenv import load_dotenv
import os
load_dotenv()
from users.queries import query
from users.schemas import user_sch


user_router = APIRouter()



@user_router.post("/login", summary="Create access and refresh tokens for user",tags=["User"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
    db: Session = Depends(get_db),
):
    user = query.get_user(db, form_data.username)
    if user is None :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password or user is inactive",
        )


    hashed_pass = user.hashed_password
    if not verify_password(form_data.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    return {
        "access_token": create_access_token(user.username),
        "refresh_token": create_refresh_token(user.username),
    }



@user_router.post("/refresh",response_model=user_sch.User, summary="Refresh access token",tags=["User"])
async def refresh(
    refresh_token: str,
    db: Session = Depends(get_db),
):
    username = verify_refresh_token(refresh_token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token",
        )
    return {"access_token": create_access_token(username)}



@user_router.post("/register",response_model=user_sch.User, summary="Register a new user",tags=["User"])
async def register(
    form_data: user_sch.UserCreate,
    db: Session = Depends(get_db)):
    user = query.user_create(db=db, user=form_data)

    return user

@user_router.get("/me", response_model=user_sch.User, summary="Get current user",tags=["User"])
async def current_user(db:Session=Depends(get_db),current_user: user_sch.User = Depends(get_current_user)):
    return current_user


@user_router.put('/update',summary="Reset password",tags=["User"])
async def reset_password(
    form_data:user_sch.UserUpdate,
    db: Session = Depends(get_db),
    current_user: user_sch.User = Depends(get_current_user)
):
    query.user_update(db=db,id=current_user.id,password=form_data.password,phone_number=form_data.phone_number,name=form_data.name)
    return {"message":"Password reset successfully",'success':True}


@user_router.get('/users',summary="Get all users",tags=["User"],response_model=Page[user_sch.User])
async def get_users(name: Optional[str]=None,
                    id: Optional[int]=None,
                    phone_number: Optional[str]=None,
                    status: Optional[int]=None,
                    db: Session = Depends(get_db),
                    current_user: user_sch.User = Depends(get_current_user)):
    users = query.get_users(db,name=name,id=id,phone_number=phone_number,status=status)
    return paginate(users)





















