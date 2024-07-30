import csv
import os
import time
import pandas as pd
import pdfplumber
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
from config import DOWNLOAD_FOLDER
from utils import check_file_downloaded, delete_folder, delete_path, print_the_output_statement


def scrap_courts_delaware_gov_county(driver_instance, country_name, country_url, output_text):
    print('scrap_courts_delaware_gov_county')
    print_the_output_statement(output_text, f"Opening the site {country_url}")
    try:
        driver_instance.get(country_url)
        print_the_output_statement(output_text, f"Scraping started for {country_name}. Please wait a few minutes.")
        time.sleep(5)  # Wait for the page to load
        # Locate the table
        table = driver_instance.find_element(By.CLASS_NAME, 'table')

        # Extract table headers
        headers = [header.text for header in table.find_elements(By.XPATH, './/thead//th')]

        # Extract table rows
        rows = []
        for i in range(ord('a'), ord('c') + 1):
            dropdown = driver_instance.find_element(By.XPATH, '//*[@id="main_content"]/select')
            dropdown.send_keys(chr(i))
            time.sleep(3)
            # Locate the table
            table = driver_instance.find_element(By.CLASS_NAME, 'table')
            for row in table.find_elements(By.XPATH, './/tbody//tr'):
                cells = [cell.text for cell in row.find_elements(By.XPATH, './/td')]
                cells = [data for data in cells if not (len(data) == 1 and data.isalpha())]
                rows.append(cells)

        # Save scraped data to CSV
        csv_file = 'table_data.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers) 
            writer.writerows(rows)  
        # Define columns of interest and mapping rules
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

        # Load the CSV file and clean the data
        df = pd.read_csv(csv_file)
        df_cleaned = df.drop_duplicates()

        # Create a new DataFrame with columns of interest
        new_df = pd.DataFrame(columns=columns_of_interest)

        # Map and extract relevant data
        for column in columns_of_interest:
            original_column_name = mapping.get(column, column)
            # if original_column_name in df_cleaned.columns:
            new_df[column] = df_cleaned[original_column_name]
        new_df = new_df.drop_duplicates()
        
        delete_path(csv_file)
        return True, "Scraping completed successfully", 'courts_delaware', new_df
    except NoSuchElementException as e:
        error_message = f"NoSuchElementException: {e}"
        print(error_message)
        print_the_output_statement(output_text, error_message)
        return False, error_message, "", ""
    
    except StaleElementReferenceException as e:
        error_message = f"StaleElementReferenceException: {e}"
        print(error_message)
        print_the_output_statement(output_text, error_message)
        return False, error_message, "", ""
    
    except WebDriverException as e:
        error_message = f"WebDriverException: {e}"
        print(error_message)
        print_the_output_statement(output_text, error_message)
        return False, error_message, "", ""
    
    except ValueError as e:
        error_message = f"ValueError: {e}"
        print(error_message)
        print_the_output_statement(output_text, error_message)
        return False, error_message, "", ""
    
    finally:
        if "driver_instance" in locals():
            driver_instance.quit()

def scrap_sumterclerk_county(driver_instance, country_name, country_url, output_text):
    print('scrap_sumterclerk_county')
    all_tables = []
    print_the_output_statement(output_text, f"Opening the site {country_url}")

    try:
        driver_instance.get(country_url)
        print_the_output_statement(output_text, f"Scraping started for {country_name}. Please wait a few minutes.")
        
        if check_file_downloaded(DOWNLOAD_FOLDER, 'Tax Deed Surplus.pdf'):
            main_download_file = os.path.join(DOWNLOAD_FOLDER, 'Tax Deed Surplus.pdf')
        else:
            download_button_xpath = "/html/body/div[3]/main/div[2]/div/section/div/div/div/div/div/div[1]/ul[2]/li[2]/strong/a"
            actions = ActionChains(driver_instance)
            download_element = driver_instance.find_element(By.XPATH, download_button_xpath)
            actions.move_to_element(download_element).click().perform()
            time.sleep(5)
            wait = WebDriverWait(driver_instance, 30)
            download_path = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[4]/div/div[3]/div[2]/div[2]/div[2]")))
            actions.move_to_element(download_path).click().perform()
            time.sleep(5)
            main_download_file = os.path.join(DOWNLOAD_FOLDER, 'Tax Deed Surplus.pdf')

        print('main_download_file', main_download_file)
        
        with pdfplumber.open(main_download_file) as pdf:
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

        print("Combining all tables into one DataFrame...")
        combined_df = pd.concat(all_tables, ignore_index=True).dropna(how="all")
        combined_df = combined_df[combined_df.apply(lambda row: row.astype(str).str.strip().ne("").any(), axis=1)]
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
            "APPLICATION DATE": "Application Date"
        }
        merged_df = merged_df.rename(columns=column_mapping)

        final_columns = [
            "Property Owner",
            "Property Address",
            "Sale Date",
            "Amount of Surplus",
            "Parcel #",
            "Application Date"
        ]
        # Ensure all final columns are present and fill missing columns with "Nill"
        for col in final_columns:
            if col not in merged_df.columns:
                merged_df[col] = "Nill"

        merged_df = merged_df[final_columns]
        merged_df = merged_df.replace({pd.NA: "Nill", pd.NaT: "Nill"})  # Handle missing values
        delete_path(main_download_file)
        delete_folder(DOWNLOAD_FOLDER)
        return True, "Data Scrapped Successfully", "sumterclerk", merged_df

    except FileNotFoundError:
        print(f"File not found: {main_download_file}")
        if "driver_instance" in locals():
            driver_instance.quit()
        return False, f"File not found: {main_download_file}", "", ""
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


def scrap_polkcountyclerk_net_county(driver_instance, country_name, country_url, output_text):
    all_tables = []
    print_the_output_statement(output_text, f"Opening the site {country_url}")
    try:
        driver_instance.get(country_url)
        time.sleep(5)
        print_the_output_statement(output_text, f"Scraping started for {country_name}. Please wait a few minutes.")
        box = driver_instance.find_element(By.XPATH, '//*[@id="isPasted"]')
        print('isPasted element is foumd')
        # Locate the table within the box
        table = box.find_element(By.TAG_NAME, 'tbody')
        # Locate the title row within the box
        title = box.find_element(By.TAG_NAME, 'thead')
        # Locate the rows within the thread
        conts = title.find_elements(By.TAG_NAME, 'tr')
        # Locate the rows within the table
        rows = table.find_elements(By.TAG_NAME, 'tr')
        i = 1
        driver_instance.execute_script(f"window.scrollBy(0,0.3);")
        print('Scrollling In Progress............')
        # Iterate over rows and extract header
        for cont in conts:
            cells = cont.find_elements(By.TAG_NAME, 'th')
            header = [cell.text for cell in cells]
            # Remove blank entries
            header = [item for item in header if item]
            break
         # Extract data
        all_data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            row_data = [cell.text for cell in cells]
            if ',' in row_data[3]:
                row_data[3] = row_data[3].replace(',', '')
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
            "Certificate Number"
        ]
        merged_df = merged_df[final_columns]
        merged_df = merged_df.replace({pd.NA: "Nill", pd.NaT: "Nill"})  # Handle missing values
        return True, "Data Scrapped Successfully", "PolkCountyclerk", merged_df
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

    

