import random
import pdfplumber
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from screeninfo import get_monitors
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

from Common import delete_folder, delete_path



# Application Settings
REPORT_FOLDER = os.path.join(os.getcwd(), "output")
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
CURRENT_DATE = datetime.now()
FILE_NAME = "sumterclerk"
FILE_TYPE = "csv"
APP_URL = "https://www.sumterclerk.com/surplus-funds-list"
monitor = get_monitors()[0]
WIDTH = monitor.width
HEIGHT = monitor.height


def initialize_driver(download_dir):
    chrome_options = Options()
    # Get the monitor's width and height
    window_size = f'{WIDTH},{HEIGHT}'
    print(f"Window Size: {window_size}")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(f'--window-size={window_size}')
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--verbose')
    chrome_options.add_experimental_option("prefs", {
            "download.default_directory":download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False
    })
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chromedriver_path = ChromeDriverManager().install()
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service = service ,options = chrome_options)
    return driver

def check_file_downloaded(download_dir, filename):
    files = os.listdir(download_dir)
    if filename in files:
        print(f"File '{filename}' successfully downloaded.")
        return True 
    else:
        print(f"File '{filename}' not found in the download directory.")
        return False
        
def download_pdf(driver, xpath, expected_filename):
    checked = check_file_downloaded(DOWNLOAD_FOLDER, expected_filename)
    if checked:
        download_pdf = os.path.join(DOWNLOAD_FOLDER, expected_filename)
    else:
        actions = ActionChains(driver)
        # Locate the download element
        download_element = driver.find_element(By.XPATH, xpath)
        print('Download element:', download_element)
        # Perform click action
        actions.move_to_element(download_element).click().perform()
        time.sleep(5)
        print('Download element clicked successfully')
        wait = WebDriverWait(driver, 30)  # wait up to 10 seconds
        donwload_path = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[4]/div/div[3]/div[2]/div[2]/div[2]')))
        print('donwload_path',donwload_path)
        actions.move_to_element(donwload_path).click().perform()
        print('donwload_path element clicked successfully')
        time.sleep(5)
        download_pdf = os.path.join(DOWNLOAD_FOLDER, expected_filename)
    return download_pdf

def pdf_to_single_csv(pdf_path, csv_path):
    """
    Convert tables in a PDF to a single CSV file, cleaning specific unwanted rows,
    empty rows, renaming columns, and adding default columns if necessary.

    Parameters:
    - pdf_path (str): The path to the input PDF file.
    - csv_path (str): The path where the CSV file will be saved.
    """
    try:
        print('Starting PDF to CSV conversion...')
        all_tables = []

        with pdfplumber.open(pdf_path) as pdf:
            # Iterate over all pages in the PDF
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    df = df.apply(lambda x: x.str.replace("LIST LAST UPDATED 7/5/2024", "", regex=False) if x.dtype == "object" else x)
                    df = df.apply(lambda x: x.str.replace("ALL FUNDS LISTED ARE STILL HELD BY CLERK", "", regex=False) if x.dtype == "object" else x)
                    df = df.dropna(how='all')
                    df = df[df.apply(lambda row: row.astype(str).str.strip().ne('').any(), axis=1)]
                    
                    all_tables.append(df)
        
        if all_tables:
            print('Combining all tables into one DataFrame...')
            combined_df = pd.concat(all_tables, ignore_index=True)
            combined_df = combined_df.dropna(how='all')
            combined_df = combined_df[combined_df.apply(lambda row: row.astype(str).str.strip().ne('').any(), axis=1)]
            
            combined_df = combined_df.fillna('Nill')

            even_rows = combined_df.iloc[::2].reset_index(drop=True)
            odd_rows = combined_df.iloc[1::2].reset_index(drop=True)
            odd_rows = odd_rows.reindex(even_rows.index, fill_value=pd.NA)
            merged_df = pd.concat([even_rows, odd_rows.add_suffix('_Odd')], axis=1)
            column_mapping = {
                "PROPERTY OWNER & ADDRESS_Odd": "Property Address",
                "PROPERTY OWNER & ADDRESS": "Prior Owner",
                "PARCEL #": "Parcel ID",
                "AMOUNT OF SURPLUS": "Surplus amount",
                "SALE DATE": "Sale Date",
                "APPLICATION #": "Applicant/Purchaser"
            }
            
            renamed_df = merged_df.rename(columns=column_mapping)
            
            # Add required columns if they are missing, with default values
            required_columns = [
                "Opening Bid",
                "Sale Price",
                "Case Number"
            ]

            for col in required_columns:
                if col not in renamed_df.columns:
                    renamed_df[col] = 'Nill'
            renamed_df = renamed_df.fillna('Nill')
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
            
            
            renamed_df = renamed_df[final_columns]
            for col in final_columns:
                if col not in renamed_df.columns:
                    renamed_df[col] = 'Nill'
            renamed_df.to_csv(csv_path, index=False)
            print(f"Filtered and cleaned data saved to {csv_path}")
        else:
            print("No tables found in the PDF.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
    # Create the Output directory if it does not exist
    if not os.path.exists(REPORT_FOLDER):
        os.makedirs(REPORT_FOLDER)

    # Initialize the WebDriver
    driver = initialize_driver(DOWNLOAD_FOLDER)
    # Open the target webpage
    driver.get(APP_URL)
    
    # Define the XPath for the download link
    xpath = '/html/body/div[3]/main/div[2]/div/section/div/div/div/div/div/div[1]/ul[2]/li[2]/strong/a'
    # Download the PDF
    expected_filename = "Tax Deed Surplus.pdf"
    downlaod_file = download_pdf(driver, xpath,expected_filename)
    print('downlaod_file', downlaod_file)
    # print('data', data)
    output_csv = os.path.join(REPORT_FOLDER, f'{FILE_NAME}_{CURRENT_DATE.strftime("%Y_%B_%d")}.{FILE_TYPE}')
    pdf_to_single_csv(downlaod_file,output_csv)
    delete_path(downlaod_file)
    delete_folder(DOWNLOAD_FOLDER)
    driver.quit()