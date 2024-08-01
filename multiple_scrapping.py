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
    format_location,
    print_the_output_statement,
)


def scrap_courts_delaware_gov_county(
    driver_instance, country_name, country_url, output_text
):
    print("scrap_courts_delaware_gov_county")
    print_the_output_statement(output_text, f"Opening the site {country_url}")

    try:
        driver_instance.get(country_url)
        print_the_output_statement(
            output_text,
            f"Scraping started for {country_name}. Please wait a few minutes.",
        )
        time.sleep(5)  # Allow time for page to fully load

        # Extract table headers
        table = driver_instance.find_element(By.CLASS_NAME, "table")
        headers = [
            header.text for header in table.find_elements(By.XPATH, ".//thead//th")
        ]

        rows = []
        for i in range(
            ord("a"), ord("c") + 1
        ):  # Loop through dropdown values 'a' to 'c'
            dropdown = driver_instance.find_element(
                By.XPATH, '//*[@id="main_content"]/select'
            )
            dropdown.send_keys(chr(i))
            time.sleep(3)  # Wait for table data to update

            # Extract table rows
            table = driver_instance.find_element(By.CLASS_NAME, "table")
            for row in table.find_elements(By.XPATH, ".//tbody//tr"):
                cells = [cell.text for cell in row.find_elements(By.XPATH, ".//td")]
                # Remove single alphabetic data entries (often empty cells or headers)
                cells = [
                    data for data in cells if not (len(data) == 1 and data.isalpha())
                ]
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
            f"Scraping started for {country_name}. Please wait a few minutes.",
        )

        # Check if PDF is already downloaded
        if not check_file_downloaded(DOWNLOAD_FOLDER, pdf_filename):
            # Click to download the PDF
            download_button_xpath = "/html/body/div[3]/main/div[2]/div/section/div/div/div/div/div/div[1]/ul[2]/li[2]/strong/a"
            actions = ActionChains(driver_instance)
            download_element = driver_instance.find_element(
                By.XPATH, download_button_xpath
            )
            actions.move_to_element(download_element).click().perform()
            time.sleep(5)  # Wait for download to start

            # Wait for download to complete
            wait = WebDriverWait(driver_instance, 30)
            download_path = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "/html/body/div[1]/div[4]/div/div[3]/div[2]/div[2]/div[2]",
                    )
                )
            )
            actions.move_to_element(download_path).click().perform()
            time.sleep(5)

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


def scrap_polkcountyclerk_net_county(
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

        # Locate the box containing the table
        box = driver_instance.find_element(By.XPATH, '//*[@id="isPasted"]')
        print("isPasted element is found")

        # Locate the table within the box
        table = box.find_element(By.TAG_NAME, "tbody")
        title = box.find_element(By.TAG_NAME, "thead")

        # Extract headers
        header = [
            cell.text for cell in title.find_elements(By.TAG_NAME, "th") if cell.text
        ]
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
            "Certificate Number",
        ]
        merged_df = merged_df[final_columns]
        # Handle missing values
        merged_df = merged_df.fillna("Nill")
        return True, "Data Scrapped Successfully", "PolkCountyclerk", merged_df
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


def scrap_shasta_california_county(
    driver_instance, country_name, country_url, output_text
):
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    print_the_output_statement(output_text, f"Opening the site {country_url}")

    pdf_filename = "tax_sale_results_1.pdf"
    pdf_path = os.path.join(DOWNLOAD_FOLDER, pdf_filename)
    pdf_url = "https://www.shastacounty.gov/sites/default/files/fileattachments/tax_collector/page/2691/tax_sale_results_1.pdf"

    try:
        # Download the PDF if not already downloaded
        if not check_file_downloaded(DOWNLOAD_FOLDER, pdf_filename):
            driver_instance.get(pdf_url)
            time.sleep(5)  # Adjust sleep time if needed

        # Read and parse the PDF
        pdf_reader = PdfReader(open(pdf_path, "rb"))
        pdf_text = "\n".join(page.extract_text() for page in pdf_reader.pages)

        # Regex pattern to match the table rows
        pattern = re.compile(
            r"(\w+)\s+([\d-]+)\s+(.+?)\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(REDEEMED|WITHDRAWN|NO SALE|\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(.*)?"
        )
        data = [
            match.groups()[1:6]  # Extract groups from regex match
            for line in pdf_text.split("\n")
            if (match := pattern.match(line))
        ]
        # Create DataFrame
        columns = [
            "Parcel Number",
            "Assessee Name",
            "Minimum Bid Price",
            "Sale Price",
            "Excess Proceeds",
        ]
        merged_df = pd.DataFrame(data, columns=columns)
        # Clean up
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
        print("Internal Error Occurred while running application. Please Try Again!!")
        if "driver_instance" in locals():
            driver_instance.quit()
        return (
            False,
            "Internal Error Occurred while running application. Please Try Again!!",
            "",
            "",
        )



def extract_single_row_data(driver):
    headers_data =[]
    try:
        # Extract data from the first row only
        table = driver.find_element(By.ID, 'county-setup')

        rows = table.find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, 'td')
            col_data = [col.text for col in cols]
            headers_data.append(col_data)
        headers_data_in_csv = headers_data[0]
        print('headers_data_in_csv : ', headers_data_in_csv)

        if not rows:
            print("No rows found.")
            return [], []

        # Extract the header and the first row
        header_row = rows[0]
        header_cols = header_row.find_elements(By.TAG_NAME, 'th')
        headers = [header.text for header in header_cols]

        # Extract the first data row
        row = rows[1]  # Assuming the first data row is at index 1
        cols = row.find_elements(By.TAG_NAME, 'td')
        col_data = [col.text for col in cols]
        print("col_data : ", col_data)

        # Click the row to go to the detail page
        row.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.btn.btn-back-to-case-list')))

        # Extract data from the detail page
        property_address = driver.find_element(By.XPATH, '//*[@id="summarySummary"]/table/tbody/tr[4]/td[2]').text

        # Click "Parties" link
        parties_link = driver.find_element(By.XPATH, '//a[@data-handler="dspCaseParties"]')
        parties_link.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'table-public')))

        # Extract parties table data
        parties_table = driver.find_element(By.CLASS_NAME, 'table-public')
        thead = parties_table.find_element(By.TAG_NAME, 'thead')
        parties_headers = thead.find_elements(By.TAG_NAME, 'th')
        parties_header_texts = [header.text for header in parties_headers]

        parties_rows = parties_table.find_elements(By.TAG_NAME, 'tr')
        parties_data = []
        for parties_row in parties_rows[1:]:  # Skip header row
            parties_cols = parties_row.find_elements(By.TAG_NAME, 'td')
            parties_data.append([col.text for col in parties_cols])

        # Click "Disbursements" link
        disbursements_link = driver.find_element(By.XPATH, '//a[@data-handler="dspDisbursements"]')
        disbursements_link.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="publicSection"]/div[2]/table[2]/tbody/tr/td[4]/strong')))

        # Extract surplus amount
        surplus_amount_element = driver.find_element(By.XPATH, '//*[@id="publicSection"]/div[2]/table[2]/tbody/tr/td[4]/strong')
        surplus_amount = surplus_amount_element.text
        print("surplus_amount : ", surplus_amount)

        return headers, property_address, parties_header_texts, parties_data, surplus_amount

    except Exception as e:
        print(f"Error processing row: {e}")
        return [], [], [], []

def scrap_sarasota_county_florida(
    driver, country_name, country_url, output_text
):
    # formatted_location = country_name.replace(" ", "_").lower()
    formattedlocation = format_location(country_name)
    print('formatted_location', formattedlocation)
    try:
        print_the_output_statement(output_text, f"Opening the site {country_url}")
        driver.get(country_url)
        time.sleep(5)
        print_the_output_statement(
            output_text,
            f"Scraping started for {country_name}. Please wait a few minutes.",
        )
        # Perform the initial filtering and navigation
        button = driver.find_element(By.ID, 'filterButtonStatus')
        button.click()
        time.sleep(2)
        element_to_hover_over = driver.find_element(By.ID, 'caseStatus2')
        actions = ActionChains(driver)
        actions.move_to_element(element_to_hover_over).perform()

        element_to_click = driver.find_element(By.XPATH, '//a[@data-statusid="1011" and @data-parentid="2"]')
        element_to_click.click()

        button = driver.find_element(By.ID, 'filterButtonStatus')
        button.click()

        button_to_click = driver.find_element(By.XPATH, '//button[@class="btn btn-default dropdown-toggle" and @data-id="filterBalanceType"]')
        button_to_click.click()
        time.sleep(2)

        starplus_element = driver.find_element(By.XPATH, '/html/body/div[8]/div/ul/li[2]/a/span')
        starplus_element.click()
        time.sleep(3)

        search_button = driver.find_element(By.XPATH, '//button[@class="btn btn-success filters-submit"]')
        search_button.click()
        time.sleep(10)

        headers_data = []

        def extract_single_row_data(driver):
            try:
                # Extract data from the first row only
                table = driver.find_element(By.ID, 'county-setup')

                rows = table.find_elements(By.TAG_NAME, 'tr')
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, 'td')
                    col_data = [col.text for col in cols]
                    headers_data.append(col_data)
                headers_data_in_csv = headers_data[0]
                print('headers_data_in_csv : ', headers_data_in_csv)

                if not rows:
                    print("No rows found.")
                    return [], []

                # Extract the header and the first row
                header_row = rows[0]
                header_cols = header_row.find_elements(By.TAG_NAME, 'th')
                headers = [header.text for header in header_cols]

                # Extract the first data row
                row = rows[1]  # Assuming the first data row is at index 1
                cols = row.find_elements(By.TAG_NAME, 'td')
                col_data = [col.text for col in cols]
                print("col_data : ", col_data)

                # Click the row to go to the detail page
                row.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.btn.btn-back-to-case-list')))

                # Extract data from the detail page
                property_address = driver.find_element(By.XPATH, '//*[@id="summarySummary"]/table/tbody/tr[4]/td[2]').text

                # Click "Parties" link
                parties_link = driver.find_element(By.XPATH, '//a[@data-handler="dspCaseParties"]')
                parties_link.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'table-public')))

                # Extract parties table data
                parties_table = driver.find_element(By.CLASS_NAME, 'table-public')
                thead = parties_table.find_element(By.TAG_NAME, 'thead')
                parties_headers = thead.find_elements(By.TAG_NAME, 'th')
                parties_header_texts = [header.text for header in parties_headers]

                parties_rows = parties_table.find_elements(By.TAG_NAME, 'tr')
                parties_data = []
                for parties_row in parties_rows[1:]:  # Skip header row
                    parties_cols = parties_row.find_elements(By.TAG_NAME, 'td')
                    parties_data.append([col.text for col in parties_cols])

                # Click "Disbursements" link
                disbursements_link = driver.find_element(By.XPATH, '//a[@data-handler="dspDisbursements"]')
                disbursements_link.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="publicSection"]/div[2]/table[2]/tbody/tr/td[4]/strong')))

                # Extract surplus amount
                surplus_amount_element = driver.find_element(By.XPATH, '//*[@id="publicSection"]/div[2]/table[2]/tbody/tr/td[4]/strong')
                surplus_amount = surplus_amount_element.text
                print("surplus_amount : ", surplus_amount)

                return headers, property_address, parties_header_texts, parties_data, surplus_amount

            except Exception as e:
                print(f"Error processing row: {e}")
                return [], [], [], []

        # Extract data from one row and exit
        headers, property_address, parties_header_texts, parties_data, surplus_amount = extract_single_row_data(driver)

        # Save headers and column data to first_csv.csv
        headers_data_in_csv = headers_data[0] if headers_data else []
        col_data = headers_data[1] if len(headers_data) > 1 else []

        df_first_csv = pd.DataFrame([col_data], columns=headers_data_in_csv)
        df_first_csv.to_csv('first_csv.csv', index=False)

        # Format the data as required
        formatted_data = []
        if property_address and parties_data:
            for party_row in parties_data:
                formatted_row = [property_address] + party_row
                formatted_data.append(formatted_row)

        # Include the header row for the main table data
        main_table_data = [headers] + [formatted_data[0] if formatted_data else []]

        # Convert the consolidated data into a DataFrame with appropriate headers
        df = pd.DataFrame(formatted_data, columns=[
            'Property Address', 'Name', 'Party Type', 'Street Address', 'City', 'State', 'Zip', 'Country'
        ])
        df['Surplus Amount'] = surplus_amount

        # Save the DataFrame to a CSV file
        df.to_csv('single_row_data_formatted.csv', index=False)

        # Merge both CSV files
        df_first = pd.read_csv('first_csv.csv')
        df_formatted = pd.read_csv('single_row_data_formatted.csv')

        # Concatenate them vertically
        merged_df = pd.concat([df_first, df_formatted], ignore_index=True)

        # Save the merged DataFrame to a new CSV file
        merged_df.to_csv('merged_data.csv', index=False)
        # Read the merged data CSV
        df_merged = pd.read_csv('merged_data.csv')

        # Ensure that all address columns are converted to strings
        df_merged['Street Address'] = df_merged['Street Address'].astype(str)
        df_merged['City'] = df_merged['City'].astype(str)
        df_merged['State'] = df_merged['State'].astype(str)
        df_merged['Zip'] = df_merged['Zip'].astype(str)

        # Create the new DataFrame with the required columns and headers
        df_final = pd.DataFrame()

        df_final['Property Owner Name'] = df_merged['Name']
        df_final['Property Owner Address'] = df_merged['Street Address'] + ', ' + df_merged['City'] + ', ' + df_merged['State'] + ', ' + df_merged['Zip']
        df_final['Property Address'] = df_merged['Property Address']
        df_final['Sale Date'] = df_merged['Sale Date']
        df_final['Surplus Balance'] = df_merged['Surplus Balance']
        df_final['Parcel Number'] = df_merged['Parcel Number']
        df_final['Case Number'] = df_merged['Case Number']
        os.remove('first_csv.csv')
        os.remove('merged_data.csv')
        os.remove('single_row_data_formatted.csv')
        df.drop_duplicates(subset='Property Address', keep='first', inplace=True)
        # df_final.to_csv('final_csv.csv', index=False)
        return True, "Data Scrapped Successfully", format_location(country_name),df_final
    except (
        NoSuchElementException,
        StaleElementReferenceException,
        WebDriverException,
        ValueError,
    ) as e:
        error_message = "Internal Error Occurred while running application. Please Try Again!!"
        print(error_message)
        print_the_output_statement(output_text, error_message)
        return False, error_message, "", ""
    finally:
        if "driver_instance" in locals():
            driver.quit()
    