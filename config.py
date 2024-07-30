import os
from datetime import datetime
import asyncio
import time
from screeninfo import get_monitors

APP_TITLE = "Surplus Funds/Tax Overages Lead Generation System"
APP_NAME = APP_TITLE
JSON_FILE_NAME = 'websites.json'
REPORT_FOLDER = os.path.join(os.getcwd(), "output")
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
FILE_TYPE = "csv"
CURRENT_DATE = datetime.now()
monitor = get_monitors()[0]
WIDTH, HEIGHT = monitor.width, monitor.height
THREAD_EVENT = asyncio.Event()
NEW_EVENT_LOOP = asyncio.new_event_loop()
START_TIME = time.time()
HEADLESS = True
# Ensure directories exist
os.makedirs(REPORT_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
