from pydantic import BaseModel, validator
from fastapi import Form, UploadFile, File
from typing import Optional, Annotated, Dict
from datetime import datetime, time,date
from fastapi import Form
from uuid import UUID

class DivisionUpdate(BaseModel):
    id:int
    limit: Optional[int]=None
    name: Optional[str]=None
    status:Optional[int]=None


class Division(BaseModel):
    id:int
    limit: Optional[int]=None
    name: Optional[str]=None
    opened_date: Optional[date]=None
    closed_date: Optional[date]=None
    code: Optional[str]=None
    state: Optional[str]=None
    parent_id: Optional[int]=None
    workers: Optional[int]=None
    class Config:
        orm_mode = True