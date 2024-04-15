from pydantic import BaseModel, validator
from fastapi import Form, UploadFile, File
from typing import Optional, Annotated, Dict
from datetime import datetime, time
from fastapi import Form
from uuid import UUID

    





class User(BaseModel):
    id:int
    name: Optional[str]=None
    phone_number: Optional[str]=None
    created_at: Optional[datetime]=None
    updated_at: Optional[datetime]=None
    class Config:
        orm_mode = True



class UserCreate(BaseModel):
    username:str
    password:str
    name: Optional[str]=None
    phone_number: Optional[str]=None
    

class UserUpdate(BaseModel):
    #username:Optional[str]=None
    password:Optional[str]=None
    name: Optional[str]=None
    phone_number: Optional[str]=None




class ResetPassword(BaseModel):
    password:str
    phone_number:Optional[str]=None 







