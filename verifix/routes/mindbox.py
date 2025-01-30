from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status,UploadFile,File,Request
from typing import Optional, Annotated, Any
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
    excell_generate_v2, get_basic_auth

)
from verifix.query import crud
from verifix.schemas import schema
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

#set time zones
timezone_tash = pytz.timezone("Asia/Tashkent")

# base Router
mindbox_router = APIRouter()


@mindbox_router.post("/orders", summary="Update division", tags=["Division"])
async def update_division(
        request: Request,
        db: Session = Depends(get_db),
        username: str = Depends(get_basic_auth),
):
    try:
        data = await request.json()  # Parse JSON data

        if not data:  # If data is empty
            raise HTTPException(status_code=400, detail="Empty JSON body received")

        print(str(data))  # Print as string
        return {"success": True, "message": "Data received", "data": data}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")


