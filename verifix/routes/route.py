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
from datetime import datetime,date
from services import (
    create_access_token,
    create_refresh_token,
    get_db,
    get_current_user,
    verify_password,
    verify_refresh_token,
    get_virifix_divisions,
    get_verifix_timesheets,
    excell_generate,
    get_verifix_workers,
    get_verifix_staff,
    get_verifix_schedules,
    sort_list_with_keys_at_end

)
import pytz


timezone_tash = pytz.timezone("Asia/Tashkent")



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
    cursor = 1
    while True:
        divisions_list = get_virifix_divisions(cursor=cursor)
        for i in divisions_list['data']:
            crud.division_create(db=db,id=int(i["division_id"]),name=i["name"],code=i["code"],state=i["state"],parent_id=i["parent_id"])
        if len(divisions_list['data'])>0:
            cursor = divisions_list['meta']['next_cursor']
        else:
            break
    cursor = 1
    while True:
        schedules = get_verifix_schedules(cursor=cursor)
        for i in schedules['data']:
            crud.create_schedule(db=db,id=i['schedule_id'],name=i['name'],code=i['code'],state=i['state'])
        if len(schedules['data'])>0 :

            cursor = schedules['meta']['next_cursor']
        else:
            break
    cursor = 1
    while True:
        worker_list = get_verifix_workers(cursor=cursor)
        for i in worker_list['data']:
            crud.create_staff(db=db,id=i['staff_id'],schedule_id=i['schedule_id'],division_id=i['org_unit_id'],phone_number=i['main_phone'],name=i['employee_name'],employee_id=i['employee_id'])
        if len(worker_list['data'])>0:
            cursor = worker_list['meta']['next_cursor']
        else:
            break

    # divisions_list = get_virifix_divisions()
    # for i in divisions_list['data']:
    #     crud.division_create(db=db,id=int(i["division_id"]),name=i["name"],code=i["code"],state=i["state"],parent_id=i["parent_id"])
    return {"message":"Divisions created successfully",'success':True}


@verifix_router.get("/divisions", summary="Get divisions",tags=["Division"])
async def get_divisions(
    from_date: date,
    db: Session = Depends(get_db),
    current_user: user_sch.User = Depends(get_current_user)
):
    expected_workers = 0
    came_workers = 0
    division_count = []
    division_dict = {}
    required_schedules = [505,21,44,45,41,54]
    schedule_list = crud.get_schedules(db=db)
    schedule_data = {}


    division_list = crud.get_divisions(db=db)
    for i in division_list:
        for schedule in schedule_list:
            if schedule.id in required_schedules:
                schedule_data[str(schedule.id)] = schedule.name
                get_from_division = division_dict.get(str(i.id))
                if get_from_division:
                    division_dict[str(i.id)][str(schedule.id)] = 0
                else:
                    division_dict[str(i.id)] = {str(schedule.id):0}

        division_dict[str(i.id)]['came_workers'] = 0
        division_dict[str(i.id)]['division_workers'] = 0



    cursor = 1

    while True:
        timesheets = get_verifix_timesheets(fromdate=from_date.strftime("%d.%m.%Y"),todate=from_date.strftime("%d.%m.%Y"),cursor=cursor)
        #worker_list = get_verifix_workers(cursor=cursor)
        for i in timesheets['data']:
            try:
                input_time_value = i['days'][0]['input_time']
                expected_workers += 1
                if input_time_value:
                    came_workers += 1
                    staff_data = crud.get_staff(db=db,staff_id=i['staff_id'])
                    if not staff_data:
                        staff_data = get_verifix_staff(i['staff_id'])
                        staff_data = crud.create_staff(db=db,id=i['staff_id'],schedule_id=i['division_id'],division_id=staff_data['data'][0]['org_unit_id'],phone_number=staff_data['data'][0]['main_phone'],name=staff_data['data'][0]['employee_name'],employee_id=staff_data['data'][0]['employee_id'])
                    if staff_data.schedule_id in required_schedules:
                        division_dict[str(staff_data.division_id)][str(staff_data.schedule_id)] += 1
                    division_dict[str(staff_data.division_id)]['came_workers'] += 1
                division_dict[str(staff_data.division_id)]['division_workers'] += 1


            except :
                pass
        if len(timesheets['data'])>0:
            cursor = timesheets['meta']['next_cursor']
        else:
            break
    division_list = sort_list_with_keys_at_end(data=division_list,keys_list=['9431 Бургер цех',
                                                             '5111 Техн. разработки',
                                                             '0002 Автоматизация оборудования',
                                                             '0111 Склад СиМ',
                                                             '5411 Дегустационная',
                                                             '5211 Кабинет ЗамНач'
                                                             ])
    for i in division_list:
        division_count.append({'id':i.id,"division":i.name,"workers":division_dict[str(i.id)],'limit':i.limit})
    return {"data":division_count,'schedules':schedule_data,'expected_workers':expected_workers,'came_workers':came_workers}





@verifix_router.get("/divisions/excell", summary="Get timesheets",tags=["Timesheet"])
async def get_divisions_excell(
    from_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: user_sch.User = Depends(get_current_user)
):
    division_list = crud.get_divisions(db=db)
    division_dict = {}

    division_list = crud.get_divisions(db=db)
    for i in division_list:
        division_dict[str(i.id)] = 0
    cursor = 1

    while True:
        worker_list = get_verifix_workers(cursor=cursor)
        for i in worker_list['data']:
            staff= crud.get_staff(db=db,staff_id=i['staff_id'])
            if not staff:
                staff_data = get_verifix_staff(i['staff_id'])
                staff = crud.create_staff(db=db,schedule_id=i["schedule_id"],id=i['staff_id'],division_id=staff_data['data'][0]['org_unit_id'],phone_number=staff_data['data'][0]['main_phone'],name=staff_data['data'][0]['employee_name'],employee_id=staff_data['data'][0]['employee_id'])
            division_dict[str(staff.division_id)] += 1
        if len(worker_list['data'])>0:
            cursor = worker_list['meta']['next_cursor']
        else:
            break

    division_list = sort_list_with_keys_at_end(data=division_list, keys_list=['9431 Бургер цех',
                                                                              '5111 Техн. разработки',
                                                                              '0002 Автоматизация оборудования',
                                                                              '0111 Склад СиМ',
                                                                              '5411 Дегустационная',
                                                                              '5211 Кабинет ЗамНач'
                                                                              ])
    file_name = excell_generate(division_list,division_dict)

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
            if pd.isnull(i['Норма Выхода']):
                limit = None
            else:
                limit = int((i['Норма Выхода']))

            crud.update_division(db, schema.DivisionUpdate(id=i['№'],limit=limit,name=i['Отдел'],status=None))
    except Exception as e:
        return {"message":str(e)}
    return {"message":"Timesheets updated successfully",'success':True}

@verifix_router.put("/staff", summary="Staff",tags=["STAff"])
async def create_staff(
    db: Session = Depends(get_db),
    current_user: user_sch.User = Depends(get_current_user),
):
    cursor = 1
    while True:
        worker_list = get_verifix_workers(cursor=cursor)
        if len(worker_list['data'])>0:
            cursor = worker_list['meta']['next_cursor']
        else:
            break
        for i in worker_list['data']:
            crud.create_staff(db=db,id=i['staff_id'],division_id=i['org_unit_id'],phone_number=i['main_phone'],name=i['employee_name'],employee_id=i['employee_id'])

        
    return {"message":"Staff created successfully",'success':True}
