import csv
import os
import re
import sys
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pdfplumber
import pandas as pd
from PyPDF2 import PdfReader
from config import DOWNLOAD_FOLDER
from utils import check_file_downloaded, delete_folder, delete_path, format_location, print_the_output_statement

# Utility function to scrape table data
def scrape_table(driver, dropdown_xpath, table_class_name, alphabet_range):
    rows = []
    for i in alphabet_range:
        current_letter = chr(i)
        sys.stdout.write('\r' + f"Data scraping for the letter: {current_letter}")
        sys.stdout.flush()
        time.sleep(1)
        driver.find_element(By.XPATH, dropdown_xpath).send_keys(chr(i))
        time.sleep(3)
        table = driver.find_element(By.CLASS_NAME, table_class_name)
        for row in table.find_elements(By.XPATH, './/tbody//tr'):
            cells = [cell.text for cell in row.find_elements(By.XPATH, './/td')]
            rows.append(cells)
    return rows

# New Castle County Delaware Function 
def scrap_new_castle_county_delaware(driver_instance, country_name, country_url, output_text):
    print_the_output_statement(output_text, f"Opening the site {country_url}")
    try:
        driver_instance.get(country_url)
        print_the_output_statement( output_text, f"Scraping started for {country_name}. Please wait a few minutes.",)
        time.sleep(5)
        table = driver_instance.find_element(By.CLASS_NAME, 'table')
        headers = [header.text for header in table.find_elements(By.XPATH, './/thead//th')]
        rows = scrape_table(driver_instance, '//*[@id="main_content"]/select', 'table', range(ord('a'), ord('z') + 1))
        # Handle rows with varying lengths
        max_len = max(len(row) for row in rows)
        rows = [row + [''] * (max_len - len(row)) for row in rows]  # Pad rows to have the same length

        with open('table_data.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)
        print('Data Scrapp successfully and saving  to csv file ')
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
def scrap_sumter_county_florida(driver_instance, country_name, country_url, output_text):
    print("scrap_sumterclerk_county")
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    all_tables = []
    pdf_filename = "Tax Deed Surplus.pdf"
    pdf_path = os.path.join(DOWNLOAD_FOLDER, pdf_filename)

    print_the_output_statement(output_text, f"Opening the site {country_url}")

    try:
        print_the_output_statement(
            output_text,
            f"Scraping started for {country_name}. Please wait a few minutes.",
        )
        
        

        # Check if PDF is already downloaded
        if not check_file_downloaded(DOWNLOAD_FOLDER, pdf_filename):
            driver_instance.get('https://docs.google.com/viewer?url=https://docs.google.com/spreadsheets/d/1uW4muYX69nJvSNPqLt93jf0IYcNWxzpA3HEjUxIZoz4/export?format=pdf')
            time.sleep(5)
            driver_instance.save_screenshot(os.path.join(DOWNLOAD_FOLDER, 'screenshot.png'))
            # Click to download the PDF
            # download_element = driver_instance.find_element(By.CSS_SELECTOR, 'a[title="Downloadable PDF"]')
            # download_element.click()            
            #   # Wait for download to start
            start_time = time.time()
            # Wait for download to complete
            wait = WebDriverWait(driver_instance, 60)
            download_path = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "/html/body/div[1]/div[4]/div/div[3]/div[2]/div[2]/div[2]",
                    )
                )
            )
            actions = ActionChains(driver_instance)
            actions.move_to_element(download_path).click().perform()
            end_time = time.time()
            download_duration = end_time - start_time
            print(f'Downloading the pdf in the {pdf_path}')
            print(f"Download completed in {download_duration:.2f} seconds")
            time.sleep(5)
            print(f'Downloaded  the pdf in the {pdf_path} then the data scrapping in the progress and save into the csv' )
        # Read and process the PDF
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
        merged_df = merged_df.replace(
            {pd.NA: "Nill", pd.NaT: "Nill"}
        )  # Handle missing values

        # Clean up
        delete_path(pdf_path)
        delete_folder(DOWNLOAD_FOLDER)

        return True, "Data Scrapped Successfully", "sumterclerk", merged_df

    except (
        NoSuchElementException,
        StaleElementReferenceException,
        WebDriverException,
    ) as e:
        print(f"Error occurred: {e}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return (
            False,
            "Internal Error Occurred while running application. Please Try Again!!",
            "",
            "",
        )
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        ValueError,
        OSError,
        IOError,
    ) as e:
        print(f"Error occurred: {e}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return (
            False,
            "Internal Error Occurred while running application. Please Try Again!!",
            "",
            "",
        )
    finally:
        if "driver_instance" in locals():
            driver_instance.quit()


# Sarasota County Florida Function

def wait_and_click(driver, locator_type, locator_value, wait_time=10):
    WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable((locator_type, locator_value))).click()

def extract_data_from_row(driver, row):
    try:
        row.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.btn.btn-back-to-case-list')))

        # Extract data from the detail page
        property_address = driver.find_element(By.XPATH, '//*[@id="summarySummary"]/table/tbody/tr[4]/td[2]').text
        surplus_amount = driver.find_element(By.XPATH, '//*[@id="publicSection"]/div[2]/table[2]/tbody/tr/td[4]/strong').text

        # Extract parties data
        parties_data = []
        wait_and_click(driver, By.XPATH, '//a[@data-handler="dspCaseParties"]')
        parties_table = driver.find_element(By.CLASS_NAME, 'table-public')
        parties_rows = parties_table.find_elements(By.TAG_NAME, 'tr')[1:]  # Skip header row
        for party_row in parties_rows:
            parties_data.append([col.text for col in party_row.find_elements(By.TAG_NAME, 'td')])

        # Extract surplus amount
        wait_and_click(driver, By.XPATH, '//a[@data-handler="dspDisbursements"]')
        surplus_amount = driver.find_element(By.XPATH, '//*[@id="publicSection"]/div[2]/table[2]/tbody/tr/td[4]/strong').text

        # Click the back button to return to the case list
        wait_and_click(driver, By.CSS_SELECTOR, 'button.btn.btn-back-to-case-list')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'county-setup')))
        time.sleep(2)  # Ensure full page load

        return property_address, parties_data, surplus_amount
    except Exception as e:
        print(f"Error processing row: {e}")
        return '', [], ''

def scrap_sarasota_county_florida(driver, country_name, country_url, output_text):
    try:
        print_the_output_statement(output_text, f"Opening the site {country_url}")
        driver.get(country_url)
        print_the_output_statement(output_text, f"Scraping started for {country_name}. Please wait a few minutes.")
        time.sleep(5)
        # Initial filtering and navigation
        wait_and_click(driver, By.ID, 'filterButtonStatus')
        time.sleep(2)
        actions = ActionChains(driver)
        actions.move_to_element(driver.find_element(By.ID, 'caseStatus2')).perform()
        wait_and_click(driver, By.XPATH, '//a[@data-statusid="1011" and @data-parentid="2"]')
        wait_and_click(driver, By.ID, 'filterButtonStatus')
        wait_and_click(driver, By.XPATH, '//button[@class="btn btn-default dropdown-toggle" and @data-id="filterBalanceType"]')
        time.sleep(2)
        wait_and_click(driver, By.XPATH, '/html/body/div[8]/div/ul/li[2]/a/span')
        time.sleep(3)
        wait_and_click(driver, By.XPATH, '//button[@class="btn btn-success filters-submit"]')
        time.sleep(10)
        # Process rows
        table = driver.find_element(By.ID, 'county-setup')
        rows = table.find_elements(By.TAG_NAME, 'tr')
        header = [col.text for col in rows[0].find_elements(By.TAG_NAME, 'td')]
        if header[0] == '':
            header.pop(0)
        print("Header is", header)
        header_data = [header]
        all_data_row = []

        for i in range(1, min(3, len(rows))):
            property_address, parties_data, surplus_amount = extract_data_from_row(driver, rows[i])
            if property_address and parties_data:
                for party_row in parties_data:
                    all_data_row.append([property_address] + party_row + [surplus_amount])
        # Process and save data
        pattern = re.compile(r'^(.?) (\d{4} TD \d{6}) (\d{2}/\d{2}/\d{4}) (\d+) (\d+) (.?) (.*)$')
        columns = ['Status', 'Case Number', 'Date Created', 'Application Number', 'Parcel Number', 'Sale Date', 'Surplus Balance']
        processed_rows = []
        for row in all_data_row:
            match = pattern.match(row[0])
            if match:
                status, case_number, date_created, app_number, parcel_number, sale_date_part, surplus_balance = match.groups()
                sale_date = sale_date_part if sale_date_part != 'Not' else f"Not Assigned {surplus_balance.split(' ', 1)[0]}"
                surplus_balance = surplus_balance.split(' ', 1)[1] if sale_date_part == 'Not' else surplus_balance
                processed_rows.append([status.strip(), case_number.strip(), date_created.strip(), app_number.strip(), parcel_number.strip(), sale_date.strip(), surplus_balance.strip()])

        df_first = pd.DataFrame(processed_rows, columns=columns)
        df_single_row = pd.DataFrame(all_data_row, columns=[
            'Property Address', 'Name', 'Party Type', 'Street Address', 'City', 'State', 'Zip', 'Country', 'Surplus Amount'
        ])

        df_first.to_csv('first.csv', index=False)
        df_single_row.to_csv('single_row_data_formatted.csv', index=False)

        # Merge CSV files
        df_first = pd.read_csv('first.csv')
        df_formatted = pd.read_csv('single_row_data_formatted.csv')
        merged_df = pd.concat([df_first, df_formatted], ignore_index=True)
        merged_df.to_csv('merged_data.csv', index=False)
        # Final DataFrame
        df_merged = pd.read_csv('merged_data.csv')
        df_final = pd.DataFrame({
            'Property Owner Name': df_merged['Name'],
            'Property Owner Address': df_merged['Street Address'] + ', ' + df_merged['City'] + ', ' + df_merged['State'] + ', ' + df_merged['Zip'],
            'Property Address': df_merged['Property Address'],
            'Sale Date': df_merged['Sale Date'],
            'Surplus Balance': df_merged['Surplus Balance'],
            'Parcel Number': df_merged['Parcel Number'],
            'Case Number': df_merged['Case Number']
        })
        os.remove('first.csv')
        os.remove('merged_data.csv')
        os.remove('single_row_data_formatted.csv')
        df_final.to_csv('final_csv.csv', index=False)
        return True, "Data Scrapped Successfully", format_location(country_name), df_final

    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        ValueError,
        OSError,
        IOError,
        NoSuchElementException,
        StaleElementReferenceException,
        WebDriverException,
    ) as e:
        print(f"Internal Error Occurred: {e}")
        if "driver" in locals():
            driver.quit()
        return False, "Internal Error Occurred while running application. Please Try Again!!", "", ""




# Polk County Florida Function
def scrap_polk_county_florida(driver_instance, country_name, country_url, output_text):
    all_tables = []
    print_the_output_statement(output_text, f"Opening the site {country_url}")
    try:
        driver_instance.get(country_url)
        time.sleep(5)
        print_the_output_statement(
            output_text,
            f"Scraping started for {country_name}. Please wait a few minutes.",
        )
        box = driver_instance.find_element(By.XPATH, '//*[@id="isPasted"]')
        print("isPasted element is foumd")
        # Locate the table within the box
        table = box.find_element(By.TAG_NAME, "tbody")
        # Locate the title row within the box
        title = box.find_element(By.TAG_NAME, "thead")
        # Locate the rows within the thread
        conts = title.find_elements(By.TAG_NAME, "tr")
        # Locate the rows within the table
        rows = table.find_elements(By.TAG_NAME, "tr")
        i = 1
        driver_instance.execute_script(f"window.scrollBy(0,0.3);")
        print("Scrollling In Progress............")
        # Iterate over rows and extract header
        print('data is scrapping and save into the csv file')
        for cont in conts:
            cells = cont.find_elements(By.TAG_NAME, "th")
            header = [cell.text for cell in cells]
            # Remove blank entries
            header = [item for item in header if item]
            break
        # Extract data
        all_data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = [cell.text for cell in cells]
            if "," in row_data[3]:
                row_data[3] = row_data[3].replace(",", "")
            all_data.append(row_data)
            i += 1
        all_data.insert(0, header)
        merged_df = pd.DataFrame(all_data[1:], columns=all_data[0])
        final_columns = [
            "Previous Owner of Record",
            "Sale Date",
            "Amount Available",
            "Property ID Number",
            "Tax Deed Number",
            "Certificate Number",
        ]
        merged_df = merged_df[final_columns]
        merged_df = merged_df.replace(
            {pd.NA: "Nill", pd.NaT: "Nill"}
        )  # Handle missing values
        return True, "Data Scrapped Successfully", format_location(country_name), merged_df
    except NoSuchElementException as e:
        print(f"An error occurred: {e}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, f"An error occurred: {e}", "", ""
    except StaleElementReferenceException as e:
        print(f"An error occurred: {e}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, f"An error occurred: {e}", "", ""
    except WebDriverException as e:
        print(f"An error occurred: {e}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, f"An error occurred: {e}", "", ""



# Sarasota County Florida Function
def scrap_shasta_county_california(driver_instance, country_name, country_url, output_text):
    pdf_url = "https://www.shastacounty.gov/sites/default/files/fileattachments/tax_collector/page/2691/tax_sale_results_1.pdf"
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    print_the_output_statement(output_text, f"Opening the site {country_url}")
    pdf_filename = "tax_sale_results_1.pdf"
    pdf_path = ''
    try:
        if check_file_downloaded(DOWNLOAD_FOLDER, pdf_filename):
            pdf_path = os.path.join(DOWNLOAD_FOLDER, pdf_filename)
        else:
             start_time = time.time()
             driver_instance.get(pdf_url)
             time.sleep(5)  # Adjust sleep time if needed
             pdf_path = os.path.join(DOWNLOAD_FOLDER, pdf_filename)
             end_time = time.time()
             download_duration = end_time - start_time
             print(f'Downloading the pdf in the {pdf_path}')

        print(f"Download completed in {download_duration:.2f} seconds")
        print('pdf_path', pdf_path)
        with open(pdf_path, "rb") as file:
            pdf_reader = PdfReader(file)
            pdf_text = "\n".join(page.extract_text() for page in pdf_reader.pages)
        # Regex pattern to match the table rows
        pattern = re.compile(
            r"(\w+)\s+([\d-]+)\s+(.+?)\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(REDEEMED|WITHDRAWN|NO SALE|\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(.*)?"
        )
        data = []
        print(f'Downloaded  the pdf in the {pdf_path} then the data scrapping in the progress and save into the csv' )
        for line in pdf_text.split("\n"):
            match = pattern.match(line)
            if match:
                data.append(match.groups()[1:6])  # Extract groups from regex match

        # Create DataFrame
        columns = [
            "Parcel Number",
            "Assessee Name",
            "Minimum Bid Price",
            "Sale Price",
            "Excess Proceeds",
        ]
        merged_df = pd.DataFrame(data, columns=columns)
        # # Clean up
        delete_path(pdf_path)
        delete_folder(DOWNLOAD_FOLDER)
        return True, "Data Scrapped Successfully", "shasta_county_california", merged_df
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        ValueError,
        OSError,
        IOError,
        NoSuchElementException,
        StaleElementReferenceException,
        WebDriverException,
    ) as e:
        print(f"Internal Error Occurred: {e}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return (
            False,
            "Internal Error Occurred while running application. Please Try Again!!",
            "",
            "",
        )
