import pytz
import requests
from dotenv import load_dotenv
import os
from datetime import datetime,timedelta
load_dotenv()  # Load environment variables from .env
import os
import gzip
import shutil
timezonetash = pytz.timezone("Asia/Tashkent")

SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL')
bot_token = os.getenv("TELEGRAMBOT")
chat_id = os.getenv('CHAT')

def getFileMinbox():
    today = datetime.now(tz=timezonetash)

    yesterday = today - timedelta(days=1)
    from_date = yesterday.strftime("%Y-%-m-%-d 00:00:00")
    to_date = today.strftime("%Y-%-m-%-d 00:00:00")


    # Get environment variables safely
    server_user = os.getenv('SERVER_USER', 'default_user')
    server_password = os.getenv('SERVER_PASSWORD', 'default_password')
    server_host = os.getenv('SERVER_HOST', 'default_host')

    # Define request body
    body_ = {
        "sinceDateTimeUtc": from_date,
        "tillDateTimeUtc": to_date,
        "exportOutput": {
            "type": "FTP",
            "directory": "/mindbox",
            "credentials": {
                "userName": server_user,
                "password": server_password
            },
            "server": {
                "url": f"ftp://{server_host}",
                "port": 21
            }
        }
    }

    # API URL and Headers
    url_ = "https://api.mindbox.ru/v3/operations/sync?endpointId=safiabakery.fraud&operation=SafiaExportOrders"
    headers = {
        "Authorization": "SecretKey j2IJGNyoO6BwtxhQS00wr9DVE452R3Re",
        "Content-Type": "application/json"
    }

    # Send request and handle errors
    try:
        response = requests.post(url_, json=body_, headers=headers)
        response.raise_for_status()  # Raise error for 4xx/5xx responses
        return response.json()  # Return JSON response
    except requests.exceptions.RequestException as e:
        return False



def checkStatusFileMindbox(export_id):

    # Define request body
    body_ = {
            "exportId":str(export_id)
    }

    # API URL and Headers
    url_ = "https://api.mindbox.ru/v3/operations/sync?endpointId=safiabakery.fraud&operation=SafiaExportOrders"
    headers = {
        "Authorization": "SecretKey j2IJGNyoO6BwtxhQS00wr9DVE452R3Re",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url_, json=body_, headers=headers)
        response.raise_for_status()  # Raise error for 4xx/5xx responses
        return response.json()  # Return JSON response
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}



def extract_json_from_gz(directory, target_id, output_directory):
    for file in os.listdir(directory):
        if file.endswith(".gz") and target_id in file:
            gz_path = os.path.join(directory, file)
            json_filename = file.replace(".gz", "")
            output_path = os.path.join(output_directory, json_filename)

            with gzip.open(gz_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

            return {'gz_file':gz_path,'file_path':output_path}

    return None


def send_file_telegram( file_path, caption="Here is your file"):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    with open(file_path, 'rb') as file:
        files = {'document': file}
        data = {'chat_id': chat_id, 'caption': caption}
        response = requests.post(url, data=data, files=files)
    return response.json()