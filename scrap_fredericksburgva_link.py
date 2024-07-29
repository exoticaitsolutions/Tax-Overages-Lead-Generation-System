# Standard library imports
import re
import time
import os
from datetime import datetime

# Third-party imports
from pdf2image import convert_from_path
import pdfplumber
import pytesseract
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from screeninfo import get_monitors
from webdriver_manager.chrome import ChromeDriverManager

# Local application imports
from Common import delete_folder, delete_path, get_the_tesseract_path

# Application Settings
REPORT_FOLDER = os.path.join(os.getcwd(), "output")
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
CURRENT_DATE = datetime.now()
FILE_NAME = "fredericksburgva"
FILE_TYPE = "csv"
EXPECTED_OUTPUT_FILE = '_BU11_7.pdf'
APP_URL = "https://www.fredericksburgva.gov/1142/Surplus-Funds"
monitor = get_monitors()[0]
WIDTH = monitor.width
HEIGHT = monitor.height

def initialize_driver(download_dir):
    """Initialize and return a Selenium WebDriver with specified options."""
    chrome_options = Options()
    window_size = f"{WIDTH},{HEIGHT}"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(f"--window-size={window_size}")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--verbose")
    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False,
        },
    )
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chromedriver_path = ChromeDriverManager().install()
    service = Service(chromedriver_path)
    return webdriver.Chrome(service=service, options=chrome_options)

def classify_data(data):
    date_pattern = re.compile(r'\d{2}/\d{2}/\d{4}')
    money_pattern = re.compile(r'(?:\d{1,3}(?:,\d{3})*|\d+)?\.\d{2}')
    columns = []
    temp = [" ", " ", " ", " "]

    for item in data.split(' '):
        if date_pattern.match(item):
            if temp[0] == " ":
                temp[0] = item
            elif temp[1] == " ":
                temp[1] = item
            elif temp[3] == " ":
                temp[3] = item
        elif money_pattern.match(item):
            if temp[2] == " ":
                temp[2] = item

        if temp.count(" ") == 0:
            columns.append(temp)
            temp = [" ", " ", " ", " "]
    
    if temp != [" ", " ", " ", " "]:
        columns.append(temp)

    return columns

def pdf_to_single_csv(pdfpath, savecsvfile):
    pytesseract.pytesseract.tesseract_cmd = get_the_tesseract_path()
    delimiter = "##"
    delimiter2 = "|"

    # Convert PDF pages to images
    pages = convert_from_path(pdfpath, 300)

    # Extract text from each page
    data_str = ""
    for page in pages:
        data_str += pytesseract.image_to_string(page)
    data_str = re.sub(r'\n', delimiter, data_str)

    # Define regex patterns for each section
    patterns = {
        "case_to_account_of": r'##CASE##(.*?)##ACCOUNT OF##',
        "account_of_to_collection_date": r'##ACCOUNT OF##(.*?)##FREDERICKSBURG CITY CIRCUIT COURT##',
        "pay_date_to_restitution_balance": r'##DATE BALANCE INTEREST DT(.*?)##REST INTEREST##',
        "collection_balance_to_page": r'##BALANCE##(.*?)##PAGE:##',
    }

    # Extract data based on the patterns
    sections = {}
    for key, pattern in patterns.items():
        sections[key] = re.findall(pattern, data_str)

    # Ensure all sections have the same length
    max_length = max(len(section) for section in sections.values())
    for key in sections:
        while len(sections[key]) < max_length:
            sections[key].append('')

    # List to hold the grouped elements
    grouped_data = [''] * 3000  # Initialize grouped_data with empty strings
    for i in range(max_length):
        for key in sections:
            data = sections[key][i]
            data_array = data.split(delimiter)
            x = 0
            for index, item in enumerate(data_array):
                if item:  # Check if the item is not empty
                    if key == "pay_date_to_restitution_balance":
                        for row in classify_data(item):
                            row_combined = " | ".join(row)
                            item = row_combined
                    grouped_data[x] += f'{item}{delimiter2}'
                    x += 1

    # Remove empty strings from grouped_data
    grouped_data = [data for data in grouped_data if data]

    # Split each data item by "|" and create a list of lists
    data_list = [data.split("|") for data in grouped_data]

    # Ensure each row has exactly 7 columns
    for row in data_list:
        while len(row) > 7:
            row[-2] += row.pop(-1)  # Combine extra columns
        while len(row) < 7:
            row.append("")  # Add empty columns if less than 7

    # Define column names
    columns = ["CASE", "ACCOUNT OF", "COLLECTION DATE", "PAY DATE", "RESTITUTION BALANCE", "RESTITUTION INTEREST DT", "REST INTEREST BALANCE"]

    # Create a DataFrame
    df = pd.DataFrame(data_list, columns=columns)
    

    # Select columns of interest
    columns_of_interest = ["CASE", "ACCOUNT OF", "RESTITUTION BALANCE", "PAY DATE"]
    filtered_df = df[columns_of_interest].copy()

    # Rename columns
    column_mapping = {
        "CASE": "Case Number",
        "ACCOUNT OF": "Prior Owner",
        "RESTITUTION BALANCE": "Surplus amount",
        "PAY DATE": "Sale Date"
    }
    filtered_df.rename(columns=column_mapping, inplace=True)

    # Add required columns
    required_columns = ["Property Address", "Parcel ID", "Opening Bid", "Sale Price", "Applicant/Purchaser"]
    for col in required_columns:
        filtered_df.loc[:, col] = 'Nill'

    # Reorder columns
    final_columns = [
        "Property Address",
        "Prior Owner",
        "Parcel ID",
        "Opening Bid",
        "Sale Price",
        "Surplus amount",
        "Sale Date",
        "Case Number",
        "Applicant/Purchaser"
    ]
    for col in final_columns:
        if col not in filtered_df.columns:
            filtered_df.loc[:, col] = "Nill"

    filtered_df = filtered_df[final_columns]

    # Write the DataFrame to a CSV file
    with open(savecsvfile, 'w') as f:
        filtered_df.to_csv(f, index=False)
    print(f"Data extraction complete and CSV file created. {savecsvfile}")
    return savecsvfile

def check_file_downloaded(download_dir, filename):
    files = os.listdir(download_dir)
    if filename in files:
        print(f"File '{filename}' successfully downloaded.")
        return True 
    else:
        print(f"File '{filename}' not found in the download directory.")
        return False

def scrapping_the_data(driver_instance):
    print('Scrapping_the_data')
    """Download the PDF file from the specified URL."""
    if check_file_downloaded(DOWNLOAD_FOLDER, EXPECTED_OUTPUT_FILE):
        download_pdf =  os.path.join(DOWNLOAD_FOLDER, EXPECTED_OUTPUT_FILE)
    else:
        print(f'Opening the URL {APP_URL}')
        driver_instance.get(APP_URL)
        time.sleep(5)
        xpath = '//*[@id="divEditorf07f49c4-e833-4363-b38a-c2847c5c0205"]/div/ul[10]/li[8]/a'
        actions = ActionChains(driver_instance)
        # Locate the download element
        download_element = driver_instance.find_element(By.XPATH, xpath)
        actions.move_to_element(download_element).perform()
        download_element.click()
        print('Download element clicked successfully')
        time.sleep(10)
        download_pdf = os.path.join(DOWNLOAD_FOLDER, EXPECTED_OUTPUT_FILE)
    return True, download_pdf

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
if not os.path.exists(REPORT_FOLDER):
    os.makedirs(REPORT_FOLDER)

driver = initialize_driver(DOWNLOAD_FOLDER)
status, download_file = scrapping_the_data(driver)
print('download_file', download_file)
driver.quit()

if status:
    output_csv_path = os.path.join(REPORT_FOLDER, f'{FILE_NAME}_{CURRENT_DATE.strftime("%Y_%B_%d")}.{FILE_TYPE}')
    print('output_csv_path' , output_csv_path)
    pdf_to_single_csv(download_file, output_csv_path)
    delete_path(download_file)
    delete_folder(DOWNLOAD_FOLDER)
else:
    print('Ubanle to Scrapp ')