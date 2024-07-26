import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import pandas as pd
import os

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

# Load the original CSV file
input_csv_file = 'table_data.csv'  # Replace with your CSV file name
df = pd.read_csv(input_csv_file)

# Define the columns of interest
columns_of_interest = [
    "Property Address", "Prior Owner", "Parcel ID", "Opening Bid",
    "Sale Price", "Surplus amount", "Sale Date", "Case Number",
    "Applicant/Purchaser"
]

# Ensure all columns of interest are present in the DataFrame
for column in columns_of_interest:
    if column not in df.columns:
        df[column] = 'null'  # Add missing columns with 'null' values

# Reorder the DataFrame to have columns in the desired order
df = df[columns_of_interest]

# Replace empty cells with 'null'
df = df.fillna('null')

# Save to a single CSV file
output = os.path.join(os.getcwd(), "output")
if not os.path.exists(output):
        os.makedirs(output)
output_csv_file = os.path.join(output, 'filtered_data.csv')
# output_csv_file = 'filtered_data.csv'
df.to_csv(output_csv_file, index=False)
os.remove('table_data.csv')
print(f'Saved filtered data to {output_csv_file}')
