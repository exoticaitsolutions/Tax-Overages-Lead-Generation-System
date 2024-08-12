import importlib
import json
import os
import shutil
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QMessageBox

def center_window(window):
    """
    Centers the given window on the screen.

    Parameters:
        window (QWidget): The window to be centered.
    """
    qr = window.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())


def read_json_from_file(filename):
    """
    Reads JSON data from a file.

    Parameters:
        filename (str): The path to the JSON file to be read.

    Returns:
        dict or None: The JSON data as a dictionary if successful, or None if an error occurs.
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


def print_the_output_statement(output_text, message,html_print):
        """Updates the output text with the provided HTML message."""
        if html_print:
            output_text.setHtml(f"<b>{message}</b> \n \n")
        else:
            output_text.append(f"<b>{message}</b> \n \n")

        output_text.moveCursor(QTextCursor.End)
        print(message)


def show_message_box(parent, icon_type, title, text):
    """
    Displays a message box with specified icon, title, and text.
    Parameters:
        parent (QWidget): The parent widget for the message box.
        icon_type (QMessageBox.Icon): The icon type to be displayed in the message box (e.g., QMessageBox.Information, QMessageBox.Warning, QMessageBox.Question).
        title (str): The title of the message box window.
        text (str): The text message to be displayed in the message box.
    Returns:
        int: The result of the message box (e.g., QMessageBox.Yes, QMessageBox.No, QMessageBox.Ok).
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



def get_function(function_name):
    # Construct the path to the module
    module_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "website_scrapping",
        f"{function_name}.py"
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
            print(f"Function '{function_name}' not found in module '{function_name}.py'.")
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
    


def save_to_csv(df, csv_path):
    """Save the DataFrame to a CSV file."""
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"Filtered and cleaned data saved to {csv_path}")



def format_location(country_name):
    formatted_location = country_name.replace(" ", "_").lower()
    return formatted_location



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