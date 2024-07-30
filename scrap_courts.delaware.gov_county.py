import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import pandas as pd
import os
from datetime import datetime
import time

def initialize_webdriver():
    """Initialize the WebDriver."""
    driver = webdriver.Chrome()
    return driver

def scrape_data(driver):
    start_time = time.time()
    """Scrape data from the webpage and save to a CSV file."""
    driver.get("https://courts.delaware.gov/superior/rightfulowner/sale_a_b1.aspx#b")
    sleep(6)

    # Locate the table
    table = driver.find_element(By.CLASS_NAME, 'table')

    # Extract table headers
    headers = [header.text for header in table.find_elements(By.XPATH, './/thead//th')]

    # Extract table rows
    rows = []
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
    csv_file = 'table_data.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # Write the header row
        writer.writerows(rows)    # Write the data rows
    
    end_time = time.time()
    total_time = end_time - start_time
    print() 
    print(f"Total execution time: {total_time:.2f} seconds")
    return csv_file

def process_csv(csv_file):
    """Process the CSV file to clean and map the data."""
    # Define the columns of interest and mapping rules
    columns_of_interest = [
        "Last Name", "First Name", "Address", "Court Held Amount",
        "Sale Date", "Case Number"
    ]

    mapping = {
        "Last Name": "Last Name or Business Name",
        "First Name": "First Name",
        "Address": "Address (Sheriff's Sale)",
        "Court Held Amount": "Court-Held\nAmount",
        "Sale Date": "Sale Date",
        "Case Number":"Case Number"
    }

    # Load the original CSV file and remove data redundancy
    df = pd.read_csv(csv_file)
    df_cleaned = df.drop_duplicates()
    
    # Create a new DataFrame with the columns of interest
    new_df = pd.DataFrame(columns=columns_of_interest)

    # Map and extract relevant data into the new DataFrame
    for column in columns_of_interest:
        original_column_name = mapping.get(column, column)
        # if original_column_name in df_cleaned.columns:
        new_df[column] = df_cleaned[original_column_name]
        # else:
        #     new_df[column] = 'null'

    # Fill missing values and remove duplicates
    new_df = new_df.drop_duplicates()

    return new_df

def save_new_csv(new_df):
    """Save the processed data to a new CSV file."""
    # Create output folder if it doesn't exist
    output_folder = 'output_folder'
    os.makedirs(output_folder, exist_ok=True)

    # Save the new DataFrame to a new CSV file
    county_name = 'courts.delaware'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    new_filename = os.path.join(output_folder, f'new_table_data_{county_name}_{timestamp}.csv')
    new_df.to_csv(new_filename, index=False)
    
    return new_filename

def clean_up(csv_file):
    """Remove the original CSV file."""
    if os.path.exists(csv_file):
        os.remove(csv_file)

def main():
    driver = initialize_webdriver()
    csv_file = scrape_data(driver)
    driver.quit()

    new_df = process_csv(csv_file)
    new_filename = save_new_csv(new_df)
    clean_up(csv_file)

    print(f"New CSV file saved to: {new_filename}")

if __name__ == "__main__":
    main()
