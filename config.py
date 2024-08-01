import os
from datetime import datetime
import asyncio
import time
from screeninfo import get_monitors
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
# Determine API type


APP_TITLE = "Surplus Funds/Tax Overages Lead Generation System"
APP_NAME = APP_TITLE
JSON_FILE_NAME = "websites.json"
# REPORT_FOLDER = os.path.join(os.getcwd(), "output")
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
FILE_TYPE = "csv"
CURRENT_DATE = datetime.now()
monitor = get_monitors()[0]
WIDTH, HEIGHT = monitor.width, monitor.height
THREAD_EVENT = asyncio.Event()
NEW_EVENT_LOOP = asyncio.new_event_loop()
START_TIME = time.time()
HEADLESS = True
# Determine API type
api_type = os.getenv("API_TYPE")
API_BASE_URL = os.getenv("API_BASE_URL")
if api_type == "dev":
    CLIENT_ID = os.getenv("DEV_CLIENT_ID")
    CLIENT_SECRET = os.getenv("DEV_CLIENT_SECRET")
    APPLICATION_NAME = os.getenv("DEV_APPLICATION_NAME")
    CALL_BACK_URL = os.getenv("DEV_CALL_BACK_URL")
    PHONE_BURNER_USER_ID = os.getenv("DEV_PHONE_BURNER_USER_ID")
    ACCESS_TOKEN = os.getenv("DEV_ACCESS_TOKEN")
elif api_type == "prod":
    CLIENT_ID = os.getenv("PROD_CLIENT_ID")
    CLIENT_SECRET = os.getenv("PROD_CLIENT_SECRET")
    APPLICATION_NAME = os.getenv("PROD_APPLICATION_NAME")
    CALL_BACK_URL = os.getenv("PROD_CALL_BACK_URL")
    PHONE_BURNER_USER_ID = os.getenv("PROD_PHONE_BURNER_USER_ID")
    ACCESS_TOKEN = os.getenv("PROD_ACCESS_TOKEN")
else:
    raise ValueError(f"Unknown API_TYPE: {api_type}")
