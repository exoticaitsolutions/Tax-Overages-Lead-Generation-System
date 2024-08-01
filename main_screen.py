import os
import sys
import time
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from threading import Thread
from config import (
    APP_NAME,
    APP_TITLE,
    CURRENT_DATE,
    FILE_TYPE,
    JSON_FILE_NAME,
    NEW_EVENT_LOOP,
    START_TIME,
    THREAD_EVENT,
)
from crm_intergation import intergation_with_phoneburner_crn
from utils import (
    center_window,
    get_function,
    print_the_output_statement,
    read_json_from_file,
    save_to_csv,
    show_message_box,
    xlsx_to_json,
)
from web_driver import initialize_driver

bootstrap_style = """
QWidget { font-family: Arial, sans-serif; font-size: 14px; }
QMainWindow { background-color: #f8f9fa; }
QLabel { color: #212529; }
QLineEdit { border: 1px solid #ced4da; border-radius: 4px; padding: 5px; font-size: 14px; color: #495057; }
QLineEdit:focus { border-color: #80bdff; outline: 0; background-color: rgba(0, 123, 255, 0.1); }
QPushButton { background-color: #007bff; border: 1px solid #007bff; border-radius: 4px; color: white; padding: 5px 10px; font-size: 14px; }
QPushButton:hover { background-color: #0056b3; border-color: #0056b3; }
QPushButton:disabled { background-color: #6c757d; border-color: #6c757d; color: white; }
QTextEdit { border: 1px solid #ced4da; border-radius: 4px; padding: 5px; font-size: 14px; color: #495057; background-color: white; }
"""


class Worker(QObject):
    scrapping_finish = pyqtSignal(bool, str, str)
    intergation_finished = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()

    def run_the_scrapping_thread(
        self,
        loop,
        driver_instance,
        country_name,
        country_url,
        custom_function_name,
        output_text,
        scrape_thread_event,
    ):
        try:
            scrapping_function = get_function(custom_function_name)
            if scrapping_function:
                global csv_data
                status, scrapping_status, file_name, csv_data = scrapping_function(
                    driver_instance, country_name, country_url, output_text
                )
                self.scrapping_finish.emit(status, scrapping_status, file_name)
            else:
                self.scrapping_finish.emit(False, "Function not found", "")
        except Exception as e:
            self.scrapping_finish.emit(False, f"Error occurred: {e}", "")
        finally:
            scrape_thread_event.set()

    def run_intergation_thread(
        self, loop, json_data_str, output_text, scrape_thread_event
    ):
        try:
            status, intergationStatus = intergation_with_phoneburner_crn(
                json_data_str, output_text
            )
            self.intergation_finished.emit(status, intergationStatus)
        except Exception as e:
            self.intergation_finished.emit(False, f"Error occurred: {e}")
        finally:
            scrape_thread_event.set()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(500, 600, 800, 500)
        center_window(self)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        app_title_label = QLabel(f"<h1>{APP_NAME}</h1>")
        app_title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(app_title_label)

        font = QFont()
        font.setBold(True)

        form_layout = QVBoxLayout()
        form_layout.addSpacing(20)
        layout.addLayout(form_layout)

        form_layout.addWidget(QLabel("<b>Select a country for Scrapping:</b>"))
        self.country_combo_box = QComboBox()
        self.country_combo_box.addItem("Select Country")
        data = read_json_from_file(JSON_FILE_NAME)
        if data:
            for website in data.get("websites", []):
                name = website.get("name")
                url = website.get("url")
                function_name = website.get("function_name")
                self.country_combo_box.addItem(name, (url, function_name))
        else:
            self.country_combo_box.addItem("No countries available")
        self.country_combo_box.setFont(font)
        self.country_combo_box.setStyleSheet("height: 30px;")
        form_layout.addWidget(self.country_combo_box)
        form_layout.addWidget(
            QLabel("<i>Please choose a country from the dropdown menu.</i>")
        )

        button_layout = QHBoxLayout()
        form_layout.addLayout(button_layout)

        self.scrapping_button = QPushButton("Scrap Country Website")
        self.scrapping_button.setFont(font)
        self.scrapping_button.clicked.connect(self.multiple_site_scrapping)
        button_layout.addWidget(self.scrapping_button)

        self.close_button = QPushButton("Close Window")
        self.close_button.setFont(font)
        self.close_button.clicked.connect(self.closed_window)
        button_layout.addWidget(self.close_button)

        bottom_button_layout = QHBoxLayout()
        layout.addLayout(bottom_button_layout)

        self.upload_csv_button = QPushButton("Intergate with Skip Matrix")
        self.upload_csv_button.setEnabled(False)
        self.upload_csv_button.setFont(font)
        bottom_button_layout.addWidget(self.upload_csv_button)

        self.intergate_with_crm = QPushButton("Intergate With CRM")
        self.intergate_with_crm.setFont(font)
        self.intergate_with_crm.clicked.connect(self.intergate_with_crm_function)
        bottom_button_layout.addWidget(self.intergate_with_crm)

        layout.addWidget(QLabel("<b>Output:</b>"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Arial", 12))
        layout.addWidget(self.output_text)

    def multiple_site_scrapping(self):
        self.output_text.clear()
        index = self.country_combo_box.currentIndex()
        self.scrapping_button.setEnabled(False)
        if index == 0:
            show_message_box(
                self,
                QMessageBox.Warning,
                "Validation Error",
                "No country selected. Please choose a country from the dropdown menu.",
            )
            self.scrapping_button.setEnabled(True)
        else:
            name = self.country_combo_box.currentText()
            url, function_name = self.country_combo_box.itemData(index)
            global driver
            driver = initialize_driver(NEW_EVENT_LOOP)
            self.worker = Worker()
            self.worker.scrapping_finish.connect(self.on_scrapping_finished)
            scrape_thread = Thread(
                target=self.worker.run_the_scrapping_thread,
                args=(
                    NEW_EVENT_LOOP,
                    driver,
                    name,
                    url,
                    function_name,
                    self.output_text,
                    THREAD_EVENT,
                ),
            )
            scrape_thread.start()

    def on_scrapping_finished(self, status, scrapping_status, file_name):
        if status:
            print_the_output_statement(self.output_text, scrapping_status)
            options = QFileDialog.Options()
            folder_path = QFileDialog.getExistingDirectory(
                self, "Select Directory", options=options
            )
            if folder_path:
                output_csv_path = os.path.join(
                    folder_path,
                    f'{file_name}_{CURRENT_DATE.strftime("%Y_%B_%d")}.{FILE_TYPE}',
                )
                save_to_csv(csv_data, output_csv_path)
                print_the_output_statement(
                    self.output_text, f"Data saved successfully to {output_csv_path}"
                )
                show_message_box(
                    self,
                    QMessageBox.NoIcon,
                    "Success",
                    f"Data saved successfully to {output_csv_path}",
                )
            else:
                show_message_box(
                    self, QMessageBox.Warning, "Error", "Data found but failed to save."
                )
        else:
            show_message_box(self, QMessageBox.Warning, "Error", scrapping_status)
        driver.quit()
        self.scrapping_button.setEnabled(True)
        total_time = time.time() - START_TIME
        print_the_output_statement(
            self.output_text, f"Total execution time: {total_time:.2f} seconds"
        )

    def upload_excel(self):
        print("Excel upload function is not yet implemented.")

    def on_intergation_finished(self, status, scrapping_status):
        if status:
            print_the_output_statement(self.output_text, scrapping_status)
            show_message_box(self, QMessageBox.NoIcon, "Success", scrapping_status)
        else:
            show_message_box(self, QMessageBox.Warning, "Error", scrapping_status)
        self.intergate_with_crm.setEnabled(True)
        total_time = time.time() - START_TIME
        print_the_output_statement(
            self.output_text, f"Total execution time: {total_time:.2f} seconds"
        )

    def intergate_with_crm_function(self):
        self.output_text.clear()
        print_the_output_statement(self.output_text, "Uploading Excel...")
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "Excel Files (*.xlsx)", options=options
        )
        if file_path:
            self.intergate_with_crm.setEnabled(False)
            print_the_output_statement(
                self.output_text, f"Excel file selected: {file_path}"
            )
            csv_header, json_data_str, num_records = xlsx_to_json(file_path)
            print("csv_header", csv_header)
            if num_records > 0:
                missing_headers = [
                    header
                    for header in [
                        "First Name",
                        "Last Name",
                        "Phone",
                        "Email",
                        "Address Line 1",
                        "Address Line 2",
                        "City ",
                        "State ",
                        "Zip",
                    ]
                    if header not in csv_header
                ]
                if missing_headers:
                    self.intergate_with_crm.setEnabled(True)
                    show_message_box(
                        self,
                        QMessageBox.Warning,
                        "File Error",
                        "Missing headers in the Excel file. Please choose the correct file.",
                    )
                else:
                    self.worker = Worker()
                    self.worker.intergation_finished.connect(
                        self.on_intergation_finished
                    )
                    scrape_thread = Thread(
                        target=self.worker.run_intergation_thread,
                        args=(
                            NEW_EVENT_LOOP,
                            json_data_str,
                            self.output_text,
                            THREAD_EVENT,
                        ),
                    )
                    scrape_thread.start()
            else:
                self.intergate_with_crm.setEnabled(True)
                show_message_box(
                    self,
                    QMessageBox.Warning,
                    "File Error",
                    "Excel file is empty. Please choose another file.",
                )
        else:
            self.intergate_with_crm.setEnabled(True)
            show_message_box(
                self,
                QMessageBox.Warning,
                "File Error",
                "Please choose the correct Excel file.",
            )

    def closed_window(self):
        reply = QMessageBox.question(
            self,
            "Close",
            "Are you sure you want to close the window?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.close()
            if "driver" in globals():
                driver.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(bootstrap_style)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
