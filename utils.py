import json
import os
import importlib
import shutil
import pandas as pd
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QTextCursor
import sys

from config import PHONE_BURNER_USER_ID

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def center_window(window):
    qr = window.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())


def read_json_from_file(filename):
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


def show_message_box(parent, icon_type, title, text):
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


def print_the_output_statement(output, message):
    output.append(f"<b>{message}</b> \n \n")
    # Print the message to the console
    output.moveCursor(QTextCursor.End)
    print(message)


def check_file_downloaded(download_dir, filename):
    """Check if the specified file has been downloaded."""
    files = os.listdir(download_dir)
    if filename in files:
        print(f"File '{filename}' successfully downloaded.")
        return True
    print(f"File '{filename}' not found in the download directory.")
    return False


def save_to_csv(df, csv_path):
    """Save the DataFrame to a CSV file."""
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"Filtered and cleaned data saved to {csv_path}")


def get_function(function_name, module_name="multiple_scrapping"):
    """
    Retrieve a function from a module given its name.

    :param function_name: The name of the function to retrieve.
    :param module_name: The name of the module where the function is defined.
    :return: The function object or None if not found.
    """
    try:
        module = importlib.import_module(module_name)
        func = getattr(module, function_name, None)
        return func
    except ModuleNotFoundError:
        print(f"Module {module_name} not found.")
        return None
    except AttributeError:
        print(f"Function {function_name} not found in module {module_name}.")
        return None


def delete_folder(folder_path):
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


def delete_path(path):
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


def xlsx_to_json(xlsx_file_path):
    df = pd.read_excel(xlsx_file_path)
    data_dict = df.to_dict(orient="records")
    json_data = json.dumps(data_dict, indent=4)
    num_records = len(df)
    header_columns = list(df.columns)
    return header_columns, json_data, num_records


def modification_the_json(json_data_str):
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

    # Convert modified data to JSON string with indentation
    modified_json_data_str = json.dumps(modified_data, indent=4)
    # Get the length of the modified data
    data_length = len(modified_data)

    # Return both the modified JSON string and its length
    return json.loads(json.dumps(modified_data, indent=4)), data_length


def format_location(country_name):
    formatted_location = country_name.replace(" ", "_").lower()
    return formatted_location


def mask_password(password: str) -> str:
    return "*" * len(password)


def update_json_file(new_data):
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


def read_json_file(file_path):
    """
    Read the JSON file and return its contents.
    
    Parameters:
    - file_path (str): The path to the JSON file.
    
    Returns:
    - dict: The contents of the JSON file as a dictionary.
    """
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the file '{file_path}'.")
        return {}
