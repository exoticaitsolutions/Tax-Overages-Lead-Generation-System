import os
import time
import pandas as pd
import pdfplumber
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from typing import List

from config import DOWNLOAD_FOLDER
from utils import *


def scrap_sumter_county_florida(
    driver_instance, country_name, country_url, output_text
):
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
    main_download_file = os.path.join(DOWNLOAD_FOLDER, "Tax Deed Surplus.pdf")
    print_the_output_statement(output_text, f"Opening the site {country_url}")
    try:
        print_the_output_statement(
            output_text,
            f"Scraping started for {country_name}. Please wait a few minutes.",
        )
        if not check_file_downloaded(DOWNLOAD_FOLDER, "Tax Deed Surplus.pdf"):
            driver_instance.get(country_url)
            time.sleep(5)
            download_button_xpath = find_element_with_retry(
                driver_instance,
                By.XPATH,
                "/html/body/div[3]/main/div[2]/div/section/div/div/div/div/div/div[1]/ul[2]/li[2]/strong/a",
            )
            download_button_xpath.click()
            print("download_button_xpath element is found and clicked successfully")
            time.sleep(5)
            forcelly_dowload_x_path = find_element_with_retry(
                driver_instance,
                By.XPATH,
                "/html/body/div[1]/div[4]/div/div[3]/div[2]/div[2]/div[2]",
            )
            forcelly_dowload_x_path.click()
            print("forcelly_dowload_x_path element is found and clicked successfully")
            print("Downlading the pdf ............................................")
            time.sleep(10)
            main_download_file = os.path.join(DOWNLOAD_FOLDER, "Tax Deed Surplus.pdf")
            print(f"Downladed the  the pdf {main_download_file}")
        print("main_download_file", main_download_file)
        print(pdfplumber.__file__)  # Shows the file path of the pdfplumber module
        arrClean = []
        with pdfplumber.open(main_download_file) as pdf:
            for page_number, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                table = tables[0]
                data_rows = table[1:]  # Skip the header row
                arrData = []

                for index, value in enumerate(data_rows):
                    if index > 3:
                        arrData.append(value)
                dummyData = []
                address = ""
                a = 1
                for index, value in enumerate(arrData):
                    # print('value', value)
                    if a == 1:
                        dummyData.append(value)
                        a = a + 1
                    elif not value[0]:
                        a = 1
                        dummyData[0].insert(1, address)
                        address = ""
                        arrClean.append(dummyData[0])
                        dummyData = []
                    else:
                        address += value[0]
        merged_df = pd.DataFrame(
            arrClean,
            columns=[
                "PROPERTY OWNER",
                "PROPERTY ADDRESS",
                "APPLICATION",
                "SALE DATE",
                "AMOUNT OF SURPLUS",
                "PARCEL",
                "APPLICATION DATE",
                "CLAIMS",
            ],
        )
        delete_path(main_download_file)
        delete_folder(DOWNLOAD_FOLDER)
        return (
            True,
            "Data Scrapped Successfully",
            format_location(country_name),
            merged_df,
        )
    except (
        NoSuchElementException,
        StaleElementReferenceException,
        WebDriverException,
    ) as e:
        return handle_exception(e, driver_instance)
    except (OSError, IOError, ValueError) as e:
        return handle_exception(e, driver_instance)
    finally:
        if "driver_instance" in locals():
            driver_instance.quit()
