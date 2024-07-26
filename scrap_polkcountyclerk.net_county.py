from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
import csv, os
import pandas as pd
from datetime import datetime

# Set up the Selenium WebDriver (here using Chrome)
driver = webdriver.Chrome()

all_data = []
header = []
# URL to start scraping
url = 'https://www.polkcountyclerk.net/280/Surplus-Funds-List'
driver.get(url)


try:
    # Locate the element with id="isPasted"
    box = driver.find_element(By.XPATH, '//*[@id="isPasted"]')
        
    # Locate the table within the box
    table = box.find_element(By.TAG_NAME, 'tbody')
    # Locate the title row within the box
    title = box.find_element(By.TAG_NAME, 'thead')
    # Locate the rows within the thread
    conts = title.find_elements(By.TAG_NAME, 'tr')
    # Locate the rows within the table
    rows = table.find_elements(By.TAG_NAME, 'tr')
    i=1
    driver.execute_script(f"window.scrollBy(0,0.3);")
    # Iterate over rows and extract data
    for cont in conts:
        cells = cont.find_elements(By.TAG_NAME, 'th')
        header = [cell.text for cell in cells]
        # Remove blank entries
        header = [item for item in header if item]
        print(header)
        break
    # Iterate over rows and extract data
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, 'td')
        row_data = [cell.text for cell in cells]
        if ',' in row_data[3]:
            row_data[3] = row_data[3].replace(',', '')
        print(i,row_data)
        all_data.append(row_data)
        i+=1
    all_data.insert(0, header)
    print("---------------------------------------"*80,all_data)
    print("Page scraped successfully.")
    time.sleep(5)
except Exception as e:
    print(f"Finished scraping. No more pages or encountered an error: {e}")
driver.quit()

# Save data to CSV file
output = os.path.join(os.getcwd(), "output_folder")
if not os.path.exists(output):
        os.makedirs(output)
county_name = 'polkcountyclerk.net'
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f'data_{county_name}_{timestamp}.csv'
csv_file_path = os.path.join(output, f'{filename}')
# csv_file_path = 'scraped_data.csv'
with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerows(all_data)

print(f"Data saved to {csv_file_path}")