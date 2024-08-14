import time
import pandas as pd
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from utils import format_location, handle_exception, print_the_output_statement


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
