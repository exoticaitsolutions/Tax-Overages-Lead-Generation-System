import os
import time
import pandas as pd
import pdfplumber
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
from typing import List

from config import DOWNLOAD_FOLDER
from utils import *

def scrap_sarasota_county_florida(driver_instance, country_name, country_url, output_text):
    """
    Scrapes tax deed surplus data from Sumter County, Florida.
    Downloads the PDF report from the specified URL, processes it to extract
    relevant data, and returns the extracted data as a pandas DataFrame.
    Args:
        driver_instance: An instance of a Selenium WebDriver.
        country_name (str): The name of the country (used for logging purposes).
        country_url (str): The URL from which to download the PDF report.
        output_text (str): Output stream or file to print log messages.
    Returns:
        tuple: A tuple containing a boolean indicating success, a message, the formatted location, and a DataFrame with the scraped data.
    """
    print("scrap_sumterclerk_county")
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    data_scraped = os.path.join(DOWNLOAD_FOLDER, "data_scraped.json")
    print_the_output_statement(output_text, f"Opening the site {country_url}")
    try:
        if not check_file_downloaded(DOWNLOAD_FOLDER, "data_scraped.json"):
            driver_instance.get(country_url)
            print_the_output_statement(
            output_text,
            f"Scraping started for {country_name}. Please wait a few minutes."
        )
            time.sleep(5)            
            # Perform the initial filtering and navigation
            button = driver_instance.find_element(By.ID, "filterButtonStatus")
            button.click()
            time.sleep(2)
            element_to_hover_over = driver_instance.find_element(By.ID, "caseStatus2")
            actions = ActionChains(driver_instance)
            actions.move_to_element(element_to_hover_over).perform()
            element_to_click = driver_instance.find_element(By.XPATH, '//a[@data-statusid="1011" and @data-parentid="2"]')
            element_to_click.click()
            button_to_click = driver_instance.find_element(By.XPATH, '//button[@class="btn btn-default dropdown-toggle" and @data-id="filterBalanceType"]')
            button_to_click.click()
            time.sleep(2)
            starplus_element = driver_instance.find_element(By.XPATH, "/html/body/div[8]/div/ul/li[2]/a/span")
            starplus_element.click()
            time.sleep(2)
            search_button = driver_instance.find_element(By.XPATH, '//button[@class="btn btn-success filters-submit"]')
            search_button.click()
            print_the_output_statement(output_text, "Please wait, data is being found according to the criteria")
            time.sleep(4)
            # Process rows
            select_element = WebDriverWait(driver_instance, 4).until(EC.presence_of_element_located((By.ID, "resultsPerPage")))
            select = Select(select_element)
            select.select_by_value("100")
            print("Selected value 100")
            time.sleep(10)
        
        return (
            False,
            "Data Scrapped Successfully",
            format_location(country_name),
            'merged_df',
        )
    except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
        return handle_exception(e, driver_instance)
    except (OSError, IOError, ValueError) as e:
        return handle_exception(e, driver_instance)
    finally:
        if "driver_instance" in locals():
            driver_instance.quit()