import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import pandas as pd
import os
from datetime import datetime

# Initialize the WebDriver
driver = webdriver.Chrome()
driver.get("https://courts.delaware.gov/superior/rightfulowner/sale_n_p1.aspx#p")
sleep(6)

# Locate the table
table = driver.find_element(By.CLASS_NAME, 'table')

# Extract table headers
headers = [header.text for header in table.find_elements(By.XPATH, './/thead//th')]

# Extract table rows
rows = []
for row in table.find_elements(By.XPATH, './/tbody//tr'):
    cells = [cell.text for cell in row.find_elements(By.XPATH, './/td')]
    rows.append(cells)

# Save data to CSV
with open('table_data.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(headers)  # Write the header row
    writer.writerows(rows)    # Write the data rows

# Close the WebDriver
driver.quit()

import pandas as pd

# Define the columns of interest
columns_of_interest = [
    "Property Address", "Prior Owner", "Parcel ID", "Opening Bid",
    "Sale Price", "Surplus amount", "Sale Date", "Case Number",
    "Applicant/Purchaser"
]

# Mapping rules
mapping = {
    "Property Address": "Address (Sheriff's Sale)",
    "Prior Owner": "First Name",
    "Parcel ID": "Parcel ID",
    "Opening Bid": "Opening Bid",
    "Sale Price": "Sale Price",
    "Surplus amount": "Court-Held\nAmount",
    "Sale Date": "Sale Date",
    "Case Number": "Case Number",
    "Applicant/Purchaser": "Applicant/Purchaser"
}

# Load the original CSV file
df = pd.read_csv('table_data.csv')

# Debug: Print columns in the original DataFrame
print("Original columns:", df.columns)

# Debug: Check if the 'Court-Held\nAmount' column has data
print("Court-Held Amount data:", df['Court-Held\nAmount'].head())

# Create a new DataFrame with the columns of interest
new_df = pd.DataFrame(columns=columns_of_interest)
county_name = 'courts.delaware'
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f'table_data_{county_name}_{timestamp}.csv'

# Map and insert data
for new_col, old_col in mapping.items():
    if old_col in df.columns:
        if new_col == "Prior Owner":
            # Combine 'First Name' and 'Last Name' into 'Prior Owner'
            if 'First Name' in df.columns and 'Last Name' in df.columns:
                new_df[new_col] = df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)
            else:
                new_df[new_col] = None
        else:
            new_df[new_col] = df[old_col]
    else:
        new_df[new_col] = None

# Fill missing values
new_df = new_df.fillna('null')
os.remove('table_data.csv')
# Save the new DataFrame to a new CSV file
# new_df.to_csv('new_table_data.csv', index=False)
output_folder = 'output_folder'
# Create the folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)
new_filename = os.path.join(output_folder, f'new_table_data_{county_name}_{timestamp}.csv')

# Save the new DataFrame to a new CSV file
new_df.to_csv(new_filename, index=False)