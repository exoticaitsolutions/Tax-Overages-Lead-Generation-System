import csv
import os
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.common.action_chains import ActionChains
import pdfplumber
import pandas as pd
from config import DOWNLOAD_FOLDER
from utils import delete_folder, delete_path, format_location, print_the_output_statement

# Utility function to scrape table data
def scrape_table(driver, dropdown_xpath, table_class_name, alphabet_range):
    rows = []
    for i in alphabet_range:
        driver.find_element(By.XPATH, dropdown_xpath).send_keys(chr(i))
        time.sleep(3)
        table = driver.find_element(By.CLASS_NAME, table_class_name)
        rows.extend([cell.text for row in table.find_elements(By.XPATH, './/tbody//tr')
                            for cell in row.find_elements(By.XPATH, './/td')])
    return rows

# New Castle County Delaware Function 

def Scrap_New_Castle_County_Delaware(driver_instance, country_name, country_url, output_text):
    print_the_output_statement(output_text, f"Opening the site {country_url}")
    try:
        driver_instance.get(country_url)
        time.sleep(5)
        table = driver_instance.find_element(By.CLASS_NAME, 'table')
        headers = [header.text for header in table.find_elements(By.XPATH, './/thead//th')]
        
        rows = scrape_table(driver_instance, '//*[@id="main_content"]/select', 'table', range(ord('a'), ord('z') + 1))
        
        with open('table_data.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)

        columns_of_interest = [
            "Property Address", "Prior Owner", "Parcel ID", "Opening Bid",
            "Sale Price", "Surplus amount", "Sale Date", "Case Number",
            "Applicant/Purchaser"
        ]
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

        df = pd.read_csv('table_data.csv').drop_duplicates()
        new_df = pd.DataFrame({new_col: df[old_col] if old_col in df.columns else None
                               for new_col, old_col in mapping.items()})

        new_df['Prior Owner'] = df['First Name'].astype(str) if 'First Name' in df.columns else None
        new_df = new_df.fillna('').iloc[:, 1:]  # Drop the first column if needed
        delete_path('table_data.csv')
        return True, "Data Scrapped Successfully", format_location(country_name), new_df
    except (NoSuchElementException, StaleElementReferenceException, WebDriverException, ValueError) as e:
        error_message = f"Error occurred: {e}"
        print(error_message)
        print_the_output_statement(output_text, error_message)
        return False, error_message, "", ""
    finally:
        if "driver_instance" in locals():
            driver_instance.quit()


# Sumter County Florida Function
def Scrap_Sumter_County_Florida(driver_instance, country_name, country_url, output_text):
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    pdf_filename = "Tax Deed Surplus.pdf"
    pdf_path = os.path.join(DOWNLOAD_FOLDER, pdf_filename)
    all_tables = []
    try:
        print_the_output_statement(output_text, f"Opening the site {country_url}")
        if not os.path.exists(pdf_path):
            driver_instance.get(country_url)
            print_the_output_statement(output_text, f"Scraping started for {country_name}. Please wait a few minutes.")
            download_button_xpath = "/html/body/div[3]/main/div[2]/div/section/div/div/div/div/div/div[1]/ul[2]/li[2]/strong/a"
            actions = ActionChains(driver_instance)
            download_element = driver_instance.find_element(By.XPATH, download_button_xpath)
            actions.move_to_element(download_element).click().perform()
            time.sleep(10)  # Wait for download to complete
            while not os.path.exists(pdf_path):
                print(f"Waiting for {pdf_filename} to be downloaded...")
                time.sleep(5)
        print('pdf_path', pdf_path)
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
        if not all_tables:
            if "driver_instance" in locals():
                driver_instance.quit()
            return False, "No tables found in the PDF.", "", ""
        # Combine all tables into one DataFrame
        combined_df = pd.concat(all_tables, ignore_index=True).dropna(how="all")
        combined_df = combined_df[
            combined_df.apply(
                lambda row: row.astype(str).str.strip().ne("").any(), axis=1
            )
        ]
        combined_df = combined_df.fillna("Nill")
        # Check for specific columns
        if "PROPERTY OWNER" in combined_df.columns and "PROPERTY ADDRESS" in combined_df.columns:
            # Ensure that 'PROPERTY OWNER' is not empty and 'PROPERTY ADDRESS' has data
            combined_df = combined_df[
                combined_df["PROPERTY OWNER"].str.strip() != ""
            ]
            combined_df = combined_df[
                combined_df["PROPERTY ADDRESS"].str.strip() != ""
            ]
        # # Process rows to handle empty rows by filling with "Nill"
        return False, "Data Scrapped Successfully", format_location(country_name), 'merged_df'
    except (NoSuchElementException, StaleElementReferenceException, WebDriverException, ValueError) as e:
        error_message = "Internal Error Occurred while running application. Please Try Again!!"
        print(error_message)
        print_the_output_statement(output_text, error_message)
        return False, error_message, "", ""
    finally:
        if "driver_instance" in locals():
            driver_instance.quit()
