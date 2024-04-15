from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status,UploadFile,File
from fastapi_pagination import paginate, Page, add_pagination
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional,Annotated
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from uuid import UUID
from users.schemas import user_sch
import random
import pandas as pd
import re 
from services import (
    create_access_token,
    create_refresh_token,
    get_db,
    get_current_user,
    verify_password,
    verify_refresh_token,
    get_virifix_divisions,
    get_verifix_timesheets,
    excell_generate

)


verifix_router = APIRouter()    
from verifix.query import crud
from verifix.schemas import schema


@verifix_router.put("/division", summary="Update division",tags=["Division"])
async def update_division(
    form_data: schema.DivisionUpdate,
    db: Session = Depends(get_db),
    current_user: user_sch.User = Depends(get_current_user)
):

    return crud.update_division(db, form_data)



@verifix_router.post("/division", summary="Create division",tags=["Division"])
async def create_division(
    db: Session = Depends(get_db),
    current_user: user_sch.User = Depends(get_current_user)
):
    divisions_list = get_virifix_divisions()
    for i in divisions_list['data']:
        crud.division_create(db=db,id=int(i["division_id"]),name=i["name"],code=i["code"],state=i["state"],parent_id=i["parent_id"])
    return {"message":"Divisions created successfully",'success':True}


@verifix_router.get("/divisions", summary="Get divisions",tags=["Division"])
async def get_divisions(
    from_date: Optional[str]=None,
    to_date: Optional[str]=None,
    name: Optional[str]=None,
    id:Optional[int]=None,
    db: Session = Depends(get_db),
    current_user: user_sch.User = Depends(get_current_user)
):
    division_count = []
    division_list = crud.get_divisions(db=db,id=id,name=name)
    for i in division_list:
        #data = get_verifix_timesheets(i.id,from_date,to_date)
        #if data:

        division_count.append({'id':i.id,"division":i.name,"workers":6,'limit':i.limit})
    

    return {"data":division_count}


@verifix_router.get("/divisions/excell", summary="Get timesheets",tags=["Timesheet"])
async def get_divisions_excell(
    from_date: Optional[str]=None,
    to_date: Optional[str]=None,
    db: Session = Depends(get_db),
    current_user: user_sch.User = Depends(get_current_user)
):
    division_list = crud.get_divisions(db=db)
    file_name = excell_generate(division_list)

    return {"file_name":file_name}


@verifix_router.put("/divisions/excell", summary="Update timesheet",tags=["Timesheet"])
async def update_divisions_excell(
    file:UploadFile=None,
    db: Session = Depends(get_db),
    current_user: user_sch.User = Depends(get_current_user)
):
    
    
    try:
        with open(f"files/{file.filename}", "wb") as buffer:
            while True:
                chunk = await file.read(1024)
                if not chunk:
                    break
                buffer.write(chunk)
        file_path = f"files/{file.filename}"
        data = pd.read_excel(file_path)

        for index,i in data.iterrows():
            if pd.isnull(i['limit']):
                limit = None
            else:
                limit = int((i['limit']))

            crud.update_division(db, schema.DivisionUpdate(id=i['id'],limit=limit,name=i['department']))
    except Exception as e:
        return {"message":str(e)}
    return {"message":"Timesheets updated successfully",'success':True}
