from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import threading
import time
from typing import Dict, List, Optional
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException,
)
import concurrent.futures

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from config import DOWNLOAD_FOLDER
from utils import (
    check_file_downloaded,
    checked_url,
    find_element_with_retry,
    format_location,
    handle_exception,
    print_the_output_statement,
    read_json_from_file,
)

NUMBER_OF_SCRAPPING = 40

lock = threading.Lock()


def append_row_to_json(row: Dict, json_file_path: str) -> None:
    """
    Appends a row to a JSON file containing a list.
    Args:
        row (dict): The row to be appended.
        json_file_path (str): The path to the JSON file.
    """
    with lock:
        # Read existing data
        if os.path.exists(json_file_path):
            with open(json_file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if not isinstance(data, list):
                    raise ValueError("The JSON file does not contain a list.")
        else:
            data = []
        if not isinstance(data, list):
            raise ValueError("The data structure is not a list.")
        data.append(row)

        # Write data back to the file
        with open(json_file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)


def get_current_page(driver: WebDriver) -> Optional[int]:
    """
    Retrieves the current page number from the pagination button.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.

    Returns:
        Optional[int]: The current page number or None if it cannot be determined.
    """
    try:
        current_page_button = find_element_with_retry(
            driver, By.CSS_SELECTOR, "button.pagination-button"
        )
        if current_page_button is None:
            return None

        current_page_text = current_page_button.text.strip()
        current_page_number = int(current_page_text.split()[-1])
        return current_page_number
    except ValueError:
        # Handle cases where the text is not convertible to an integer
        return None


def get_the_page_list(driver: WebDriver) -> List[int]:
    """
    Retrieves a sorted list of unique page numbers from a pagination menu.
    Tries to find the pagination menu by ID and, if it fails,
    retries using a CSS selector for buttons.
    Args:
        driver (WebDriver): The Selenium WebDriver instance.
    Returns:
        List[int]: Sorted list of unique page numbers.
    """
    try:
        pagination_menu = find_element_with_retry(driver, By.ID, "caseFilterPagination")
        print("pagination_menu element is found")
        # pages = sorted(set(int(a.get_attribute("data-page")) for a in pagination_menu.find_elements(By.TAG_NAME, "a")))
        pages = [1]
    except (NoSuchElementException, WebDriverException):
        print(f"Exception encountered, retrying with alternative selector...")
        pagination_buttons = find_element_with_retry(
            driver, By.CSS_SELECTOR, "span.btn-group button.btn"
        )
        print("pagination_buttons element is found")
        # pages = sorted(set(int(btn.get_attribute("data-page")) for btn in pagination_buttons if btn.get_attribute("data-page")))
        pages = [1, 2]
    return pages


def main_scrapping_process(
    driver: WebDriver, page_number: int, json_file_path: str, header_data: List[str]
) -> None:
    """
    Scrapes data from a specific page of the website and saves it to a JSON file.

    This function:
    1. Iterates over rows of a table on the specified page.
    2. For each row, it extracts data and navigates through various tabs to collect additional details.
    3. Extracts data from Summary, Party, and Disbursements tabs, including handling potential exceptions.
    4. Clicks on each row to open detailed views, retrieves necessary information, and saves it to the JSON file.
    Parameters:
    - driver: WebDriver instance used for browser automation.
    - page_number: The page number currently being scraped.
    - json_file_path: Path to the JSON file where scraped data is saved.
    - header_data: List of column headers used to parse table data.

    Returns:
    - None
    """
    table = find_element_with_retry(driver, By.ID, "county-setup")
    print("table element is found")
    rows = table.find_elements(By.TAG_NAME, "tr")
    number_of_rows = len(rows)
    print("number_of_rows", number_of_rows)
    if number_of_rows > 0:
        for i in range(1, number_of_rows):  # Loop through all rows
            table = find_element_with_retry(driver, By.ID, "county-setup")
            print("table element is found")
            rows = table.find_elements(By.TAG_NAME, "tr")
            driver.execute_script("window.scrollBy(0, window.innerHeight * 0.5);")
            print(
                f"Data scraping for table row {i} out of {number_of_rows} for page number {page_number}"
            )
            row = rows[i]
            cols = row.find_elements(By.TAG_NAME, "td")
            if cols:
                row_data = [col.text.strip() for col in cols]
                if any(row_data):
                    row_data.pop(0)  # Adjust if necessary
                    if len(header_data) == len(row_data):
                        row_dict = dict(zip(header_data, row_data))
                        row_dict = dict(zip(header_data, row_data))
                        outer_layer = []
                        outer_layer.append({"row_uuid": i, "outer_layer": row_dict})
                        WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable(rows[i])
                        ).click()
                        print(
                            f"Clicked the row {i} out of {number_of_rows} for page number {page_number}"
                        )
                        driver.execute_script(
                            "window.scrollBy(0, -window.innerHeight);"
                        )
                        time.sleep(2)
                        # Summary  tab functionality
                        print(
                            f"Please wait, data scraping of the Summary tab section for row {i} for page number {page_number}"
                        )
                        summary_section = find_element_with_retry(
                            driver, By.ID, "summarySummary"
                        )
                        details_table = summary_section.find_element(
                            By.CLASS_NAME, "table"
                        )
                        detail_rows = details_table.find_elements(By.TAG_NAME, "tr")
                        for row in detail_rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if cells:
                                header = cells[0].text.strip()
                                if "Property Address" in header:
                                    address = cells[1].text.strip()
                                    outer_layer[0]["Property Address"] = address

                        # Party tab functionality
                        party_tab = find_element_with_retry(
                            driver, By.XPATH, '//*[@id="publicSection"]/div[1]/a[2]'
                        )
                        party_tab.click()
                        print(
                            f"Please wait, data scraping of the Party tab section for row {i} for page number {page_number}"
                        )
                        time.sleep(2)
                        party_table = driver.find_element(By.CLASS_NAME, "table-public")
                        headers = party_table.find_elements(By.XPATH, ".//thead//th")
                        party_headers = [header.text.strip() for header in headers]
                        party_rows = party_table.find_elements(By.XPATH, ".//tbody//tr")
                        party_data = []  # Reset party_data for each row
                        for row in party_rows:
                            cols = row.find_elements(By.XPATH, ".//td")
                            row_data = [col.text.strip() for col in cols]
                            row_dict = dict(zip(party_headers, row_data))
                            party_data.append(row_dict)
                        outer_layer[0]["Party Data"] = party_data
                        # Disbursements tab functionality
                        Disbursements_tab = find_element_with_retry(
                            driver, By.XPATH, '//*[@id="publicSection"]/div[1]/a[8]'
                        )
                        Disbursements_tab.click()
                        print(
                            f"Please wait, data scraping of the Disbursements tab section for row {i} for page number {page_number}"
                        )
                        time.sleep(2)
                        try:
                            serplus_ammout = find_element_with_retry(
                                driver,
                                By.XPATH,
                                '//*[@id="publicSection"]/div[2]/table[2]/tbody/tr/td[4]/strong',
                            )
                            serplus_ammout.click()
                            print(f"Clicked the element for row {i}")
                        except (
                            TimeoutException,
                            NoSuchElementException,
                            StaleElementReferenceException,
                            WebDriverException,
                        ) as e:
                            serplus_ammout = find_element_with_retry(
                                driver,
                                By.XPATH,
                                '//*[@id="publicSection"]/div[2]/table[3]/tbody/tr/td[4]/strong',
                            )
                            serplus_ammout.click()
                            print(
                                f"Clicked the element for row {i} using alternative XPath"
                            )

                        scroll_target = find_element_with_retry(
                            driver, By.XPATH, '//*[@id="publicSection"]/div[2]/div[4]'
                        )
                        driver.execute_script(
                            "arguments[0].scrollIntoView();", scroll_target
                        )
                        time.sleep(3)
                        text_value = serplus_ammout.text.strip()
                        outer_layer[0]["Surplus Amount"] = text_value
                        # Click the back button
                        back_button = find_element_with_retry(
                            driver, By.CSS_SELECTOR, "button.btn.btn-back-to-case-list"
                        )
                        back_button.click()
                        print(
                            f"Clicked the back button for row {i} for page number {page_number}"
                        )
                        time.sleep(3)
                        append_row_to_json(outer_layer, json_file_path)


def scrapping_data_with_pagiantion_process(
    driver, header_data, page_list, json_file_path
):
    """
    Scrapes data from multiple pages of a website using pagination.
    Parameters:
    - driver: WebDriver instance used for browser automation.
    - header_data: List of column headers used to parse data.
    - page_list: List of available page numbers for pagination.
    - json_file_path: Path to the JSON file where scraped data is saved.
    Returns:
    - None
    """
    page_number = 1
    while True:
        tasks = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            for page in range(
                page_number, page_number + 1
            ):  # Adjust if you want to handle more pages concurrently
                future = executor.submit(
                    main_scrapping_process, driver, page, json_file_path, header_data
                )
                tasks.append(future)
            # Wait for all futures to complete
            for future in as_completed(tasks):
                future.result()  # Wait for the thread to complete

        if not page_list:
            print("No pagination buttons found.")
            break
        current_page = get_current_page(driver)
        if current_page is None:
            print("Could not determine the current page.")
            break
        next_page_number = current_page + 1
        if next_page_number not in page_list:
            print("No more pages to navigate.")
            break
        next_page_button = find_element_with_retry(
            driver, By.CSS_SELECTOR, f"button.btn[data-page='{next_page_number}']"
        )
        print("next_page_button element is found")
        if "disabled" in next_page_button.get_attribute("class"):
            print("No more pages to navigate.")
            break
        next_page_button.click()
        print(f"Navigating to page {next_page_number}...")
        time.sleep(10)
        page_number = next_page_number

def process_page(driver: WebDriver, page: int, json_file_path: str, current_url: str, header_data: list) -> None:
    """
    Processes a single page and performs scraping operations.
    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        page (int): The page number to be processed.
        json_file_path (str): The path to the JSON file where scraped data is saved.
        current_url (str): The current URL for the page.
        header_data (list): List of column headers for the table.
    """
    print(f'Processing page {page}')
    print(f'JSON file path: {json_file_path}')
    
    # Open the URL for the specific page
    page_url = f"{current_url}"
    driver.get(page_url)
    time.sleep(5)
    # Implement your scraping logic here
    # For example, extract the title and save to file
    data = {"url": page_url, "page": page,"title": driver.title}
    print('data', data)
    dynamic_x_path = f"//button[@data-page='{page}']"
    print('dynamic_x_path', dynamic_x_path)
    dynamic_btn = find_element_with_retry(driver, By.XPATH, dynamic_x_path)
    class_attribute = dynamic_btn.get_attribute("class")
    if 'active' in class_attribute.split():
        print("Button is active.")
    else:
        print("Button is not active. Clicking the button...")
        dynamic_btn.click()
        print("Button clicked.")
    main_scrapping_process(driver, page, json_file_path, header_data)


def scrapping_data_without_pagination_process(
    driver: WebDriver, 
    header_data: list, 
    page_list: list, 
    json_file_path: str,
    current_url: str
) -> None:
    """
    Scrapes data from multiple pages without using pagination.
    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        header_data (list): List of column headers for the table.
        page_list (list): List of page numbers to be processed.
        json_file_path (str): The path to the JSON file where scraped data is saved.
        current_url (str): The base URL for the pages to be processed.
    """
    print(f"Page list: {page_list}")
    number_of_pages = len(page_list)
    print(f"Number of pages: {number_of_pages}")
    
    # Create a ThreadPoolExecutor with a number of workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(number_of_pages, 5)) as executor:
        # Submit tasks to the executor
        future_to_page = {
            executor.submit(process_page, driver, page, json_file_path, current_url, header_data): page 
            for page in page_list
        }
        
        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(future_to_page):
            page = future_to_page[future]
            try:
                future.result()  # Retrieve the result or raise an exception if occurred
                print(f"Page {page} processed successfully.")
            except Exception as e:
                print(f"An error occurred while processing page {page}: {e}")

def scrap_sarasota_county_florida(driver, country_name, country_url, output_text):
    """
    Scrapes case data from Sarasota County, Florida website and saves it to a JSON file.
    Parameters:
    - driver: WebDriver instance used for browser automation.
    - country_name: Name of the country for which data is being scraped.
    - country_url: URL of the website to scrape data from.
    - output_text: Text to display for output messages.
    Returns:
    - Tuple indicating success or failure, along with status messages and additional information.
    """
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    json_file_path = os.path.join(DOWNLOAD_FOLDER, "data_scraped.json")
    try:
        if not check_file_downloaded(DOWNLOAD_FOLDER, "data_scraped.json"):
            print_the_output_statement(output_text, f"Opening the site {country_url}")
            if not checked_url(driver, country_url, country_name):
                return (
                    False,
                    "Failed to access URL",
                    format_location(country_name),
                    "",
                )
            Case_Status_btn = find_element_with_retry(
                driver, By.ID, "filterButtonStatus"
            )
            Case_Status_btn.click()
            print("Case_Status_btn element is found and clicked")
            time.sleep(2)
            element_to_hover_over = find_element_with_retry(
                driver, By.ID, "caseStatus2"
            )
            actions = ActionChains(driver)
            actions.move_to_element(element_to_hover_over).perform()
            print("element_to_hover_over element is found and clicked")
            element_to_click = find_element_with_retry(
                driver, By.XPATH, '//a[@data-statusid="1011" and @data-parentid="2"]'
            )
            element_to_click.click()
            time.sleep(2)
            print("element_to_click element is found and clicked")
            button_to_click = find_element_with_retry(
                driver,
                By.XPATH,
                '//button[@class="btn btn-default dropdown-toggle" and @data-id="filterBalanceType"]',
            )
            button_to_click.click()
            time.sleep(2)
            starplus_element = find_element_with_retry(
                driver, By.XPATH, "/html/body/div[8]/div/ul/li[2]/a/span"
            )
            starplus_element.click()
            print("starplus_element element is found and clicked")
            search_button = find_element_with_retry(
                driver, By.XPATH, '//button[@class="btn btn-success filters-submit"]'
            )
            search_button.click()
            print("search_button element is found and clicked")
            print_the_output_statement(
                output_text,
                "Please wait, data is being found according to the criteria",
            )
            time.sleep(5)
            select_element = find_element_with_retry(driver, By.ID, "resultsPerPage")
            select = Select(select_element)
            select.select_by_value(f"{NUMBER_OF_SCRAPPING}")
            print(
                f"select_element element is found and enter the {NUMBER_OF_SCRAPPING} in the seldcted value "
            )
            table = find_element_with_retry(driver, By.ID, "county-setup")
            print("table element is found")
            rows = table.find_elements(By.TAG_NAME, "tr")
            header_data = [col.text for col in rows[0].find_elements(By.TAG_NAME, "th")]
            header_data = header_data or [
                col.text for col in rows[0].find_elements(By.TAG_NAME, "td")
            ]
            if header_data and header_data[0] == "":
                header_data.pop(0)
            print("header_data", header_data)
            page_list = get_the_page_list(driver)
            with open(json_file_path, "w", encoding="utf-8") as file:
                json.dump([], file, indent=4)
            if NUMBER_OF_SCRAPPING in [10, 20,40,50,80,100]:
                print("pagination process")
                scrapping_data_with_pagiantion_process(
                    driver, header_data, page_list, json_file_path
                )
            else:
                print("Without pagiantion process")
                scrapping_data_without_pagination_process(
                    driver, header_data, page_list, json_file_path, driver.current_url
                )

        print(f"Data scraped and saved to {json_file_path}")
        json_file_read = read_json_from_file(json_file_path)
        if json_file_read:

            formatted_data = [
                {
                    "Name": party["Name"],
                    "Party Type": party["Party Type"],
                    "Property Owner Address": f"{party['Street Address']}, {party['City']}, {party['State']} {party['Zip']}, {party['Country']}",
                    "Property Address": entity["Property Address"],
                    "Surplus Amount": entity["Surplus Amount"],
                    "Case Number": outer_layer["Case Number"],
                    "Surplus Balance": outer_layer["Surplus Balance"],
                    "Parcel Number": outer_layer["Parcel Number"],
                    "Sale Date": outer_layer["Sale Date"],
                }
                for group in json_file_read
                for entity in group
                for party in entity["Party Data"]
                if party["Party Type"] == "OWNER"
                for outer_layer in [entity["outer_layer"]]
            ]
            # Convert the data to a pandas DataFrame
            df_final = pd.DataFrame(formatted_data)
            df_final = df_final.rename(columns={"Name": "Property Owner Name"})
            df_final = df_final[
                [
                    "Property Owner Name",
                    "Property Owner Address",
                    "Property Address",
                    "Sale Date",
                    "Surplus Balance",
                    "Parcel Number",
                    "Case Number",
                ]
            ]
            # df_final.to_csv('final_delaware_website.csv', index=False)
        else:
           df_final = pd.DataFrame
        return (
            False,
            "Data Scraped Successfully",
            format_location(country_name),
            df_final,
        )
    except (
        NoSuchElementException,
        StaleElementReferenceException,
        WebDriverException,
    ) as e:
        # Print error details concisely
        print(f"Error: {type(e).__name__} - {str(e)}")
        print(f"URL at error: {driver.current_url}")
        print(f"Page snippet: {driver.page_source[:500]}")
        return handle_exception(e, driver)
