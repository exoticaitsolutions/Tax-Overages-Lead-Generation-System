import os
import pytesseract
from pdf2image import convert_from_path
import re
import csv
from datetime import datetime

from screeninfo import get_monitors
from Common import get_the_tesseract_path


# Application Settings
REPORT_FOLDER = os.path.join(os.getcwd(), "output")
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
CURRENT_DATE = datetime.now()
FILE_NAME = "fredericksburgva"
FILE_TYPE = "csv"
EXPECTED_OUTPUT_FILE = '_BU11_7.pdf'
APP_URL = "https://www.fredericksburgva.gov/1142/Surplus-Funds"
monitor = get_monitors()[0]
WIDTH = monitor.width
HEIGHT = monitor.height

if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
if not os.path.exists(REPORT_FOLDER):
        os.makedirs(REPORT_FOLDER)
# Path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = get_the_tesseract_path()

# Path to the PDF file
# pdf_path = r'C:\Users\rohit\Downloads\_BU11_7.pdf'
pdf_path = os.path.join(DOWNLOAD_FOLDER, '_BU11_7-pages-1.pdf')
delimiter="##"
delimiter2="|"

# Define regular expression patterns
date_pattern = re.compile(r'\d{2}/\d{2}/\d{4}')
money_pattern = re.compile(r'(?:\d{1,3}(?:,\d{3})*|\d+)?\.\d{2}')


# Function to classify data into columns
def classify_data(data):
    columns = []
    temp = [" ", " ", " ", " "]

    for item in data.split(' '):
        if date_pattern.match(item):
            if temp[0] == " ":
                temp[0] = item
            elif temp[1] == " ":
                temp[1] = item
            elif temp[3] == " ":
                temp[3] = item
        elif money_pattern.match(item):
            if temp[2] == " ":
                temp[2] = item

        if temp.count(" ") == 0:
            columns.append(temp)
            temp = [" ", " ", " ", " "]
    
    if temp != [" ", " ", " ", " "]:
        columns.append(temp)

    return columns


# Convert PDF pages to images
pages = convert_from_path(pdf_path, 300)

# Extract text from each page
data_str = ""
for page in pages:
    data_str += pytesseract.image_to_string(page)

# Print the extracted text to understand its structure
print("Extracted text:")


# Clean up the text
# data_str = re.sub(r'\s+', ' ', data_str)
data_str = re.sub(r'\n', delimiter, data_str)
print(data_str)

# Define regex patterns for each section
patterns = {
    "case_to_account_of": r'##CASE##(.*?)##ACCOUNT OF##',
    "account_of_to_collection_date": r'##ACCOUNT OF##(.*?)##FREDERICKSBURG CITY CIRCUIT COURT##',
    "pay_date_to_restitution_balance": r'##DATE BALANCE INTEREST DT(.*?)##REST INTEREST##',
    "collection_balance_to_page": r'##BALANCE##(.*?)##PAGE:##',
}

# Extract data based on the patterns
sections = {}
for key, pattern in patterns.items():
    sections[key] = re.findall(pattern, data_str)

# Ensure all sections have the same length
max_length = max(len(section) for section in sections.values())
for key in sections:
    while len(sections[key]) < max_length:
        sections[key].append('')

print(f"----------------------- {max_length} --------------------------")
# List to hold the grouped elements
grouped_data = [''] * 3000  # Initialize grouped_data with empty strings

# Print each row of data
for i in range(max_length):
    row = []
    for key in sections:
        data=sections[key][i]

        # Split the data into a new array by "##"
        data_array = data.split(delimiter)
        # print(" >>>>>>>> ",{key})
        
        x=0
        for index, item in enumerate(data_array):
            if item:  # Check if the item is not empty
                if(key=="pay_date_to_restitution_balance"):              
                    for row in classify_data(item):
                        row_combined = " | ".join(row)
                        # print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")                        
                        item=row_combined
                grouped_data[x] += f'{item}{delimiter2}'
                x += 1
                print(f"{x} - {item}")
        print("-------------------------------------------------")
        row.append(data)
        # print(data)

    # Join the row and print it if needed
    print("-------------------------------------------------")
    # for final_data in grouped_data:
    #     print(final_data)


# Print the grouped_data
print("Grouped Data:")
for data in grouped_data:
    print(data)

# Write the grouped_data to a CSV file
# csv_file_path = 'output_folder/output.csv'
csv_file_path = os.path.join( REPORT_FOLDER, f'{FILE_NAME}_{CURRENT_DATE.strftime("%Y_%B_%d")}.{FILE_TYPE}')
with open(csv_file_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["CASE", "ACCOUNT OF", "COLLECTION DATE", "PAY DATE", "RESTITUTION BALANCE", "RESTITUTION INTEREST DT", "REST INTEREST BALANCE"]) 
    for data in grouped_data:
        writer.writerow(data.split("|"))

print("Data extraction complete and CSV file created.")

print("Data extraction complete.")