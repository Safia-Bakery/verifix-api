import os

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter

from verifix.query.mindbox import createExport, getIsSended
from verifix.utils.utils import getFileMinbox, extract_json_from_gz

#set time zones
timezone_tash = pytz.timezone("Asia/Tashkent")
from database import SessionLocal



# base Router
mindbox_router = APIRouter()


def requestFileReportMindbox():
    response = getFileMinbox()

    if response:
        with SessionLocal() as db:
            createExport(db=db,export_id=response['exportId'])

    return True


def prepareReport():
    with SessionLocal() as db:
        query_ = getIsSended(db=db)
        print(query_)
        file_directory = '/Users/gayratbekakhmedov/projects/backend/verifx/files'
        output_directory ='/Users/gayratbekakhmedov/projects/backend/verifx/files'
        file_id = '110174'
        file_path = extract_json_from_gz(directory=file_directory,output_directory=output_directory,target_id=file_id)

        if file_path and os.path.exists(file_path):

            # Perform operations on the extracted file...

            # Delete the file after processing
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
            # try:
            #     os.remove(f"{file_path}.gz")
            #
            # except Exception as e:
            #     print(f"Error deleting gz file {e}")


    return True






@mindbox_router.on_event("startup")
def startup_event():
    scheduler = BackgroundScheduler()
    trigger = CronTrigger(hour=17, minute=5, second=00,
                          timezone=timezone_tash)  # Set the desired time for the function to run (here, 12:00 PM)
    scheduler.add_job(prepareReport, trigger=trigger)
    scheduler.start()




@mindbox_router.on_event("startup")
def startup_event_request_report():
    scheduler = BackgroundScheduler()
    trigger = CronTrigger(hour=17, minute=4, second=00,
                          timezone=timezone_tash)  # Set the desired time for the function to run (here, 12:00 PM)
    scheduler.add_job(requestFileReportMindbox, trigger=trigger)
    scheduler.start()












