import csv
import os
import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from site_scraper.webdriver import InitializeDriver

driver_initializer = InitializeDriver()

def scrape_delaware_county_court_data():
    # Initialize the WebDriver
    driver = webdriver.Chrome()
    driver = driver_initializer.initialize_chrome()
    driver.get("https://courts.delaware.gov/superior/rightfulowner/sale_a_b1.aspx#b")
    sleep(6)

    # Locate the table
    table = driver.find_element(By.CLASS_NAME, 'table')

    # Extract table headers
    headers = [header.text for header in table.find_elements(By.XPATH, './/thead//th')]

    # Extract table rows
    rows = []
    print("Start scraping please wait for a few seconds")
    for i in range(ord('a'), ord('z') + 1):
        dropdown = driver.find_element(By.XPATH, '//*[@id="main_content"]/select')
        dropdown.send_keys(chr(i))
        sleep(3)
        # Locate the table
        table = driver.find_element(By.CLASS_NAME, 'table')
        for row in table.find_elements(By.XPATH, './/tbody//tr'):
            cells = [cell.text for cell in row.find_elements(By.XPATH, './/td')]
            rows.append(cells)

    # Save data to CSV
    csv_file_path = 'table_data.csv'
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # Write the header row
        writer.writerows(rows)    # Write the data rows
    driver.quit()
    return csv_file_path

def process_csv_file(csv_file_path):
    # Define the columns of interest
    columns_of_interest = [
        "Property Address", "Prior Owner", "Parcel ID", "Opening Bid",
        "Sale Price", "Surplus amount", "Sale Date", "Case Number",
        "Applicant/Purchaser"
    ]

    # Mapping rules
    mapping = {
        "Property Address": "Address (Sheriff's Sale)",
        "Prior Owner": "First Name",
        "Parcel ID": "Parcel ID",
        "Opening Bid": "Opening Bid",
        "Sale Price": "Sale Price",
        "Surplus amount": "Court-Held\nAmount",
        "Sale Date": "Sale Date",
        "Case Number": "Case Number",
        "Applicant/Purchaser": "Applicant/Purchaser"
    }

    # Load the original CSV file
    df = pd.read_csv(csv_file_path)
    df_cleaned = df.drop_duplicates()
    df_cleaned.to_csv(csv_file_path, index=False)

    # Create a new DataFrame with the columns of interest
    new_df = pd.DataFrame(columns=columns_of_interest)
    county_name = 'courts.delaware'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'table_data_{county_name}_{timestamp}.csv'

    # Map and insert data
    for new_col, old_col in mapping.items():
        if old_col in df.columns:
            if new_col == "Prior Owner":
                if 'First Name' in df.columns:
                    new_df[new_col] = df['First Name'].astype(str)
                else:
                    new_df[new_col] = None
            else:
                new_df[new_col] = df[old_col]
        else:
            new_df[new_col] = None

    # Fill missing values
    new_df = new_df.fillna('null')

    # Output folder path relative to the current working directory
    output_folder = os.path.join(os.getcwd(), 'output_folder')
    os.makedirs(output_folder, exist_ok=True)
    new_filename = os.path.join(output_folder, filename)

    # Debug: Print paths for verification
    print(f"Output folder path: {output_folder}")
    print(f"Saving new file to: {new_filename}")

    # Save the new DataFrame to a new CSV file
    new_df.to_csv(new_filename, index=False)

    # Cleanup: Remove the file after processing
    os.remove('table_data.csv')
    return new_filename
