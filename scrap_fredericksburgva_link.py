import platform
import time
import pdfplumber
import os
import io
import pytesseract
from PIL import Image

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from screeninfo import get_monitors
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import pandas as pd

from comman_function import delete_folder, delete_path




# Get the primary monitor's resolution
monitor = get_monitors()[0]

def initialize_driver(download_dir):
    temp_directory = ""
    chrome_options = Options()
    # Get the monitor's width and height
    width = monitor.width
    height = monitor.height
    window_size = f'{width},{height}'
    print(f"Window Size: {window_size}")
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument(f'--window-size={window_size}')
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--verbose')
    chrome_options.add_experimental_option("prefs", {
           "download.default_directory": download_dir,
        "plugins.always_open_pdf_externally": True,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    })
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chromedriver_path = ChromeDriverManager().install()
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service = service ,options = chrome_options)
    return driver

def check_file_downloaded(download_dir, filename):
    files = os.listdir(download_dir)
    if filename in files:
        print(f"File '{filename}' successfully downloaded.")
        return True 
    else:
        print(f"File '{filename}' not found in the download directory.")
        return False
def Scrapping_the_data(driver, scrapping_url ,download_dir, expected_filename):
    checked = check_file_downloaded(download_dir, expected_filename)
    if checked:
        download_pdf = os.path.join(download_dir, expected_filename)
    else:
        # Open the target webpage
        print(f'Openign the url {scrapping_url}')
        driver.get(scrapping_url)
        time.sleep(5)
        xpath = '//*[@id="divEditorf07f49c4-e833-4363-b38a-c2847c5c0205"]/div/ul[10]/li[8]/a'
        actions = ActionChains(driver)
            # Locate the download element
        download_element = driver.find_element(By.XPATH, xpath)
        actions = ActionChains(driver)
        actions.move_to_element(download_element).perform()
        download_element.click()
        print('Download element clicked successfully')
        time.sleep(10)
        download_pdf = os.path.join(download_dir, expected_filename)
    return True ,download_pdf


def configure_tesseract_path():
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

    # Set the Tesseract path in pytesseract
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

    print(f"Tesseract path set to: {tesseract_path}")

def extract_images_from_pdf(pdf_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages):
            # Convert the page to an image
            page_image = page.to_image()
            img_data = page_image.original
            # Save the full-page image
            img_path = os.path.join(output_folder, f"page_{page_number+1}.png")
            img_data.save(img_path)
            print(f"Saved page image to {img_path}")

def ocr_images(image_folder, output_text_file):
    configure_tesseract_path()  # Ensure Tesseract path is configured
    with open(output_text_file, 'w') as f:
        for img_file in os.listdir(image_folder):
            if img_file.endswith(".png"):
                img_path = os.path.join(image_folder, img_file)
                img = Image.open(img_path)
                text = pytesseract.image_to_string(img)
                f.write(f"--- {img_file} ---\n")
                f.write(text)
                f.write("\n\n")
                print(f"Extracted text from {img_file}")


if __name__ == "__main__":
    
    # Create the download directory if it does not exist
    download_dir = os.path.join(os.getcwd(), "downloads")
    output_folder = os.path.join(os.getcwd(), "output_images")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    output = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output):
        os.makedirs(output)
    text_output_file = os.path.join(output, 'extracted_text.txt')
    # text_output_file = "extracted_text.txt"
    expected_filename ='_BU11_7.pdf'
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    driver = initialize_driver(download_dir)
    url = "https://www.fredericksburgva.gov/1142/Surplus-Funds"
    status , downlaod_file = Scrapping_the_data(driver, url,download_dir, expected_filename )
    print('downlaod_file', downlaod_file)
    if status :
        print('json_response', downlaod_file)
        extract_images_from_pdf(downlaod_file, output_folder)
        ocr_images(output_folder, text_output_file)
        # pdf_to_json(downlaod_file,'downlaod_file1.json')
        delete_path(output_folder)
        delete_folder(output_folder)
    else:
        print('SOmethign Wrong ')
    driver.quit()