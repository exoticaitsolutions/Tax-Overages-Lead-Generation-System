import csv
import os
import random
import re
import time
import pandas as pd
import pdfplumber
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from PyPDF2 import PdfReader
from config import DOWNLOAD_FOLDER
from utils import (
    check_file_downloaded,
    delete_folder,
    delete_path,
    print_the_output_statement,
)


def scrap_courts_delaware_gov_county(driver_instance, country_name, country_url, output_text):
    print("scrap_courts_delaware_gov_county")
    print_the_output_statement(output_text, f"Opening the site {country_url}")

    try:
        driver_instance.get(country_url)
        print_the_output_statement(
            output_text,
            f"Scraping started for {country_name}. Please wait a few minutes."
        )
        time.sleep(5)  # Allow time for page to fully load

        # Extract table headers
        table = driver_instance.find_element(By.CLASS_NAME, "table")
        headers = [header.text for header in table.find_elements(By.XPATH, ".//thead//th")]

        rows = []
        for i in range(ord("a"), ord("c") + 1):  # Loop through dropdown values 'a' to 'c'
            dropdown = driver_instance.find_element(By.XPATH, '//*[@id="main_content"]/select')
            dropdown.send_keys(chr(i))
            time.sleep(3)  # Wait for table data to update

            # Extract table rows
            table = driver_instance.find_element(By.CLASS_NAME, "table")
            for row in table.find_elements(By.XPATH, ".//tbody//tr"):
                cells = [cell.text for cell in row.find_elements(By.XPATH, ".//td")]
                # Remove single alphabetic data entries (often empty cells or headers)
                cells = [data for data in cells if not (len(data) == 1 and data.isalpha())]
                rows.append(cells)

        # Save scraped data to CSV
        csv_file = "table_data.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)

        # Define columns of interest and mapping rules
        columns_of_interest = [
            "Last Name",
            "First Name",
            "Address",
            "Court Held Amount",
            "Sale Date",
            "Case Number",
        ]

        mapping = {
            "Last Name": "Last Name or Business Name",
            "First Name": "First Name",
            "Address": "Address (Sheriff's Sale)",
            "Court Held Amount": "Court-Held\nAmount",
            "Sale Date": "Sale Date",
            "Case Number": "Case Number",
        }

        # Load CSV file into DataFrame and clean data
        df = pd.read_csv(csv_file)
        df_cleaned = df.drop_duplicates()

        # Create new DataFrame with columns of interest
        new_df = pd.DataFrame()
        for column in columns_of_interest:
            original_column_name = mapping.get(column, column)
            if original_column_name in df_cleaned.columns:
                new_df[column] = df_cleaned[original_column_name]
            else:
                new_df[column] = "Nill"  # Fill missing columns with "Nill"

        new_df = new_df.drop_duplicates()

        delete_path(csv_file)
        return True, "Scraping completed successfully", "courts_delaware", new_df

    except (NoSuchElementException, StaleElementReferenceException, WebDriverException, ValueError) as e:
        error_message = f"Error occurred: {e}"
        print(error_message)
        print_the_output_statement(output_text, error_message)
        return False, error_message, "", ""
    finally:
        if "driver_instance" in locals():
            driver_instance.quit()


def scrap_sumterclerk_county(driver_instance, country_name, country_url, output_text):
    print("scrap_sumterclerk_county")
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    all_tables = []
    pdf_filename = "Tax Deed Surplus.pdf"
    pdf_path = os.path.join(DOWNLOAD_FOLDER, pdf_filename)

    print_the_output_statement(output_text, f"Opening the site {country_url}")

    try:
        driver_instance.get(country_url)
        print_the_output_statement(
            output_text,
            f"Scraping started for {country_name}. Please wait a few minutes."
        )

        # Check if PDF is already downloaded
        if not check_file_downloaded(DOWNLOAD_FOLDER, pdf_filename):
            # Click to download the PDF
            download_button_xpath = "/html/body/div[3]/main/div[2]/div/section/div/div/div/div/div/div[1]/ul[2]/li[2]/strong/a"
            actions = ActionChains(driver_instance)
            download_element = driver_instance.find_element(By.XPATH, download_button_xpath)
            actions.move_to_element(download_element).click().perform()
            time.sleep(5)  # Wait for download to start

            # Wait for download to complete
            wait = WebDriverWait(driver_instance, 30)
            download_path = wait.until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[4]/div/div[3]/div[2]/div[2]/div[2]"))
            )
            actions.move_to_element(download_path).click().perform()
            time.sleep(5)

        # Read and process the PDF
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    df = df.apply(lambda x: x.str.replace("LIST LAST UPDATED 7/5/2024", "", regex=False) if x.dtype == "object" else x)
                    df = df.apply(lambda x: x.str.replace("ALL FUNDS LISTED ARE STILL HELD BY CLERK", "", regex=False) if x.dtype == "object" else x)
                    df = df.dropna(how="all")
                    df = df[df.apply(lambda row: row.astype(str).str.strip().ne("").any(), axis=1)]
                    all_tables.append(df)

        if not all_tables:
            if "driver_instance" in locals():
                driver_instance.quit()
            return False, "No tables found in the PDF.", "", ""

        # Combine all tables into one DataFrame
        combined_df = pd.concat(all_tables, ignore_index=True).dropna(how="all")
        combined_df = combined_df[combined_df.apply(lambda row: row.astype(str).str.strip().ne("").any(), axis=1)]
        combined_df = combined_df.fillna("Nill")

        # Process rows to handle empty rows by filling with "Nill"
        even_rows = combined_df.iloc[::2].reset_index(drop=True)
        odd_rows = combined_df.iloc[1::2].reset_index(drop=True)
        odd_rows = odd_rows.reindex(even_rows.index, fill_value=pd.NA)
        merged_df = pd.concat([even_rows, odd_rows.add_suffix("_Odd")], axis=1)

        # Rename columns and handle missing columns
        column_mapping = {
            "PROPERTY OWNER & ADDRESS": "Property Owner",
            "PROPERTY OWNER & ADDRESS_Odd": "Property Address",
            "PARCEL #": "Parcel #",
            "AMOUNT OF SURPLUS": "Amount of Surplus",
            "SALE DATE": "Sale Date",
            "APPLICATION DATE": "Application Date",
        }
        merged_df = merged_df.rename(columns=column_mapping)

        final_columns = [
            "Property Owner",
            "Property Address",
            "Sale Date",
            "Amount of Surplus",
            "Parcel #",
            "Application Date",
        ]
        for col in final_columns:
            if col not in merged_df.columns:
                merged_df[col] = "Nill"
        merged_df = merged_df[final_columns]
        merged_df = merged_df.replace({pd.NA: "Nill", pd.NaT: "Nill"})  # Handle missing values

        # Clean up
        delete_path(pdf_path)
        delete_folder(DOWNLOAD_FOLDER)

        return True, "Data Scrapped Successfully", "sumterclerk", merged_df

    except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
        print(f"Error occurred: {e}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, "Internal Error Occurred while running application. Please Try Again!!", "", ""
    except (pd.errors.EmptyDataError, pd.errors.ParserError, ValueError, OSError, IOError) as e:
        print(f"Error occurred: {e}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, "Internal Error Occurred while running application. Please Try Again!!", "", ""


def scrap_polkcountyclerk_net_county(driver_instance, country_name, country_url, output_text):
    print_the_output_statement(output_text, f"Opening the site {country_url}")

    try:
        driver_instance.get(country_url)
        time.sleep(5)
        print_the_output_statement(
            output_text,
            f"Scraping started for {country_name}. Please wait a few minutes."
        )

        # Locate the box containing the table
        box = driver_instance.find_element(By.XPATH, '//*[@id="isPasted"]')
        print("isPasted element is found")

        # Locate the table within the box
        table = box.find_element(By.TAG_NAME, "tbody")
        title = box.find_element(By.TAG_NAME, "thead")

        # Extract headers
        header = [cell.text for cell in title.find_elements(By.TAG_NAME, "th") if cell.text]
        print("Header extracted:", header)

        # Scroll to ensure all data is loaded
        driver_instance.execute_script("window.scrollBy(0, 300);")
        print("Scrolling In Progress............")

        # Extract data rows
        all_data = []
        rows = table.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = [cell.text.replace(",", "") for cell in cells]
            all_data.append(row_data)

        # Create DataFrame
        all_data.insert(0, header)
        merged_df = pd.DataFrame(all_data[1:], columns=all_data[0])

        # Select final columns
        final_columns = [
            "Previous Owner of Record",
            "Sale Date",
            "Amount Available",
            "Property ID Number",
            "Tax Deed Number",
            "Certificate Number"
        ]
        merged_df = merged_df[final_columns]
        # Handle missing values
        merged_df = merged_df.fillna("Nill")
        return True, "Data Scrapped Successfully", "PolkCountyclerk", merged_df
    except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
        print(f"Error occurred: {e}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, "Internal Error Occurred while running application. Please Try Again!!", "", ""


def scrap_shasta_california_county(driver_instance, country_name, country_url, output_text):
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    print_the_output_statement(output_text, f"Opening the site {country_url}")

    pdf_filename = "tax_sale_results_1.pdf"
    pdf_path = os.path.join(DOWNLOAD_FOLDER, pdf_filename)
    pdf_url = 'https://www.shastacounty.gov/sites/default/files/fileattachments/tax_collector/page/2691/tax_sale_results_1.pdf'

    try:
        # Download the PDF if not already downloaded
        if not check_file_downloaded(DOWNLOAD_FOLDER, pdf_filename):
            driver_instance.get(pdf_url)
            time.sleep(5)  # Adjust sleep time if needed

        # Read and parse the PDF
        pdf_reader = PdfReader(open(pdf_path, 'rb'))
        pdf_text = '\n'.join(page.extract_text() for page in pdf_reader.pages)

        # Regex pattern to match the table rows
        pattern = re.compile(
            r'(\w+)\s+([\d-]+)\s+(.+?)\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(REDEEMED|WITHDRAWN|NO SALE|\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(.*)?'
        )
        data = [
            match.groups()[1:6]  # Extract groups from regex match
            for line in pdf_text.split('\n')
            if (match := pattern.match(line))
        ]
        # Create DataFrame
        columns = ['Parcel Number', 'Assessee Name', 'Minimum Bid Price', 'Sale Price', 'Excess Proceeds']
        merged_df = pd.DataFrame(data, columns=columns)
        # Clean up
        delete_path(pdf_path)
        delete_folder(DOWNLOAD_FOLDER)
        return True, "Data Scrapped Successfully", "shasta_county_california", merged_df
    except (pd.errors.EmptyDataError, pd.errors.ParserError, ValueError, OSError, IOError,
            NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
        print("Internal Error Occurred while running application. Please Try Again!!")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, "Internal Error Occurred while running application. Please Try Again!!", "", ""

    