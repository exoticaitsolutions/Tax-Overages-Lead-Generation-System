import os
import sys
import time
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont
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
from utils import (
    center_window,
    get_function,
    print_the_output_statement,
    read_json_from_file,
    save_to_csv,
    show_message_box,
)
from web_driver import initialize_driver

bootstrap_style = """
QWidget {
    font-family: Arial, sans-serif;
    font-size: 14px;
}
QMainWindow {
    background-color: #f8f9fa;
}
QLabel {
    color: #212529;
}
QLineEdit {
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 5px;
    font-size: 14px;
    color: #495057;
}
QLineEdit:focus {
    border-color: #80bdff;
    outline: 0;
    background-color: rgba(0, 123, 255, 0.1); /* Simulating box-shadow effect */
}
QPushButton {
    background-color: #007bff;
    border: 1px solid #007bff;
    border-radius: 4px;
    color: white;
    padding: 5px 10px;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #0056b3;
    border-color: #0056b3;
}
QPushButton:disabled {
    background-color: #6c757d;
    border-color: #6c757d;
    color: white;
}
QTextEdit {
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 5px;
    font-size: 14px;
    color: #495057;
    background-color: white;
}
"""

class Worker(QObject):
    scrapping_finish = pyqtSignal(bool, str, str)

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
            # asyncio.set_event_loop(loop)
            print("custom_function_name", custom_function_name)
            scrapping_function = get_function(custom_function_name)
            if scrapping_function:
                global csv_data
                status, scrapping_status, file_name, csv_data = scrapping_function(
                    driver_instance, country_name, country_url, output_text
                )
                self.scrapping_finish.emit(status, scrapping_status, file_name)
            else:
                print(f"Function {custom_function_name} not found.")
                self.scrapping_finish.emit(False, "Function not found", "")
        except Exception as e:
            # Handle any exceptions that may occur during scraping
            print(f"An error occurred: {str(e)}")
            self.scrapping_finish.emit(False, str(e), "")
        finally:
            scrape_thread_event.set()
            try:
                driver_instance.quit()
            except Exception as e:
                print(f"Failed to quit driver: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.driver = None  # Initialize driver variable
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
            websites = data.get("websites", [])
            for website in websites:
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

        self.scrapping_button = QPushButton("Scrap Country Website ")
        self.scrapping_button.setFont(font)
        self.scrapping_button.clicked.connect(self.multiple_site_scrapping)
        button_layout.addWidget(self.scrapping_button)

        self.close_button = QPushButton("Close Window")
        self.close_button.clicked.connect(self.closed_window)
        self.close_button.setFont(font)
        button_layout.addWidget(self.close_button)

        bottom_button_layout = QHBoxLayout()
        layout.addLayout(bottom_button_layout)

        self.upload_csv_button = QPushButton("Intergate with Skip Matrix")
        self.upload_csv_button.setEnabled(False)
        self.upload_csv_button.clicked.connect(self.upload_excel)
        self.upload_csv_button.setEnabled(False)
        self.upload_csv_button.setFont(font)
        bottom_button_layout.addWidget(self.upload_csv_button)

        self.intergate_with_crm = QPushButton("Intergate With CRM")
        self.intergate_with_crm.setEnabled(False)
        self.intergate_with_crm.clicked.connect(self.intergate_with_crm_function)
        self.intergate_with_crm.setFont(font)
        bottom_button_layout.addWidget(self.intergate_with_crm)

        layout.addWidget(QLabel("<b>Output:</b>"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Arial", 12))
        layout.addWidget(self.output_text)

    def multiple_site_scrapping(self):
        index = self.country_combo_box.currentIndex()
        self.scrapping_button.setEnabled(True)
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
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    print(f"Failed to quit previous driver: {str(e)}")
            self.driver = initialize_driver(NEW_EVENT_LOOP)
            self.worker = Worker()
            self.worker.scrapping_finish.connect(self.on_scrapping_finished)
            scrape_thread = Thread(
                target=self.worker.run_the_scrapping_thread,
                args=(
                    NEW_EVENT_LOOP,
                    self.driver,
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
                    self,
                    QMessageBox.Warning,
                    "Error",
                    "Data successfully found but failed to save.",
                )
        else:
            show_message_box(
                self,
                QMessageBox.Warning,
                "Browser Error",
                scrapping_status,
            )
        self.scrapping_button.setEnabled(True)
        end_time = time.time()
        total_time = end_time - START_TIME
        print_the_output_statement(
            self.output_text,
            f"Total execution time for Scraping: {total_time:.2f} seconds",
        )

    @staticmethod
    def upload_excel():
        print("def upload_excel(self):")

    @staticmethod
    def intergate_with_crm_function():
        print("def intergate_with_crm_function(self):")

    def closed_window(self):
        print("def closed_window(self):")
        reply = QMessageBox.question(
            self,
            "Message",
            "Are you sure you want to close the window?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    print(f"Failed to quit driver: {str(e)}")
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(bootstrap_style)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
