import os
import json
import pandas as pd
from collections import defaultdict
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter
from datetime import datetime,timedelta


from verifix.query.mindbox import createExport, getIsSended,updateIsSended
from verifix.utils.utils import getFileMinbox, extract_json_from_gz, send_file_telegram

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


def parse_datetime(date_str):
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f",  # With milliseconds
        "%Y-%m-%dT%H:%M:%S"  # Without milliseconds
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass

    raise ValueError(f"Time data {date_str} does not match known formats")


def prepareReport():
    with SessionLocal() as db:
        query_ = getIsSended(db=db)
        file_directory = '/srv/ftp/test/upload'
        output_directory = '/var/www/verifix-api/files'
        file_id = query_.export_id
        file_return = extract_json_from_gz(directory=file_directory, output_directory=output_directory, target_id=file_id)


        if file_return and os.path.exists(file_return['file_path']):
            file_path = file_return['file_path']
            # Read and process the JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            fraud_orders = defaultdict(list)

            # Process Orders
            customer_orders = defaultdict(dict)  # Tracking order frequency

            for order in data.get("orders", []):
                order_id = order["ids"].get("mindboxId")
                branch_name = order['firstAction']['channel']['name']
                total_price = str(order.get("totalPrice", 0))
                order_date = str(order['firstAction']['dateTimeUtc'])

                formatted_date = parse_datetime(order_date)
                formatted_date = formatted_date.strftime("%d.%m.%Y %H:%M:%S")


                # Track how many orders a customer has made
                customer_ = order.get('customer')
                if customer_:

                    customer_ids = order['customer'].get('ids')
                    if not customer_ids:
                        continue

                    customer_id = order['customer']['ids'].get('externalClientId')
                    if not customer_id:
                        continue

                    customer_phone = order['customer'].get('mobilePhone',1)


                else:
                    continue

                customer_data = customer_orders.get(customer_id)
                if customer_data:
                    customer_orders[customer_id]['orderCount'] += 1
                    customer_orders[customer_id]['customerPhone'] = customer_phone
                    customer_orders[customer_id]['customerBranch'] = branch_name
                else:
                    customer_orders[customer_id] ={}
                    customer_orders[customer_id]['orderCount'] = 1
                    customer_orders[customer_id]['customerPhone'] = customer_phone
                    customer_orders[customer_id]['customerBranch'] = branch_name


                # Check for excessive spending
                for balance_info in order.get("bonusPointsInfoPerBalanceTypes", []):
                    # balance_type = balance_info.get("balanceType", {})
                    earned_amount = balance_info.get("earnedAmount", 0)
                    spent_amount = balance_info.get("spentAmount", 0)


                    if spent_amount >= 50000:
                        fraud_orders["high_spending"].append([order_id, spent_amount,total_price,customer_phone, branch_name,formatted_date])

                    if earned_amount >= 50000:
                        fraud_orders["high_earning"].append([ order_id, earned_amount,total_price,customer_phone, branch_name,formatted_date])

            # Identify frequent users (3+ orders)
            for customer_id, order_count in customer_orders.items():
                if order_count['orderCount'] >= 3:
                    fraud_orders["frequent_usage"].append([order_count['orderCount'],order_count['customerPhone'], order_count['customerBranch']])

            # Create an Excel file with three sheets
            output_excel = os.path.join(output_directory, "fraud_orders.xlsx")

            with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
                if fraud_orders["frequent_usage"]:
                    df1 = pd.DataFrame(fraud_orders["frequent_usage"], columns=["Сколько покупок","Номер телефона","Филиал"])
                    df1.to_excel(writer, sheet_name="Частота покупок", index=False)

                if fraud_orders["high_spending"]:
                    df2 = pd.DataFrame(fraud_orders["high_spending"],
                                       columns=["Номер заказа Mindbox", "Списание баллов","Оплачено не бонусами","Номер телефона","Филиал",'Время покупки'])
                    df2.to_excel(writer, sheet_name="Подозрительные списания", index=False)

                if fraud_orders["high_earning"]:
                    df3 = pd.DataFrame(fraud_orders["high_earning"],
                                       columns=["Номер заказа Mindbox", "Сумма начисления","Итоговая сумма","Номер телефона","Филиал",'Время покупки'])
                    df3.to_excel(writer, sheet_name="Подозрительные начисления", index=False)
            current_date = datetime.now()-timedelta(days=1)
            current_date = current_date.strftime("%d.%m.%Y")
            send_file_telegram(file_path=output_excel,  caption=f"Fraud Orders {current_date}")
            # Delete file after processing
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file path {e}")
            try:
                os.remove(output_excel)
            except Exception as e:
                print(f"Error deleting excell  {e}")
            try:
                os.remove(file_return['gz_file'])
            except Exception as e:
                print(f"Error deleting gz file {e}")
            updateIsSended(db=db,export_id=file_id)
    return True


@mindbox_router.on_event("startup")
def startup_event():
    scheduler = BackgroundScheduler()
    trigger = CronTrigger(hour=10, minute=58, second=00,
                          timezone=timezone_tash)  # Set the de sired time for the function to run (here, 12:00 PM)
    scheduler.add_job(prepareReport, trigger=trigger)
    scheduler.start()




@mindbox_router.on_event("startup")
def startup_event_request_report():
    scheduler = BackgroundScheduler()
    trigger = CronTrigger(hour=3, minute=00, second=00,
                          timezone=timezone_tash)  # Set the desired time for the function to run (here, 12:00 PM)
    scheduler.add_job(requestFileReportMindbox, trigger=trigger)
    scheduler.start()












