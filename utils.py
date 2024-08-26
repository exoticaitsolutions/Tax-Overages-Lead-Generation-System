import json
import os
import importlib.util
import shutil
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import pandas as pd
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
    TimeoutException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from PyQt5.QtWidgets import QMessageBox, QDesktopWidget, QWidget, QTextEdit
from PyQt5.QtGui import QTextCursor

from config import PHONE_BURNER_USER_ID

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def wait_and_click(driver, locator_type, locator_value, wait_time=30):
    WebDriverWait(driver, wait_time).until(
        EC.element_to_be_clickable((locator_type, locator_value))
    ).click()


def center_window(window: QWidget) -> None:
    """
    Centers the given window on the screen.
    Args:
        window (QWidget): The window to be centered.
    """
    qr = window.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())


def read_json_from_file(filename: str) -> Optional[Dict[str, Any]]:
    """
    Reads JSON data from a file.
    Args:
        filename (str): The path to the JSON file.
    Returns:
        Optional[Dict[str, Any]]: The JSON data as a dictionary if successful,
        None if an error occurred.
    """
    try:
        with open(filename, "r") as file:
            # Load JSON data from the file
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file '{filename}': {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def show_message_box(
    parent: Optional[QWidget], icon_type: QMessageBox.Icon, title: str, text: str
) -> QMessageBox.StandardButton:
    """
    Displays a message box with the specified icon, title, and text.
    Args:
        parent (Optional[QWidget]): The parent widget for the message box. Can be None.
        icon_type (QMessageBox.Icon): The icon to display in the message box (e.g., QMessageBox.Information, QMessageBox.Warning).
        title (str): The title of the message box window.
        text (str): The text to display in the message box.
    Returns:
        QMessageBox.StandardButton: The button clicked by the user (e.g., QMessageBox.Yes, QMessageBox.No, QMessageBox.Ok).
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(icon_type)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    (
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if icon_type == QMessageBox.Question
        else msg_box.setStandardButtons(QMessageBox.Ok)
    )
    return msg_box.exec_()


def print_the_output_statement(output: QTextEdit, message: str) -> None:
    """
    Appends a formatted message to a QTextEdit widget and prints it to the console.

    Args:
        output (QTextEdit): The QTextEdit widget where the message will be appended.
        message (str): The message to append and print.
    Returns:
        None
    """
    output.append(f"<b>{message}</b> \n \n")
    # Print the message to the console
    output.moveCursor(QTextCursor.End)
    print(message)


def check_file_downloaded(download_dir: str, filename: str) -> bool:
    """
    Checks if the specified file has been downloaded to the given directory.

    Args:
        download_dir (str): The path to the directory where the file should be.
        filename (str): The name of the file to check for.

    Returns:
        bool: True if the file is found in the directory, False otherwise.
    """
    files = os.listdir(download_dir)
    if filename in files:
        print(f"File '{filename}' successfully downloaded.")
        return True
    print(f"File '{filename}' not found in the download directory.")
    return False


def save_to_csv(df: pd.DataFrame, csv_path: str) -> None:
    """
    Saves the DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): The DataFrame to be saved.
        csv_path (str): The path to the CSV file where the DataFrame will be saved.
    Returns:
        None
    """
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"Filtered and cleaned data saved to {csv_path}")


def get_function(function_name: str) -> Optional[Callable]:
    """
    Dynamically loads a module and retrieves a function by its name.
    Args:
        function_name (str): The name of the function to retrieve.
          The function and its module must have the same name.
    Returns:
        Optional[Callable]: The retrieved function if successful, or None
        if the function or module could not be found.
    """

    # Construct the path to the module
    module_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "website_scrapping",
        f"{function_name}.py",
    )

    print(f"Module path: {module_path}")

    try:
        # Check if the module file exists
        if not os.path.isfile(module_path):
            print(f"Module file '{module_path}' does not exist.")
            return None

        # Load the module dynamically
        spec = importlib.util.spec_from_file_location(function_name, module_path)
        if spec is None:
            print(f"Failed to load module specification for '{module_path}'.")
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Retrieve the function from the module
        func = getattr(module, function_name, None)
        if func is None:
            print(
                f"Function '{function_name}' not found in module '{function_name}.py'."
            )
            return None

        return func

    except FileNotFoundError:
        print(f"Module file '{module_path}' does not exist.")
        return None
    except AttributeError as e:
        print(f"An AttributeError occurred: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def delete_folder(folder_path: str) -> None:
    """
    Delete a folder and all its contents.

    Parameters:
    - folder_path (str): The path to the folder to be deleted.
    """
    try:
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            print(f"Directory '{folder_path}' and all its contents have been deleted.")
        else:
            print(f"Directory '{folder_path}' does not exist or is not a directory.")
    except Exception as e:
        print(f"An error occurred while deleting the folder: {e}")


def delete_path(path: str) -> None:
    """
    Delete a file or folder and all its contents if it's a directory.

    Parameters:
    - path (str): The path to the file or folder to be deleted.
    """
    try:
        if os.path.isdir(path):
            # If the path is a directory, delete it and all its contents
            shutil.rmtree(path)
            print(f"Directory '{path}' and all its contents have been deleted.")
        elif os.path.isfile(path):
            # If the path is a file, delete it
            os.remove(path)
            print(f"File '{path}' has been deleted.")
        else:
            print(f"Path '{path}' does not exist or is not a file or directory.")
    except Exception as e:
        print(f"An error occurred while deleting the path: {e}")


def xlsx_to_json(xlsx_file_path: str) -> Tuple[List[str], str, int]:
    """
    Converts an Excel file to JSON format and returns details about the data.
    Args:
        xlsx_file_path (str): The path to the Excel file to be converted.
    Returns:
        Tuple[List[str], str, int]: A tuple containing:
            - A list of column headers (List[str]).
            - The JSON representation of the data (str).
            - The number of records in the Excel file (int).
    """
    df = pd.read_excel(xlsx_file_path)
    data_dict = df.to_dict(orient="records")
    json_data = json.dumps(data_dict, indent=4)
    num_records = len(df)
    header_columns = list(df.columns)
    return header_columns, json_data, num_records


def modification_the_json(
    json_data_str: str
) -> Tuple[Dict[str, Any], int]:
    """
    Modify JSON data by renaming keys according to a header mapping and adding an 'owner_id' field.

    Args:
        json_data_str (str): A JSON string representing a list of records.
        phone_burner_user_id (Any): The user ID to be added as the 'owner_id' in each record.
    Returns:
        Tuple[Dict[str, Any], int]: A tuple containing:
            - The modified JSON data as a dictionary.
            - The number of records in the modified JSON data.
    """
    header_mapping = {
        "First Name": "first_name",
        "Last Name": "last_name",
        "Email": "email",
        "Phone": "phone",
        "Address Line 1": "address1",
        "Address Line 2": "address2",
        "City": "city",
        "State": "state",
        "Zip": "zip",
        "owner_id": "owner_id",
    }

    # Load the JSON data from the string
    data = json.loads(json_data_str)

    # Check if data is a list
    if not isinstance(data, list):
        raise ValueError("JSON data must be a list of records")

    # Define the PHONE_BURNER_USER_ID (passed as argument)
    phone_burner_user_id = str(PHONE_BURNER_USER_ID)
    # Iterate through each record and modify it
    modified_data = []
    for record in data:
        new_record = {}
        for old_key, new_key in header_mapping.items():
            if old_key in record:
                new_record[new_key] = record[old_key]
        new_record["owner_id"] = phone_burner_user_id
        modified_data.append(new_record)
    data_length = len(modified_data)
    return json.loads(json.dumps(modified_data, indent=4)), data_length


def format_location(country_name: str) -> str:
    """
    Format the country name by replacing spaces with underscores and converting to lowercase.
    Args:
        country_name (str): The name of the country to format.
    Returns:
        str: The formatted country name, where spaces are replaced with underscores and all characters are lowercase.
    """
    formatted_location = country_name.replace(" ", "_").lower()
    return formatted_location


def mask_password(password: str) -> str:
    """
    Mask the given password by replacing each character with an asterisk (*).
    Args:
        password (str): The password to be masked.
    Returns:
        str: A string where each character of the input password is replaced by an asterisk.
    """
    return "*" * len(password)


def update_json_file(new_data: Dict[str, any], file_path: str = "token.json") -> None:
    """
    Update the JSON file with new data. If the file does not exist, it will be created.

    Parameters:
    - file_path (str): The path to the JSON file.
    - new_data (dict): A dictionary containing the new data to update.
    """
    # Read the existing data from the JSON file
    try:
        file_path = "token.json"
        with open(file_path, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist, start with an empty dictionary
        data = {}

    # Check and update the data
    for key, value in new_data.items():
        if key in data:
            print(f"Key '{key}' found. Updating value to '{value}'")
        else:
            print(f"Key '{key}' not found. Adding key '{key}' with value '{value}'")

    # Update the data dictionary with the new data
    data.update(new_data)

    # Write the updated data back to the JSON file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

    print(f"Data has been updated in {file_path}")


def has_significant_data(data: Any) -> bool:
    """
    Check if the provided data has significant content based on predefined criteria.

    Args:
        data (Any): The data to check for significance. Can be of any type.

    Returns:
        bool: True if the data meets the criteria for significance, False otherwise.

    Criteria for 'significant' data:
        - Non-empty dictionary
        - Non-empty list
        - Non-empty string
        - Non-zero number
        - Non-None value
    """
    if data:
        # Example criteria for 'significant' data:
        # Check if it's a non-empty dictionary or list
        if isinstance(data, (dict, list)) and len(data) > 0:
            return True
        # Add more criteria if needed
    return False


def find_element_with_retry(
    driver_instance: WebDriver, by: By, value: str, retries: int = 3, wait_time: int = 3
) -> Any:
    """
    Attempt to find an element with retries.
    Args:
        driver_instance (WebDriver): The Selenium WebDriver instance to use for finding the element.
        by (By): The method to locate the element (e.g., By.XPATH, By.ID).
        value (str): The value to locate the element by.
        retries (int, optional): The number of times to retry finding the element. Defaults to 3.
        wait_time (int, optional): The time (in seconds) to wait between retries. Defaults to 3.
    Returns:
        Any: The found web element.
    Raises:
        NoSuchElementException: If the element could not be found after all retries.
    """
    for _ in range(retries):
        try:
            element = WebDriverWait(driver_instance, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except StaleElementReferenceException:
            print("Stale element reference. Retrying...")
            time.sleep(wait_time)
    raise NoSuchElementException(f"Element with {by} and {value} could not be found.")


def handle_exception(
    exception: Exception, driver_instance: WebDriver
) -> Tuple[bool, str, str, str]:
    print(f"An error occurred: {exception}")
    """
    Handle an exception by logging the error and quitting the WebDriver instance if provided.

    Args:
        exception (Exception): The exception that was raised.
        driver_instance (WebDriver): The Selenium WebDriver instance to quit if it is not None.

    Returns:
        Tuple[bool, str, str, str]: A tuple where:
            - The first element is False indicating an error occurred.
            - The second element is the error message.
            - The third and fourth elements are empty strings.
    """
    if driver_instance:
        driver_instance.quit()
    return False, f"An error occurred: {exception}", "", ""


def checked_url(driver: WebDriver, url: str, country_name: str) -> bool:
    """
    Check if the URL results in a '403 Forbidden' error for a specific country.
    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        url (str): The URL to check.
        country_name (str): The name of the country to match for specific checks.

    Returns:
        bool: True if no '403 Forbidden' error is detected, False otherwise.
    """
    if country_name == "Sarasota County Florida":
        try:
            driver.get(url)
            # Reduced sleep time or removed if not necessary
            time.sleep(2)  # Use a shorter delay if needed
            if (
                driver.find_element(By.XPATH, "/html/body/center/h1").text
                == "403 Forbidden"
            ):
                print("403 Forbidden error detected.")
                return False
            print("No 403 Forbidden error.")
            return True
        except (
            NoSuchElementException,
            StaleElementReferenceException,
            WebDriverException,
        ):
            print("403 Forbidden error element not found.")
            return True
