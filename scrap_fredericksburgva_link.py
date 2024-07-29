"""
scrap_sumterclerk_county.py
This script performs web scraping and data processing tasks related to 
the Sumter County Clerk's office. It uses Selenium to automate the downloading of PDF
files from a specified URL and then processes these PDFs to extract
tabular data, which is subsequently saved to a CSV file.

Requirements:
- Selenium
- pdfplumber
- pandas
- screeninfo
- webdriver-manager
Usage:
Run the script as the main program to execute the entire workflow, 
including downloading the PDF and converting it to CSV format.
Dependencies:
- Common module with delete_folder and delete_path functions.
"""

# Standard library imports
import time
import re
import os

from datetime import datetime

# Third-party imports
import pytesseract
from selenium import webdriver
from PIL import Image

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from screeninfo import get_monitors
from webdriver_manager.chrome import ChromeDriverManager
from pdf2image import convert_from_path

# Local application imports
from Common import get_the_tesseract_path

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
    print(f"Window Size: {window_size}")
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


def check_file_downloaded(download_dir, filename):
    """Check if the specified file has been downloaded."""
    files = os.listdir(download_dir)
    if filename in files:
        print(f"File '{filename}' successfully downloaded.")
        return True
    print(f"File '{filename}' not found in the download directory.")
    return False


def download_pdf(driver_instance, xpath, expected_filename):
    """Download the PDF file from the specified URL."""
    checked = check_file_downloaded(DOWNLOAD_FOLDER, expected_filename)
    if checked:
        download_pdf = os.path.join(DOWNLOAD_FOLDER, expected_filename)
    else:
        print(f'Openign the url {APP_URL}')
        driver.get(APP_URL)
        actions = ActionChains(driver)
            # Locate the download element
        download_element = driver_instance.find_element(By.XPATH, xpath)
        actions = ActionChains(driver)
        actions.move_to_element(download_element).perform()
        download_element.click()
        print('Download element clicked successfully')
        download_pdf = os.path.join(DOWNLOAD_FOLDER, expected_filename)
        time.sleep(5)
    return download_pdf
# Function to classify data into columns
def classify_data(data):
    columns = []
    temp = [" ", " ", " ", " "]
    # Define regular expression patterns
    date_pattern = re.compile(r'\d{2}/\d{2}/\d{4}')
    money_pattern = re.compile(r'(?:\d{1,3}(?:,\d{3})*|\d+)?\.\d{2}')
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
def pdf_to_single_csv(pdf_path, csv_path):
    print('def pdf_to_single_csv(pdf_path, csv_path):')
    pytesseract.pytesseract.tesseract_cmd = get_the_tesseract_path()
    delimiter="##"
    delimiter2="|"
    # Define a list to store extracted text
    extracted_texts = []
    # Process each image
    images = convert_from_path(pdf_path)
    unwanted_texts = [
    'FASBUO11 FREDERICKSBURG CITY CIRCUIT COURT PAGE: 1\nRESTITUTION IN COLLECTIONS OVER 90 DAYS WITHOUT PAYMENT\nPREPARED: 06/28/24\n\nFOR COMMONWEALTH ATTORNEY\n'
]
    for i, image in enumerate(images):
        image_path = os.path.join(f'page_{i}.png')
        # Save image
        image.save(image_path, 'PNG')

        # Extract text from image
        text = pytesseract.image_to_string(image)
        # Remove unwanted text
    for unwanted_text in unwanted_texts:
        text = text.replace(unwanted_text, '')
        extracted_texts.append(text)

    # Delete the image file after processing
    print('extracted_texts', extracted_texts)
    os.remove(image_path)
    


if __name__ == "__main__":
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
    if not os.path.exists(REPORT_FOLDER):
        os.makedirs(REPORT_FOLDER)
    driver = initialize_driver(DOWNLOAD_FOLDER)
    driver.get(APP_URL)
    download_file_path = download_pdf(
        driver,
        '//*[@id="divEditorf07f49c4-e833-4363-b38a-c2847c5c0205"]/div/ul[10]/li[8]/a',
        EXPECTED_OUTPUT_FILE,
    )
    print("Download file path:", download_file_path)
    output_csv_path = os.path.join( REPORT_FOLDER, f'{FILE_NAME}_{CURRENT_DATE.strftime("%Y_%B_%d")}.{FILE_TYPE}')
    print('output_csv_path', output_csv_path)
    pdf_to_single_csv(download_file_path, output_csv_path)
   
    # 
    # delete_path(download_file_path)
    # delete_folder(DOWNLOAD_FOLDER)
    driver.quit()
