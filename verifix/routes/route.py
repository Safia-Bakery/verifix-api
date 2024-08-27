from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status,UploadFile,File
from typing import Optional,Annotated
from users.schemas import user_sch
from collections import OrderedDict
import pandas as pd
from datetime import datetime,date
from services import (
    get_db,
    get_current_user,
    get_virifix_divisions,
    get_verifix_timesheets,
    excell_generate,
    get_verifix_workers,
    get_verifix_staff,
    get_verifix_schedules,
    sort_list_with_keys_at_end,
excell_generate_v2

)
from verifix.query import crud
from verifix.schemas import schema
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

#set time zones
timezone_tash = pytz.timezone("Asia/Tashkent")

# base Router
verifix_router = APIRouter()


def update_users(db:Session):
    cursor =1
    division_list = get_virifix_divisions(cursor=cursor)
    while True:
        for i in division_list['data']:
            crud.division_create(db=db,id=int(i["division_id"]),name=i["name"],code=i["code"],state=i["state"],parent_id=i["parent_id"])
        if len(division_list['data'])>0:
            division_list = get_virifix_divisions(cursor=division_list['meta']['next_cursor'])
        else:
            break
    cursor = 1
    workers_list = get_verifix_workers(cursor=cursor)
    while True:
        for i in workers_list['data']:
            crud.create_staff(db=db,id=i['staff_id'],division_id=i['org_unit_id'],phone_number=i['main_phone'],name=i['employee_name'],employee_id=i['employee_id'],schedule_id=i['schedule_id'])
        if len(workers_list['data'])>0:
            workers_list = get_verifix_workers(cursor=workers_list['meta']['next_cursor'])
        else:
            break

    while True:
        schedules = get_verifix_schedules(cursor=cursor)
        for i in schedules['data']:
            crud.create_schedule(db=db, id=i['schedule_id'], name=i['name'], code=i['code'], state=i['state'])
        if len(schedules['data']) > 0:

            cursor = schedules['meta']['next_cursor']
        else:
            break


    return True


@verifix_router.on_event("startup")
def startup_event():
    scheduler = BackgroundScheduler()
    trigger  = CronTrigger(hour=11, minute=50, second=00,timezone=timezone_tash)  # Set the desired time for the function to run (here, 12:00 PM)
    scheduler.add_job(update_users, trigger=trigger, args=[next(get_db())])
    scheduler.start()




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


@verifix_router.get("/v2/divisions", summary="Get divisions",tags=["Division"])
async def get_divisions(
    from_date:date,
    db: Session = Depends(get_db),
    current_user: user_sch.User = Depends(get_current_user)
):
    expected_workers = 0
    came_workers = 0
    required_divisions = [23,102,26,44,104,103]
    ready_data = []
    required_schedules = [505,21,44,45,41,54]
    schedule_list = crud.get_schedules(db=db)
    placing_last = {}
    schedule_data = {}
    required_divisins = []
    division_list = crud.get_divisions(db=db)


    schedule_data['0']  = {}
    schedule_data['0']['divisions'] = {}
    schedule_data['0']['name'] = 'Общий'
    schedule_data['0']['id'] = 0

    placing_last['0'] = {}
    placing_last['0']['divisions'] = {}
    placing_last['0']['name'] = 'Общий'
    placing_last['0']['id'] = 0

    for division in division_list:
        required_divisins.append(division.id)
        if division.id not in required_divisions:
            schedule_data['0']['divisions'][str(division.id)] = {}
            schedule_data['0']['divisions'][str(division.id)]['came_workers'] = 0
            schedule_data['0']['divisions'][str(division.id)]['division_workers'] = 0
            schedule_data['0']['divisions'][str(division.id)]['name'] = division.name
            schedule_data['0']['divisions'][str(division.id)]['id'] = division.id
            schedule_data['0']['divisions'][str(division.id)]['limit'] = division.limit

        else:
            placing_last['0']['divisions'][str(division.id)] = {}
            placing_last['0']['divisions'][str(division.id)]['came_workers'] = 0
            placing_last['0']['divisions'][str(division.id)]['division_workers'] = 0
            placing_last['0']['divisions'][str(division.id)]['name'] = division.name
            placing_last['0']['divisions'][str(division.id)]['id'] = division.id
            placing_last['0']['divisions'][str(division.id)]['limit'] = division.limit

    for schedule in schedule_list:

        if schedule.id in required_schedules:

            schedule_data[str(schedule.id)] = {}
            schedule_data[str(schedule.id)]['divisions'] = {}
            schedule_data[str(schedule.id)]['name'] = schedule.name
            schedule_data[str(schedule.id)]['id'] = schedule.id


            placing_last[str(schedule.id)] = {}
            placing_last[str(schedule.id)]['divisions'] = {}
            placing_last[str(schedule.id)]['name'] = schedule.name
            placing_last[str(schedule.id)]['id'] = schedule.id


            for division in division_list:
                required_divisins.append(division.id)
                if division.id not in required_divisions:
                    schedule_data[str(schedule.id)]['divisions'][str(division.id)] = {}
                    schedule_data[str(schedule.id)]['divisions'][str(division.id)]['came_workers'] = 0
                    schedule_data[str(schedule.id)]['divisions'][str(division.id)]['division_workers'] = 0
                    schedule_data[str(schedule.id)]['divisions'][str(division.id)]['name'] = division.name
                    schedule_data[str(schedule.id)]['divisions'][str(division.id)]['id'] = division.id
                    schedule_data[str(schedule.id)]['divisions'][str(division.id)]['limit'] = division.limit

                else:
                    placing_last[str(schedule.id)]['divisions'][str(division.id)] = {}
                    placing_last[str(schedule.id)]['divisions'][str(division.id)]['came_workers'] = 0
                    placing_last[str(schedule.id)]['divisions'][str(division.id)]['division_workers'] = 0
                    placing_last[str(schedule.id)]['divisions'][str(division.id)]['name'] = division.name
                    placing_last[str(schedule.id)]['divisions'][str(division.id)]['id'] = division.id
                    placing_last[str(schedule.id)]['divisions'][str(division.id)]['limit'] = division.limit

                # for required_division in required_divisions:
                #     schedule_data[str(schedule.id)][str(required_division)] = schedule_data[str(schedule.id)].pop(str(required_division))
                # placing_last = {}

    cursor = 1

    while (timesheets := get_verifix_timesheets(fromdate=from_date.strftime("%d.%m.%Y"),
                                                todate=from_date.strftime("%d.%m.%Y"), cursor=cursor)) != False:
        # timesheets = get_verifix_timesheets(fromdate=from_date.strftime("%d.%m.%Y"),
        #                                     todate=from_date.strftime("%d.%m.%Y"), cursor=cursor)
        if len(timesheets['data']) > 0:
            cursor = timesheets['meta']['next_cursor']
        else:
            cursor = 0

        for i in timesheets['data']:
            try:
                input_time_value = i['days'][0]['input_time']
                expected_workers += 1
                if input_time_value:
                    came_workers += 1
                    staff_data = crud.get_staff(db=db, staff_id=i['staff_id'])

                    if staff_data:
                        if staff_data.division_id in required_divisins:
                            if staff_data.schedule_id in required_schedules:
                                schedule_data[str(0)]['divisions'][str(staff_data.division_id)]['came_workers'] += 1
                                schedule_data[str(0)]['divisions'][str(staff_data.division_id)]['division_workers'] += 1
                                schedule_data[str(staff_data.schedule_id)]['divisions'][str(staff_data.division_id)]['came_workers'] += 1
                                schedule_data[str(staff_data.schedule_id)]['divisions'][str(staff_data.division_id)]['division_workers'] += 1
                else:
                    staff_data = crud.get_staff(db=db, staff_id=i['staff_id'])
                    if staff_data:
                        if staff_data.division_id in required_divisins:
                            if staff_data.schedule_id in required_schedules:
                                schedule_data[str(staff_data.schedule_id)]['divisions'][str(staff_data.division_id)]['division_workers'] += 1
            except:
                pass



    for key,value in schedule_data.items():
        schedule_data[str(key)]['divisions'] = list(value['divisions'].values())

    for key,value in placing_last.items():
        schedule_data[str(key)]['divisions'] = schedule_data[str(key)]['divisions'] + list(value['divisions'].values())



    for key,value in schedule_data.items():
        ready_data.append(value)




    return {"timesheets":ready_data, 'expected_workers': expected_workers, 'came_workers': came_workers}




@verifix_router.post("/v2/divisions/excell", summary="Get divisions",tags=["Division"])
async def get_divisions_excell_v2(
    from_date:date,
    schdules: Optional[list[int]] = None,
    db: Session = Depends(get_db),
    current_user: user_sch.User = Depends(get_current_user)
):


    expected_workers = 0
    came_workers = 0
    required_divisions = [23,102,26,44,104,103]
    ready_data = []
    required_schedules = [505,21,44,45,41,54]
    schedule_list = crud.get_schedules(db=db)
    placing_last = {}
    schedule_data = {}
    required_divisins = []
    division_list = crud.get_divisions(db=db)
    if schdules is not None:
        required_schedules = schdules




    for schedule in schedule_list:

        if schedule.id in required_schedules:

            schedule_data[str(schedule.id)] = {}
            schedule_data[str(schedule.id)]['divisions'] = {}
            schedule_data[str(schedule.id)]['name'] = schedule.name
            schedule_data[str(schedule.id)]['id'] = schedule.id


            placing_last[str(schedule.id)] = {}
            placing_last[str(schedule.id)]['divisions'] = {}
            placing_last[str(schedule.id)]['name'] = schedule.name
            placing_last[str(schedule.id)]['id'] = schedule.id


            for division in division_list:
                required_divisins.append(division.id)
                if division.id not in required_divisions:
                    schedule_data[str(schedule.id)]['divisions'][str(division.id)] = {}
                    schedule_data[str(schedule.id)]['divisions'][str(division.id)]['came_workers'] = 0
                    schedule_data[str(schedule.id)]['divisions'][str(division.id)]['division_workers'] = 0
                    schedule_data[str(schedule.id)]['divisions'][str(division.id)]['name'] = division.name
                    schedule_data[str(schedule.id)]['divisions'][str(division.id)]['id'] = division.id
                    schedule_data[str(schedule.id)]['divisions'][str(division.id)]['limit'] = division.limit

                else:
                    placing_last[str(schedule.id)]['divisions'][str(division.id)] = {}
                    placing_last[str(schedule.id)]['divisions'][str(division.id)]['came_workers'] = 0
                    placing_last[str(schedule.id)]['divisions'][str(division.id)]['division_workers'] = 0
                    placing_last[str(schedule.id)]['divisions'][str(division.id)]['name'] = division.name
                    placing_last[str(schedule.id)]['divisions'][str(division.id)]['id'] = division.id
                    placing_last[str(schedule.id)]['divisions'][str(division.id)]['limit'] = division.limit

                # for required_division in required_divisions:
                #     schedule_data[str(schedule.id)][str(required_division)] = schedule_data[str(schedule.id)].pop(str(required_division))
                # placing_last = {}

    cursor = 1

    while (timesheets := get_verifix_timesheets(fromdate=from_date.strftime("%d.%m.%Y"),
                                                todate=from_date.strftime("%d.%m.%Y"), cursor=cursor)) != False:
        # timesheets = get_verifix_timesheets(fromdate=from_date.strftime("%d.%m.%Y"),
        #                                     todate=from_date.strftime("%d.%m.%Y"), cursor=cursor)
        if len(timesheets['data']) > 0:
            cursor = timesheets['meta']['next_cursor']
        else:
            cursor = 0

        for i in timesheets['data']:
            try:
                input_time_value = i['days'][0]['input_time']
                expected_workers += 1
                if input_time_value:
                    came_workers += 1
                    staff_data = crud.get_staff(db=db, staff_id=i['staff_id'])

                    if staff_data:
                        if staff_data.division_id in required_divisins:
                            if staff_data.schedule_id in required_schedules:
                                schedule_data[str(staff_data.schedule_id)]['divisions'][str(staff_data.division_id)]['came_workers'] += 1
                                schedule_data[str(staff_data.schedule_id)]['divisions'][str(staff_data.division_id)]['division_workers'] += 1
                else:
                    staff_data = crud.get_staff(db=db, staff_id=i['staff_id'])
                    if staff_data:
                        if staff_data.division_id in required_divisins:
                            if staff_data.schedule_id in required_schedules:
                                schedule_data[str(staff_data.schedule_id)]['divisions'][str(staff_data.division_id)]['division_workers'] += 1
            except:
                pass



    for key,value in schedule_data.items():
        schedule_data[str(key)]['divisions'] = list(value['divisions'].values())

    for key,value in placing_last.items():
        schedule_data[str(key)]['divisions'] = schedule_data[str(key)]['divisions'] + list(value['divisions'].values())



    for key,value in schedule_data.items():
        ready_data.append(value)

    excell_generate_v2(ready_data)


    return {'file':'files/outputs.xlsx'}



@verifix_router.get("/divisions", summary="Get divisions",tags=["Division"])
async def get_divisions(
    from_date: date,
    db: Session = Depends(get_db),
    current_user: user_sch.User = Depends(get_current_user)
):
    """
        Retrieves a list of divisions along with their worker counts, schedules, and the number of expected vs. actual workers who came.

        Args:
            from_date (date): The date for which to retrieve division and worker information.
            db (Session): Database session dependency to execute database operations.
            current_user (user_sch.User): The current user performing the operation, injected by dependency.

        Returns:
            dict: A dictionary containing the list of divisions with their details, schedules, expected, and actual worker counts.
    """
    expected_workers = 0
    came_workers = 0
    division_count = []
    division_dict = {}
    required_schedules = [505,21,44,45,41,54]
    schedule_list = crud.get_schedules(db=db)
    schedule_data = {}
    required_divisins = []

    division_list = crud.get_divisions(db=db)
    for i in division_list:
        required_divisins.append(i.id)
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
                    if staff_data.division_id in required_divisins:
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
    required_divisins = []

    division_list = crud.get_divisions(db=db)
    for i in division_list:
        required_divisins.append(i.id)
        division_dict[str(i.id)] = 0
    cursor = 1

    while True:
        worker_list = get_verifix_workers(cursor=cursor)
        for i in worker_list['data']:
            staff= crud.get_staff(db=db,staff_id=i['staff_id'])
            if not staff:
                staff_data = get_verifix_staff(i['staff_id'])
                staff = crud.create_staff(db=db,schedule_id=i["schedule_id"],id=i['staff_id'],division_id=staff_data['data'][0]['org_unit_id'],phone_number=staff_data['data'][0]['main_phone'],name=staff_data['data'][0]['employee_name'],employee_id=staff_data['data'][0]['employee_id'])
            if staff.division_id in required_divisins:
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




