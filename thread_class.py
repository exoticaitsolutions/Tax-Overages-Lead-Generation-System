from PyQt5.QtCore import Qt, pyqtSignal, QObject
from globals import csv_data
import pandas as pd
class Worker(QObject):
    scrapping_finish = pyqtSignal(bool, str, str, pd.DataFrame)
    # intergation_finished = pyqtSignal(bool, str)
    def __init__(self):
        super().__init__()
    def run_the_scrapping_thread(
        self,
        driver_instance,
        country_name,
        country_url,
        import_custom_function,
        output_text,
        scrape_thread_event,
    ):
        try:
            status, scrapping_status, file_name, csv_data = import_custom_function(driver_instance, country_name, country_url, output_text)
            self.scrapping_finish.emit(status, scrapping_status, file_name, csv_data)
        except Exception as e:
            self.scrapping_finish.emit(False, f"Error occurred: {e}", "")
        finally:
            scrape_thread_event.set()