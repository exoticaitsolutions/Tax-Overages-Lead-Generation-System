import os
import re
import time

import pdfplumber
from config import DOWNLOAD_FOLDER
from utils import (
    check_file_downloaded,
    delete_folder,
    delete_path,
    format_location,
    handle_exception,
    print_the_output_statement,
)
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
import pandas as pd


def scrap_shasta_county_california(driver, country_name, country_url, output_text):
    """
    Downloads and extracts data from a PDF containing tax sale results for Shasta County, California.
    Parameters:
        driver (webdriver): An instance of Selenium WebDriver.
        country_name (str): The name of the country (used for logging purposes).
        country_url (str): The URL of the site to scrape (not used in this function).
        output_text (str): Text for output statements and logging.
    Returns:
        tuple: A tuple containing a status boolean, a message, a formatted location string, and the DataFrame with extracted data.
    """
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    pdf_path = os.path.join(DOWNLOAD_FOLDER, "tax_sale_results_1.pdf")
    print_the_output_statement(output_text, f"Opening the site {country_url}")
    try:
        if not check_file_downloaded(DOWNLOAD_FOLDER, "tax_sale_results_1.pdf"):
            pdf_url = "https://www.shastacounty.gov/sites/default/files/fileattachments/tax_collector/page/2691/tax_sale_results_1.pdf"
            print_the_output_statement(
                output_text,
                f"Scraping started for {country_name}. Please wait a few minutes.",
            )
            driver.get(pdf_url)
            print("Downloading the PDF ............................................")
            time.sleep(10)  # Increased wait time
            pdf_path = os.path.join(DOWNLOAD_FOLDER, "tax_sale_results_1.pdf")
            print(f"Downloaded the PDF at {pdf_path}")
        print("PDF Path:", pdf_path)
        data = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                pdf_text = page.extract_text()
                pattern = re.compile(
                    r"(\w+)\s+([\d-]+)\s+(.+?)\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(REDEEMED|WITHDRAWN|NO SALE|\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(.*)?"
                )
                for line in pdf_text.split("\n"):
                    match = pattern.match(line)
                    if match:
                        data.append(
                            match.groups()[1:6]
                        )  # Extract groups from regex match
        print("data", data)
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
        return handle_exception(e, driver)
    except (OSError, IOError, ValueError) as e:
        return handle_exception(e, driver)
    finally:
        if "driver" in locals():
            driver.quit()
