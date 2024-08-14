import os
from datetime import datetime
import asyncio
import time
from screeninfo import get_monitors
import os

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
HEADLESS = False
# Determine API type
api_type = "dev"
API_BASE_URL = "https://www.phoneburner.com"
TOKEN_TEXT_FILE = "tokens.txt"
if api_type == "dev":
    CLIENT_ID = "3daed5e60e3c6de47c08ed4a2ec5c44ab4d07b58"
    CLIENT_SECRET = "8a0e5e181a37eaba73b50bcfd069b49766995a59"
    APPLICATION_NAME = "Tax Overages Lead Generation System"
    CALL_BACK_URL = "https://www.phoneburner.com/"
    PHONE_BURNER_USER_ID = "1127743373"
    PHONE_BURNER_USER_NAME = "rohitash@exoticaitsolutions.com"
    PHONE_BURNER_PASSWORD = "Exotica@123"
elif api_type == "prod":
    CLIENT_ID = "fea8423d7dd5723fade125b2ec7828e21bdb9bc6"
    CLIENT_SECRET = "7fd2301e856b22af449ca3b103771db8eade2ef8"
    APPLICATION_NAME = "Tax Overages Lead Generation System"
    CALL_BACK_URL = "https://www.phoneburner.com/"
    PHONE_BURNER_USER_ID = "1127327657"
    PHONE_BURNER_USER_NAME = "maveninfoadvisors@gmail.com"
    PHONE_BURNER_PASSWORD = "Exotica"
else:
    raise ValueError(f"Unknown API_TYPE: {api_type}")
