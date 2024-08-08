import csv
import json
import os
import re
import sys
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
    TimeoutException,
)
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pdfplumber
import pandas as pd
from PyPDF2 import PdfReader
from config import DOWNLOAD_FOLDER
from utils import (
    check_file_downloaded,
    delete_folder,
    delete_path,
    format_location,
    print_the_output_statement,
    read_json_file,
    wait_and_click,
)

# Utility function to scrape table data

def smooth_scroll_to_element(driver, element, offset_percentage=10):
    """Scroll the page until the element is in view with a specified offset."""
    # Calculate the viewport height and the offset in pixels
    viewport_height = driver.execute_script("return window.innerHeight")
    offset = viewport_height * (offset_percentage / 100.0)
    # Scroll to the element with the offset
    driver.execute_script(
        "window.scrollTo({ top: arguments[0].offsetTop - arguments[1], behavior: 'smooth' });",
        element, offset
    )
# Function to split Address into City, State, and Zip Code and update Address
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
    
# New Castle County Delaware Function
def scrap_new_castle_county_delaware(
    driver_instance, country_name, country_url, output_text
):
    print_the_output_statement(output_text, f"Opening the site {country_url}")
    try:
        driver_instance.get(country_url)
        time.sleep(5)
        print_the_output_statement(
            output_text,
            f"Scraping started for {country_name}. Please wait a few minutes.",
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
        os.remove('final_delaware_website.csv')
        os.remove('table_data.csv')
        os.remove('delaware_website.csv')

        # Save cleaned data back to CSV
        # df_cleaned.to_csv('table_data_cleaned.csv', index=False)
        # Delete the original CSV file
        # os.remove(csv_file)
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



# Sumter County Florida Function
def scrap_sumter_county_florida(
    driver_instance, country_name, country_url, output_text
):
    print("scrap_sumterclerk_county")
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    main_download_file = None
    all_tables = []
    print_the_output_statement(output_text, f"Opening the site {country_url}")
    try:
        driver_instance.get(country_url)
        time.sleep(5)
        print_the_output_statement(
            output_text,
            f"Scraping started for {country_name}. Please wait a few minutes.",
        )

        if check_file_downloaded(DOWNLOAD_FOLDER, "Tax Deed Surplus.pdf"):
            main_download_file = os.path.join(DOWNLOAD_FOLDER, "Tax Deed Surplus.pdf")
        else:
            download_button_xpath = "/html/body/div[3]/main/div[2]/div/section/div/div/div/div/div/div[1]/ul[2]/li[2]/strong/a"
            actions = ActionChains(driver_instance)
            download_element = driver_instance.find_element(
                By.XPATH, download_button_xpath
            )
            actions.move_to_element(download_element).click().perform()
            print(f"download_element element is found and clicked ")
            time.sleep(10)
            wait = WebDriverWait(driver_instance, 60)
            download_path = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "/html/body/div[1]/div[4]/div/div[3]/div[2]/div[2]/div[2]/div",
                    )
                )
            )
            actions.move_to_element(download_path).click().perform()
            print(f"download_path is found and clicked")
            print("Downlading the pdf ............................................")
            time.sleep(5)
            main_download_file = os.path.join(DOWNLOAD_FOLDER, "Tax Deed Surplus.pdf")
            print(f"Downladed the  the pdf {main_download_file}")
        print("main_download_file", main_download_file)

        with pdfplumber.open(main_download_file) as pdf:
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

        print("Combining all tables into one DataFrame...")
        combined_df = pd.concat(all_tables, ignore_index=True).dropna(how="all")
        combined_df = combined_df[
            combined_df.apply(
                lambda row: row.astype(str).str.strip().ne("").any(), axis=1
            )
        ]
        combined_df = combined_df.fillna("Nill")

        # Process to handle empty rows by filling with "Nill"
        even_rows = combined_df.iloc[::2].reset_index(drop=True)
        odd_rows = combined_df.iloc[1::2].reset_index(drop=True)
        odd_rows = odd_rows.reindex(even_rows.index, fill_value=pd.NA)
        merged_df = pd.concat([even_rows, odd_rows.add_suffix("_Odd")], axis=1)

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
        # Ensure all final columns are present and fill missing columns with "Nill"
        for col in final_columns:
            if col not in merged_df.columns:
                merged_df[col] = "Nill"

        merged_df = merged_df[final_columns]
        merged_df = merged_df.replace(
            {pd.NA: "Nill", pd.NaT: "Nill"}
        )  # Handle missing values
        delete_path(main_download_file)
        delete_folder(DOWNLOAD_FOLDER)
        return (
            True,
            "Data Scrapped Successfully",
            format_location(country_name),
            merged_df,
        )
    except pd.errors.EmptyDataError:
        print("No data found in the PDF.")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, "No data found in the PDF.", "", ""
    except pd.errors.ParserError as e:
        print(f"Pandas parsing error: {e}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, f"Pandas parsing error: {e}", "", ""
    except PermissionError:
        print(f"Permission denied: {'csv_path.csv'}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, f"Permission denied: {'csv_path.csv'}", "", ""
    except ValueError as e:
        print(f"An error occurred: {e}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, f"An error occurred: {e}", "", ""
    except (OSError, IOError) as e:
        print(f"An error occurred: {e}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, f"An error occurred: {e}", "", ""
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
# Sarasota County Florida Function
def scrap_sarasota_county_florida(driver, country_name, country_url, output_text):
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    data_scraped = os.path.join(DOWNLOAD_FOLDER, "data_scraped.json")
    try:
        if check_file_downloaded(DOWNLOAD_FOLDER, "data_scraped.json"):
            data_scraped = os.path.join(DOWNLOAD_FOLDER, "data_scraped.json")
        else:
            all_data_rows1 = []
            print_the_output_statement(output_text, f"Opening the site {country_url}")
            driver.get(country_url)
            time.sleep(5)
            print_the_output_statement(
                output_text,
                f"Scraping started for {country_name}. Please wait a few minutes.",
            )
            
            # Perform the initial filtering and navigation
            button = driver.find_element(By.ID, "filterButtonStatus")
            button.click()
            time.sleep(2)
            element_to_hover_over = driver.find_element(By.ID, "caseStatus2")
            actions = ActionChains(driver)
            actions.move_to_element(element_to_hover_over).perform()
            element_to_click = driver.find_element(
                By.XPATH, '//a[@data-statusid="1011" and @data-parentid="2"]'
            )
            element_to_click.click()
            button_to_click = driver.find_element(
                By.XPATH,
                '//button[@class="btn btn-default dropdown-toggle" and @data-id="filterBalanceType"]',
            )
            button_to_click.click()
            time.sleep(2)
            starplus_element = driver.find_element(
                By.XPATH, "/html/body/div[8]/div/ul/li[2]/a/span"
            )
            starplus_element.click()
            time.sleep(2)
            search_button = driver.find_element(
                By.XPATH, '//button[@class="btn btn-success filters-submit"]'
            )
            search_button.click()
            print_the_output_statement(
                output_text,
                "Please wait, data is being found according to the criteria",
            )
            time.sleep(4)

            # Process rows
            select_element = WebDriverWait(driver, 4).until(
                EC.presence_of_element_located((By.ID, "resultsPerPage"))
            )
            select = Select(select_element)
            select.select_by_value("100")
            print("Selected value 100")
            time.sleep(10)

            table = driver.find_element(By.ID, "county-setup")
            rows = table.find_elements(By.TAG_NAME, "tr")
            number_of_rows = len(rows)
            print(f"Total number of rows: {number_of_rows}")
            if number_of_rows > 0:
                header_data = [
                    col.text for col in rows[0].find_elements(By.TAG_NAME, "th")
                ]
                header_data = header_data or [
                    col.text for col in rows[0].find_elements(By.TAG_NAME, "td")
                ]
                if header_data and header_data[0] == "":
                    header_data.pop(0)
                print("header_data", header_data)

                for i in range(1, number_of_rows):  # Loop through all rows
                    print(f"Data scraping for table row {i} out of {number_of_rows}")
                    table = driver.find_element(By.ID, "county-setup")
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    row = rows[i]
                    driver.execute_script("window.scrollBy(0, window.innerHeight * 0.5);")
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if cols:
                        row_data = [col.text.strip() for col in cols]
                        if any(row_data):
                            row_data.pop(0)
                            if len(header_data) == len(row_data):
                                row_dict = dict(zip(header_data, row_data))
                                outer_layer = []
                                outer_layer.append(
                                    {"row_uuid": i, "outer_layer": row_dict}
                                )
                                WebDriverWait(driver, 20).until(
                                    EC.element_to_be_clickable(rows[i])
                                ).click()
                                print(f"Clicked the row {i}")

                                # Summary tab functionality
                                wait_and_click(
                                    driver,
                                    By.XPATH,
                                    '//*[@id="publicSection"]/div[1]/a[1]',
                                )
                                print(
                                    f"Please wait, data scraping of the Summary tab section for row {i}"
                                )
                                time.sleep(5)
                                summary_section = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located(
                                        (By.ID, "summarySummary")
                                    )
                                )
                                details_table = summary_section.find_element(
                                    By.CLASS_NAME, "table"
                                )
                                detail_rows = details_table.find_elements(
                                    By.TAG_NAME, "tr"
                                )
                                for row in detail_rows:
                                    cells = row.find_elements(By.TAG_NAME, "td")
                                    if cells:
                                        header = cells[0].text.strip()
                                        if "Property Address" in header:
                                            address = cells[1].text.strip()
                                            outer_layer[0]["Property Address"] = address

                                # Party tab functionality
                                wait_and_click(
                                    driver,
                                    By.XPATH,
                                    '//*[@id="publicSection"]/div[1]/a[2]',
                                )
                                print(
                                    f"Please wait, data scraping of the Party tab section for row {i}"
                                )
                                time.sleep(5)
                                party_table = driver.find_element(
                                    By.CLASS_NAME, "table-public"
                                )
                                headers = party_table.find_elements(
                                    By.XPATH, ".//thead//th"
                                )
                                party_headers = [
                                    header.text.strip() for header in headers
                                ]
                                party_rows = party_table.find_elements(
                                    By.XPATH, ".//tbody//tr"
                                )
                                party_data = []  # Reset party_data for each row
                                for row in party_rows:
                                    cols = row.find_elements(By.XPATH, ".//td")
                                    row_data = [col.text.strip() for col in cols]
                                    row_dict = dict(zip(party_headers, row_data))
                                    party_data.append(row_dict)
                                outer_layer[0]["Party Data"] = party_data

                                # Disbursements tab functionality
                                wait_and_click(
                                    driver,
                                    By.XPATH,
                                    '//*[@id="publicSection"]/div[1]/a[8]',
                                )
                                print(
                                    f"Please wait, data scraping of the Disbursements tab section for row {i}"
                                )
                                time.sleep(5)

                                try:
                                    # Click the specific element
                                    element = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.XPATH, '//*[@id="publicSection"]/div[2]/table[2]/tbody/tr/td[4]/strong')
                                        )
                                    )
                                    element.click()
                                    print(f"Clicked the element for row {i}")
                                except (TimeoutException, NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
                                    print(f"Exception type: {type(e).__name__}")
                                    print(f"Retrying with alternative XPath for row {i}...")
                                    try:
                                        # Retry with the alternative XPath
                                        element = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.XPATH, '//*[@id="publicSection"]/div[2]/table[3]/tbody/tr/td[4]/strong')
                                            )
                                        )
                                        element.click()
                                        print(f"Clicked the element for row {i} using alternative XPath")
                                    except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
                                        print(f"Exception details: {str(e)}")
                                        print(f"Failed to click the element for row {i} with both XPaths")
                                        print(f"Data cannot be retrieved for this row.")


                                 # Scroll down to the specified XPath element
                                scroll_target = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located(
                                        (By.XPATH, '//*[@id="publicSection"]/div[2]/div[4]')
                                    )
                                )
                                driver.execute_script("arguments[0].scrollIntoView();", scroll_target)
                                time.sleep(3)  
                                
                                text_value = element.text.strip()
                                outer_layer[0]["Surplus Amount"] = text_value
                                
                                # Scroll back up
                                driver.execute_script("window.scrollBy(0, -window.innerHeight);")
                                time.sleep(3)  # Allow time for the scroll effect

                                # Click the back button
                                back_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable(
                                        (By.CSS_SELECTOR, "button.btn.btn-back-to-case-list")
                                    )
                                )
                                back_button.click()
                                print(f"Clicked the back button for row {i}")
                                time.sleep(5)

                                # Add collected data to final list
                                all_data_rows1.append(outer_layer)
            with open(data_scraped, "w") as json_file:
                json.dump(all_data_rows1, json_file, indent=4)

        json_file_read = read_json_file(data_scraped)
        formatted_data1 = []
        for group in json_file_read:
            for entity in group:
                outer_layer = entity["outer_layer"]
                party_data = entity["Party Data"]
                for party in party_data:
                    if party["Party Type"] == "OWNER":
                        formatted_party = {
                            "Name": party["Name"],
                            "Party Type": party["Party Type"],
                            "Property Owner Address": f"{party['Street Address']}, {party['City']}, {party['State']} {party['Zip']}, {party['Country']}",
                            "Property Address": entity["Property Address"],
                            "Surplus Amount": entity["Surplus Amount"],
                            "Case Number": outer_layer["Case Number"],
                            "Surplus Balance": outer_layer["Surplus Balance"],
                            "Parcel Number": outer_layer["Parcel Number"],
                            "Case Number": outer_layer["Case Number"],
                            "Sale Date": outer_layer["Sale Date"],
                        }
                        formatted_data1.append(formatted_party)
        print("formatted_data1", formatted_data1)
        # Convert the data to a pandas DataFrame
        df_final = pd.DataFrame(formatted_data1)
        column_mapping = {
            "Name": "Property Owner Name",
        }
        df_final = df_final.rename(columns=column_mapping)
        final_columns = [
            "Property Owner Name",
            "Property Owner Address",
            "Property Address",
            "Sale Date",
            "Surplus Balance",
            "Parcel Number",
            "Case Number",
        ]
        df_final = df_final[final_columns]
        delete_path(data_scraped)
        delete_folder(DOWNLOAD_FOLDER)
        return (
            True,
            "Data Scrapped Successfully",
            format_location(country_name),
            df_final,
        )
    except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
        print(f"Exception details: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        print(f"URL at time of error: {driver.current_url}")
        print(f"Page source at error: {driver.page_source[:500]}")  # Prints first 500 chars of the page source
        if "driver" in locals():
            driver.quit()
        return (
            False,
            "Internal Error Occurred while running application. Please Try Again!!",
            "",
            "",
        )

    # except (
    #     NoSuchElementException,
    #     StaleElementReferenceException,
    #     WebDriverException,
    # ) as e:
    #     print(f"Internal Error Occurred: {e}")
    #     if "driver" in locals():
    #         driver.quit()
    #     return (
    #         False,
    #         "Internal Error Occurred while running application. Please Try Again!!",
    #         "",
    #         "",
    #     )



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
        print("data is scrapping and save into the csv file")
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
        return (
            True,
            "Data Scrapped Successfully",
            format_location(country_name),
            merged_df,
        )
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
def scrap_shasta_county_california(
    driver_instance, country_name, country_url, output_text
):
    pdf_url = "https://www.shastacounty.gov/sites/default/files/fileattachments/tax_collector/page/2691/tax_sale_results_1.pdf"
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    print_the_output_statement(output_text, f"Opening the site {country_url}")
    pdf_filename = "tax_sale_results_1.pdf"
    pdf_path = ""
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
            print(f"Downloading the pdf in the {pdf_path}")

        print(f"Download completed in {download_duration:.2f} seconds")
        print("pdf_path", pdf_path)
        with open(pdf_path, "rb") as file:
            pdf_reader = PdfReader(file)
            pdf_text = "\n".join(page.extract_text() for page in pdf_reader.pages)
        # Regex pattern to match the table rows
        pattern = re.compile(
            r"(\w+)\s+([\d-]+)\s+(.+?)\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(REDEEMED|WITHDRAWN|NO SALE|\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(.*)?"
        )
        data = []
        print(
            f"Downloaded  the pdf in the {pdf_path} then the data scrapping in the progress and save into the csv"
        )
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
