import os
import platform
import shutil


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


def get_the_tesseract_path():
    """
    Configures the path for the Tesseract executable based on the operating system.
    """
    os_name = platform.system()
    if os_name == 'Windows':
        # For Windows
        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    elif os_name == 'Darwin':
        # For macOS
        tesseract_path = '/usr/local/bin/tesseract'
    elif os_name == 'Linux':
        # For Linux
        tesseract_path = '/usr/bin/tesseract'
    else:
        raise EnvironmentError(f"Unsupported operating system: {os_name}")
    print(f"Tesseract path set to: {tesseract_path}")
    return tesseract_path
    