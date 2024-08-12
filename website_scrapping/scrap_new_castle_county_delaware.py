import csv
import os
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
import pandas as pd
from utils import (
    delete_path,
    format_location,
    print_the_output_statement,
)

def split_and_update_address(address):
    if pd.isna(address):
        return pd.Series([None, None])
    
    # Split address from the last comma
    parts = address.rsplit(',', 2)
    
    if len(parts) == 3:
        remaining_address = parts[0].strip()
        city = parts[1].strip()
        state_zip = parts[2].strip()
        # Separate state and zip code from the state_zip part
        state_zip_parts = state_zip.split(' ', 1)
        if len(state_zip_parts) == 2:
            zip_code = state_zip_parts[1].strip()
        else:
            zip_code = state_zip_parts[0].strip()
    elif len(parts) == 2:
        remaining_address = parts[0].strip()
        city_zip = parts[1].strip()
        city_parts = city_zip.split(' ')
        city = ' '.join(city_parts[:-1]).strip()
        zip_code = city_parts[-1].strip()
    else:
        remaining_address = address
        city = None
        zip_code = None
    
    # Validate and clean Zip Code to ensure it's numeric
    if zip_code and zip_code.isdigit():
        return pd.Series([remaining_address, city, f"{zip_code}"])
    else:
        return pd.Series([remaining_address, city])

def scrap_new_castle_county_delaware(
    driver_instance, country_name, country_url, output_text
):
    print_the_output_statement(output_text, f"Opening the site {country_url}", False)
    try:
        driver_instance.get(country_url)
        time.sleep(5)
        print_the_output_statement(
            output_text,
            f"Scraping started for {country_name}. Please wait a few minutes.",False
        )
        time.sleep(6)
        # Locate the table
        table = driver_instance.find_element(By.CLASS_NAME, "table")
        header_rows = table.find_elements(By.TAG_NAME, 'tr')
        header_data = []
        if header_rows:
            header_cells = header_rows[0].find_elements(By.TAG_NAME, 'td')
            for cell in header_cells:
                strong_tag = cell.find_element(By.TAG_NAME, 'strong')
                if strong_tag:
                    header_text = strong_tag.text.strip().replace('\n', ' ')
                    header_data.append(header_text)

        # Extract table rows
        rows = []
        for i in range(ord("a"), ord("z") + 1):
            current_letter = chr(i)
            print(f"Data scraping for the letter: {current_letter}")
            dropdown = driver_instance.find_element(By.XPATH, '//*[@id="main_content"]/select')
            dropdown.send_keys(chr(i))
            time.sleep(3)
            # Locate the table
            table = driver_instance.find_element(By.CLASS_NAME, 'table')
            for row in table.find_elements(By.XPATH, './/tbody//tr'):
                cells = [cell.text for cell in row.find_elements(By.XPATH, './/td')]
                if len(cells) > 1 and cells != ['No Current Records']:
                    rows.append(cells)

        # Save scraped data to CSV
        csv_file = "table_data.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(header_data)
            writer.writerows(rows)
        # Load data to DataFrame
        df = pd.read_csv(csv_file)
        # Check if the last element or 'Case Number' is empty
        last_element_empty = df.iloc[:, -1].isna()
        case_number_empty = df['Case Number'].isna()

        # Get rows where either the last element or 'Case Number' is empty
        empty_rows = last_element_empty | case_number_empty

        # Store the current values temporarily
        temp_case_number = df.loc[empty_rows, 'Case Number']
        temp_sale_date = df.loc[empty_rows, 'Sale Date']
        temp_court_held_amount = df.loc[empty_rows, 'Court-Held Amount']
        temp_address = df.loc[empty_rows, 'Address (Sheriff\'s Sale)']

        # Perform the replacements
        df.loc[empty_rows, 'Case Number'] = temp_sale_date
        df.loc[empty_rows, 'Sale Date'] = temp_court_held_amount
        df.loc[empty_rows, 'Court-Held Amount'] = temp_address
        df.loc[empty_rows, 'Address (Sheriff\'s Sale)'] = df.loc[empty_rows, 'First Name']
        df.loc[empty_rows, 'First Name'] = "Null"

        # Rename columns as per the mapping
        df.rename(columns={
            'Last Name or Business Name': 'Last Name',
            'First Name': 'First Name',
            'Address (Sheriff\'s Sale)': 'Address',
            'Court-Held Amount': 'Court Held Amount',
            'Sale Date': 'Sale Date',
            'Case Number': 'Case Number'
        }, inplace=True)
        # Apply the function to split the Address and update the Address column
        df[['Address', 'City', 'Zip Code']] = df['Address'].apply(split_and_update_address)

        # Remove duplicate rows
        df_cleaned = df.drop_duplicates()

        # Drop the last row
        df_cleaned = df_cleaned.iloc[:-1]
        df_cleaned.to_csv('delaware_website.csv', index=False)
        df = pd.read_csv('delaware_website.csv')
        df_cleaned = df[df['Last Name'] != 'Last Name or Business Name']
        df_cleaned = df_cleaned.dropna(how='all')
        df_cleaned.to_csv('final_delaware_website.csv', index=False)
        df_cleaned = df_cleaned[['Last Name', 'First Name', 'Address', 'City', 'Zip Code', 'Court Held Amount', 'Sale Date', 'Case Number']]
        # Save to CSV with the desired column order
        # df_cleaned.to_csv('final_delaware_website_data.csv', index=False)
        delete_path('final_delaware_website.csv')
        delete_path('table_data.csv')
        delete_path('delaware_website.csv')
        return (
            True,
            "Data Scrapped Successfully",
            format_location(country_name),
            df_cleaned,
        )
    except (
        NoSuchElementException,
        StaleElementReferenceException,
        WebDriverException,
        ValueError,
    ) as e:
        error_message = f"Error occurred: {e}"
        print(error_message)
        print_the_output_statement(output_text, error_message)
        return False, error_message, "", ""
    finally:
        if "driver_instance" in locals():
            driver_instance.quit()