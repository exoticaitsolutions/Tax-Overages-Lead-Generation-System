
import json
import os
import importlib
import shutil

from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QTextCursor

def center_window(window):
    qr = window.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())

def read_json_from_file(filename):
    try:
        with open(filename, 'r') as file:
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
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Filtered and cleaned data saved to {csv_path}")


def get_function(function_name, module_name='multiple_scrapping'):
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