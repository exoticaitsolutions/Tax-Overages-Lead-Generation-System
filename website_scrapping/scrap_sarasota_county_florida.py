import json
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException

from config import DOWNLOAD_FOLDER
from utils import check_file_downloaded, delete_folder, delete_path, format_location, print_the_output_statement, read_json_from_file, wait_and_click

# Define a lock for thread-safe file access
lock = threading.Lock()

def append_row_to_json(row, json_file_path):
    with lock:
        # Read existing data
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if not isinstance(data, list):
                    raise ValueError("The JSON file does not contain a list.")
        else:
            data = []

        # Append new row data
        if not isinstance(data, list):
            raise ValueError("The data structure is not a list.")
        data.append(row)

        # Write data back to the file
        with open(json_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)

def scrape_page(driver, page_number, json_file_path, header_data):
    table = driver.find_element(By.ID, "county-setup")
    rows = table.find_elements(By.TAG_NAME, "tr")
    number_of_rows = len(rows)
    if number_of_rows > 0:
        for i in range(1, number_of_rows):  # Loop through all rows
            driver.execute_script("window.scrollBy(0, window.innerHeight * 0.5);")
            print(f"Data scraping for table row {i} out of {number_of_rows} for page number {page_number}") 
            table = driver.find_element(By.ID, "county-setup")
            rows = table.find_elements(By.TAG_NAME, "tr")
            row = rows[i]
            cols = row.find_elements(By.TAG_NAME, "td")
            if cols:
                row_data = [col.text.strip() for col in cols]
                if any(row_data):
                    row_data.pop(0)  # Adjust if necessary
                    if len(header_data) == len(row_data):
                        row_dict = dict(zip(header_data, row_data))
                        outer_layer = []
                        outer_layer.append({"row_uuid": i, "outer_layer": row_dict})
                        WebDriverWait(driver, 20).until(
                                    EC.element_to_be_clickable(rows[i])
                                ).click()
                        print(f"Clicked the row {i} out of {number_of_rows} for page number {page_number}")
                        driver.execute_script("window.scrollBy(0, -window.innerHeight);")
                        time.sleep(3)  # Allow time for the scroll effect
                        print(
                                    f"Please wait, data scraping of the Summary tab section for row {i} for page number {page_number}"
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
                            f"Please wait, data scraping of the Party tab section for row {i} for page number {page_number}"
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
                            f"Please wait, data scraping of the Disbursements tab section for row {i} for page number {page_number}"
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
                        # Click the back button
                        back_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable(
                                        (By.CSS_SELECTOR, "button.btn.btn-back-to-case-list")
                                    )
                                )
                        back_button.click()
                        print(f"Clicked the back button for row {i} for page number {page_number}")
                        time.sleep(10)
                        append_row_to_json(outer_layer, json_file_path)

def get_current_page(driver):
    try:
        # Locate the button that shows the current page
        current_page_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.pagination-button"))
        )
        # Extract the current page number from the button text
        current_page_text = current_page_button.text.strip()
        # The button text might be something like "Page X", so extract the page number
        current_page_number = int(current_page_text.split()[-1])
        return current_page_number
    except (NoSuchElementException, ValueError) as e:
        print(f"Error finding or parsing the current page: {str(e)}")
        return None

def scrap_sarasota_county_florida(driver, country_name, country_url, output_text):
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    json_file_path = os.path.join(DOWNLOAD_FOLDER, "data_scraped.json")

    try:
        if check_file_downloaded(DOWNLOAD_FOLDER, "data_scraped.json"):
            json_file_path = os.path.join(DOWNLOAD_FOLDER, "data_scraped.json")
        else:
            print_the_output_statement(output_text, f"Opening the site {country_url}")
            driver.get(country_url)
            time.sleep(5)
            print_the_output_statement(output_text, f"Scraping started for {country_name}. Please wait a few minutes.")
            
            # Perform the initial filtering and navigation
            button = driver.find_element(By.ID, "filterButtonStatus")
            button.click()
            time.sleep(2)
            element_to_hover_over = driver.find_element(By.ID, "caseStatus2")
            actions = ActionChains(driver)
            actions.move_to_element(element_to_hover_over).perform()
            element_to_click = driver.find_element(By.XPATH, '//a[@data-statusid="1011" and @data-parentid="2"]')
            element_to_click.click()
            button_to_click = driver.find_element(By.XPATH, '//button[@class="btn btn-default dropdown-toggle" and @data-id="filterBalanceType"]')
            button_to_click.click()
            time.sleep(2)
            starplus_element = driver.find_element(By.XPATH, "/html/body/div[8]/div/ul/li[2]/a/span")
            starplus_element.click()
            time.sleep(2)
            search_button = driver.find_element(By.XPATH, '//button[@class="btn btn-success filters-submit"]')
            search_button.click()
            print_the_output_statement(output_text, "Please wait, data is being found according to the criteria")
            time.sleep(4)

            # Initialize the JSON file as an empty list
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump([], file, indent=4)
            # Start pagination
            select_element = WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.ID, "resultsPerPage")))
            select = Select(select_element)
            select.select_by_value("10")
            print("Selected value 10")
            time.sleep(10)
            page_number = 1

            table = driver.find_element(By.ID, "county-setup")
            rows = table.find_elements(By.TAG_NAME, "tr")
            header_data = [col.text for col in rows[0].find_elements(By.TAG_NAME, "th")]
            header_data = header_data or [col.text for col in rows[0].find_elements(By.TAG_NAME, "td")]
            if header_data and header_data[0] == "":
                header_data.pop(0)
            print("header_data", header_data)
            
            while True:
                # Collect tasks for concurrent execution
                tasks = []
                # Using ThreadPoolExecutor to run scrape_page function
                with ThreadPoolExecutor(max_workers=5) as executor:
                    for page in range(page_number, page_number + 1):  # Adjust if you want to handle more pages concurrently
                        future = executor.submit(scrape_page, driver, page, json_file_path, header_data)
                        tasks.append(future)
                    
                    # Wait for all futures to complete
                    for future in as_completed(tasks):
                        future.result()  # Wait for the thread to complete

                try:
                    # Locate pagination buttons
                    pagination_menu = driver.find_element(By.ID, "caseFilterPagination")
                    # pages = [int(a.get_attribute("data-page")) for a in pagination_menu.find_elements(By.TAG_NAME, "a")]
                    pages= [1]
                    # Determine if there are more pages
                    if not pages:
                        print("No pagination buttons found.")
                        break
                    
                    # pages = sorted(set(map(int, pages)))
                    # pages = sorted(set(map(int, pages)))
                    pages= [1]
                    print('pages', pages)
                    current_page = get_current_page(driver)
                    if current_page is None:
                        print("Could not determine the current page.")
                        break

                    next_page_number = current_page + 1
                    if next_page_number not in pages:
                        print("No more pages to navigate.")
                        break

                    next_page_button = driver.find_element(By.CSS_SELECTOR, f"button.btn[data-page='{next_page_number}']")
                    if 'disabled' in next_page_button.get_attribute('class'):
                        print("No more pages to navigate.")
                        break

                    next_page_button.click()
                    print(f"Navigating to page {next_page_number}...")
                    time.sleep(10)
                    page_number = next_page_number
                except (NoSuchElementException, WebDriverException) as e:
                    print(f"Exception type: {type(e).__name__}")
                    print(f"Retrying with alternative XPath for pages ...")
                    pagination_buttons = driver.find_elements(By.CSS_SELECTOR, "span.btn-group button.btn")
                    pages = [btn.get_attribute("data-page") for btn in pagination_buttons if btn.get_attribute("data-page")]
                    if not pages:
                        print("No pagination buttons found.")
                        break
                    pages = sorted(set(map(int, pages)))
                    print('pages', pages)
                    current_page = int(driver.find_element(By.CSS_SELECTOR, "button.btn.active").get_attribute("data-page"))

                    next_page_button = driver.find_element(By.CSS_SELECTOR, f"button.btn[data-page='{current_page + 1}']")
                    if 'disabled' in next_page_button.get_attribute('class'):
                        print("No more pages to navigate.")
                        break
                    if current_page + 1 not in pages:
                        print(f"Next page {current_page + 1} is not available.")
                        break

                    next_page_button.click()
                    print(f"Navigating to page {current_page + 1}...")
                    time.sleep(10)  # Wait for the next page to load
                    page_number = current_page + 1

        print(f"Data scraped and saved to {json_file_path}")
        json_file_read = read_json_from_file(json_file_path)
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
        df_final.to_csv('data_scrapping.csv', index=False)
        delete_path(json_file_path)
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
        print(f"Page source at error: {driver.page_source[:500]}")
        if "driver" in locals():
            driver.quit()
        return (
            False,
            "Internal Error Occurred while running application. Please Try Again!!",
            "",
            "",
        )
