import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config import DOWNLOAD_FOLDER, HEADLESS, HEIGHT, WIDTH


def initialize_driver(loop):
    """
    Initializes a Selenium WebDriver instance with specified Chrome options.
    Args:
        loop (asyncio.AbstractEventLoop): The asyncio event loop to set.

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance.
    """
    print("initialize_driver")
    chrome_options = Options()
    asyncio.set_event_loop(loop)
    window_size = f"{WIDTH},{HEIGHT}"
    print(f"Window Size: {window_size}")
    if HEADLESS:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument(f"--window-size={window_size}")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--verbose")
    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": DOWNLOAD_FOLDER,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False,
            "plugins.always_open_pdf_externally": True,  # Disable PDF viewer
        },
    )
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")  # Set the verbosity level for logging
    chrome_options.add_argument("--disable-software-rasterizer")
    return webdriver.Chrome(service="", options=chrome_options)
