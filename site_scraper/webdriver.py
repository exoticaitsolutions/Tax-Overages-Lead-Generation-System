import random
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class InitializeDriver:

    @staticmethod
    def _setup_options():
        options = webdriver.ChromeOptions()
        # Uncomment this line if you want to run in headless mode
        # options.add_argument("--headless")
        # # Randomize window size
        width = random.randint(800, 1920)
        height = random.randint(600, 1080)
        window_size = f"{width},{height}"
        options.add_argument(f"--window-size={window_size}")
        print(f"Window Size: {window_size}")
        options.add_argument("--disable-third-party-cookies")
        # Generate a random user agent
        return options
    
    def initialize_chrome(self):
        options = self._setup_options()
        chromedriver_path = ChromeDriverManager().install()
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        print("Free proxy is Working")
        return driver
