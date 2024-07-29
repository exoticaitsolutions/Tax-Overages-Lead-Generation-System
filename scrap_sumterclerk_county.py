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
import os
from datetime import datetime

# Third-party imports
import pdfplumber
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
from Common import delete_folder, delete_path

# Application Settings
REPORT_FOLDER = os.path.join(os.getcwd(), "output")
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
CURRENT_DATE = datetime.now()
FILE_NAME = "sumterclerk"
FILE_TYPE = "csv"
EXPECTED_OUTPUT_FILE = "Tax Deed Surplus.pdf"
APP_URL = "https://www.sumterclerk.com/surplus-funds-list"
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
    if check_file_downloaded(DOWNLOAD_FOLDER, expected_filename):
        return os.path.join(DOWNLOAD_FOLDER, expected_filename)
    actions = ActionChains(driver_instance)
    download_element = driver_instance.find_element(By.XPATH, xpath)
    print("Download element:", download_element)
    actions.move_to_element(download_element).click().perform()
    time.sleep(5)
    wait = WebDriverWait(driver_instance, 30)
    download_path = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "/html/body/div[1]/div[4]/div/div[3]/div[2]/div[2]/div[2]")
        )
    )
    print("Download path:", download_path)
    actions.move_to_element(download_path).click().perform()
    print("Download path element clicked successfully")
    time.sleep(5)
    return os.path.join(DOWNLOAD_FOLDER, expected_filename)


def extract_and_clean_tables(pdf_path):
    """Extract tables from the PDF and clean them."""
    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                df = pd.DataFrame(table[1:], columns=table[0])
                df = df.apply(
                    lambda x: (
                        x.str.replace("LIST LAST UPDATED 7/5/2024", "", regex=False)
                        if x.dtype == "object"
                        else x
                    )
                )
                df = df.apply(
                    lambda x: (
                        x.str.replace(
                            "ALL FUNDS LISTED ARE STILL HELD BY CLERK",
                            "",
                            regex=False,
                        )
                        if x.dtype == "object"
                        else x
                    )
                )
                df = df.dropna(how="all")
                df = df[
                    df.apply(
                        lambda row: row.astype(str).str.strip().ne("").any(), axis=1
                    )
                ]
                all_tables.append(df)
    return all_tables


def process_dataframes(dataframes):
    """Process and merge the list of DataFrames."""
    if not dataframes:
        raise ValueError("No tables found in the PDF.")
    print("Combining all tables into one DataFrame...")
    combined_df = pd.concat(dataframes, ignore_index=True)
    combined_df = combined_df.dropna(how="all")
    combined_df = combined_df[
        combined_df.apply(lambda row: row.astype(str).str.strip().ne("").any(), axis=1)
    ]
    combined_df = combined_df.fillna("Nill")

    even_rows = combined_df.iloc[::2].reset_index(drop=True)
    odd_rows = combined_df.iloc[1::2].reset_index(drop=True)
    odd_rows = odd_rows.reindex(even_rows.index, fill_value=pd.NA)
    merged_df = pd.concat([even_rows, odd_rows.add_suffix("_Odd")], axis=1)
    column_mapping = {
        "PROPERTY OWNER & ADDRESS_Odd": "Property Address",
        "PROPERTY OWNER & ADDRESS": "Prior Owner",
        "PARCEL #": "Parcel ID",
        "AMOUNT OF SURPLUS": "Surplus amount",
        "SALE DATE": "Sale Date",
        "APPLICATION #": "Applicant/Purchaser",
    }
    renamed_df = merged_df.rename(columns=column_mapping)
    required_columns = ["Opening Bid", "Sale Price", "Case Number"]
    for col in required_columns:
        if col not in renamed_df.columns:
            renamed_df[col] = "Nill"
    renamed_df = renamed_df.fillna("Nill")
    final_columns = [
        "Property Address",
        "Prior Owner",
        "Parcel ID",
        "Opening Bid",
        "Sale Price",
        "Surplus amount",
        "Sale Date",
        "Case Number",
        "Applicant/Purchaser",
    ]

    for col in final_columns:
        if col not in renamed_df.columns:
            renamed_df[col] = "Nill"
    renamed_df = renamed_df[final_columns]
    return renamed_df


def save_to_csv(df, csv_path):
    """Save the DataFrame to a CSV file."""
    df.to_csv(csv_path, index=False)
    print(f"Filtered and cleaned data saved to {csv_path}")


def pdf_to_single_csv(pdf_path, csv_path):
    """
    Convert tables in a PDF to a single CSV file, cleaning specific unwanted rows,
    empty rows, renaming columns, and adding default columns if necessary.

    Parameters:
    - pdf_path (str): The path to the input PDF file.
    - csv_path (str): The path where the CSV file will be saved.
    """
    try:
        print("Starting PDF to CSV conversion...")
        tables = extract_and_clean_tables(pdf_path)
        processed_df = process_dataframes(tables)
        save_to_csv(processed_df, csv_path)
    except FileNotFoundError:
        print(f"File not found: {pdf_path}")
    except pd.errors.EmptyDataError:
        print("No data found in the PDF.")
    except pd.errors.ParserError as e:
        print(f"Pandas parsing error: {e}")
    except PermissionError:
        print(f"Permission denied: {csv_path}")
    except ValueError as e:
        print(f"Value error: {e}")
    except (OSError, IOError) as e:
        print(f"File system error: {e}")


if __name__ == "__main__":
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
    if not os.path.exists(REPORT_FOLDER):
        os.makedirs(REPORT_FOLDER)
    driver = initialize_driver(DOWNLOAD_FOLDER)
    driver.get(APP_URL)
    download_file_path = download_pdf(
        driver,
        "/html/body/div[3]/main/div[2]/div/section/div/div/div/div/div/div[1]/ul[2]/li[2]/strong/a",
        EXPECTED_OUTPUT_FILE,
    )
    print("Download file path:", download_file_path)
    output_csv_path = os.path.join(
        REPORT_FOLDER, f'{FILE_NAME}_{CURRENT_DATE.strftime("%Y_%B_%d")}.{FILE_TYPE}'
    )
    pdf_to_single_csv(download_file_path, output_csv_path)
    delete_path(download_file_path)
    delete_folder(DOWNLOAD_FOLDER)
    driver.quit()
