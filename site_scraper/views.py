import time
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from .scrapping import scrape_delaware_county_court_data, process_csv_file
import os

class TaxOveragesView(View):
    def get(self, request):
        return render(request, 'site_scraper/index.html')

class DelawareCountyCourtScraper(View):
    def get(self, request):
        start_time = time.time()
        csv_file_path = scrape_delaware_county_court_data()
        new_filename = process_csv_file(csv_file_path)

        # Provide the CSV file for download
        with open(new_filename, 'r') as file:
            response = HttpResponse(file.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(new_filename)}'

        # Cleanup: Remove the new file after sending it
        # os.remove('table_data.csv')
        end_time = time.time()
        total_time = end_time - start_time
        print() 
        print(f"Total execution time: {total_time:.2f} seconds")

        return response
