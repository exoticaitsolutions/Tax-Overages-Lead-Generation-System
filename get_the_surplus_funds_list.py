import json
import pdfplumber
import shutil
import time
import os
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

from comman_function import delete_folder, delete_path



# Get the primary monitor's resolution
monitor = get_monitors()[0]

def initialize_driver(download_dir):
    temp_directory = ""
    chrome_options = Options()
    # Get the monitor's width and height
    width = monitor.width
    height = monitor.height
    window_size = f'{width},{height}'
    print(f"Window Size: {window_size}")
    # chrome_options.add_argument("--headless")
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
    checked = check_file_downloaded(download_dir, expected_filename)
    if checked:
        download_pdf = os.path.join(download_dir, expected_filename)
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
        # donwload_path = driver.find_element(By.XPATH, '/html/body/div[1]/div[4]/div/div[3]/div[2]/div[2]/div[2]')
        print('donwload_path',donwload_path)
        actions.move_to_element(donwload_path).click().perform()
        print('donwload_path element clicked successfully')
        time.sleep(5)
        download_pdf = os.path.join(download_dir, expected_filename)
    return download_pdf
    # Wait for download to complete (you might need to adjust the sleep time based on your connection speed)
    
def clean_csv_data(df):
    """
    Remove specific unwanted rows and completely empty rows from the DataFrame.

    Parameters:
    - df (DataFrame): The input DataFrame to be cleaned.

    Returns:
    - DataFrame: The cleaned DataFrame.
    """
    # Define unwanted texts to be removed
    unwanted_texts = ["LIST LAST UPDATED 7/5/2024", "ALL FUNDS LISTED ARE STILL HELD BY CLERK"]
    
    # Convert unwanted texts to lowercase for case-insensitive matching
    unwanted_texts = [text.lower() for text in unwanted_texts]

    # Create a boolean mask to identify rows containing unwanted texts
    def contains_unwanted_text(row):
        # Convert all cell values in the row to lowercase and check for unwanted texts
        row_lower = row.astype(str).str.lower()
        return row_lower.str.contains('|'.join(unwanted_texts)).any()

    # Apply the mask to remove unwanted rows
    mask_unwanted = df.apply(contains_unwanted_text, axis=1)
    cleaned_df = df[~mask_unwanted]
    
    # Remove completely empty rows
    cleaned_df = cleaned_df.dropna(how='all')
    
    return cleaned_df

def pdf_to_single_csv(pdf_path, csv_path, exctract_data):
    """
    Convert tables in a PDF to a single CSV file, cleaning specific unwanted rows,
    empty rows, and keeping only specified columns.

    Parameters:
    - pdf_path (str): The path to the input PDF file.
    - csv_path (str): The path where the CSV file will be saved.
    """
    try:
        all_tables = []

        # Open the PDF file
        with pdfplumber.open(pdf_path) as pdf:
            # Iterate over all pages in the PDF
            for page in pdf.pages:
                # Extract tables from the page
                tables = page.extract_tables()

                # Append each table to the all_tables list
                for table in tables:
                    df = pd.DataFrame(table[1:], columns=table[0])  # table[0] is the header row
                    all_tables.append(df)

        # Concatenate all DataFrames into one DataFrame
        if all_tables:
            combined_df = pd.concat(all_tables, ignore_index=True)
            if exctract_data:
                # Select only the desired columns
                columns_of_interest = ["PROPERTY OWNER & ADDRESS", "APPLICATION #", "AMOUNT OF SURPLUS", "SALE DATE","PARCEL #"]
                # Ensure the columns of interest are present in the DataFrame
                combined_df = combined_df[columns_of_interest]
                column_mapping = {
                    "PROPERTY OWNER & ADDRESS": "Property Address",
                    "APPLICATION #": "Applicant/Purchaser (If available)",
                    "AMOUNT OF SURPLUS": "Surplus amount",
                    "SALE DATE":"Sale Date",
                    "PARCEL #":"Parcel ID"
                    # Add additional mappings if needed
                }
                
                # Rename columns based on the mapping
                try:
                    combined_df.rename(columns=column_mapping, inplace=True)
                except Exception as e:
                    print(f"Error renaming columns: {e}")
                    # If renaming fails, list columns that couldn't be renamed
                    print("Columns in DataFrame:", combined_df.columns)
                required_columns = [
                    "Prior Owner",
                    "Opening Bid",
                ]
                for col in required_columns:
                    if col not in combined_df.columns:
                        combined_df[col] = 'Nill'
            # Clean the DataFrame by removing unwanted rows and empty rows
            cleaned_df = clean_csv_data(combined_df)
            # Save the cleaned DataFrame to a CSV file
            # return cleaned_df
            cleaned_df.to_csv(csv_path, index=False)
            print(f"Filtered and cleaned data saved to {csv_path}")
        else:
            print("No tables found in the PDF.")

    except Exception as e:
        print(f"An error occurred: {e}")





if __name__ == "__main__":
    # Create the download directory if it does not exist
    download_dir = os.path.join(os.getcwd(), "downloads")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    output = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output):
        os.makedirs(output)
    output_csv = os.path.join(output, 'get_the_surplus_funds_list.csv')
    # Initialize the WebDriver
    driver = initialize_driver(download_dir)
    # Open the target webpage
    driver.get("https://www.sumterclerk.com/surplus-funds-list")
    
    # Define the XPath for the download link
    xpath = '/html/body/div[3]/main/div[2]/div/section/div/div/div/div/div/div[1]/ul[2]/li[2]/strong/a'
    # Download the PDF
    expected_filename = "Tax Deed Surplus.pdf"
    downlaod_file = download_pdf(driver, xpath,expected_filename)
    print('downlaod_file', downlaod_file)
    # print('data', data)
    pdf_to_single_csv(downlaod_file,output_csv,True)
    delete_path(downlaod_file)
    delete_folder(download_dir)
    driver.quit()