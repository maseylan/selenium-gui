from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor
import logging
import time

SELENOID_URL = "http://localhost:4444/wd/hub"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(message)s')
logger = logging.getLogger()

def create_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless=new")  # optional

    driver = webdriver.Remote(
        command_executor=SELENOID_URL,
        options=options
    )
    return driver

def run_test(user_id):
    try:
        driver = create_driver()
        logger.info(f"[User {user_id}] Browser started")

        driver.get("https://www.example.com")
        logger.info(f"[User {user_id}] Title: {driver.title}")

        time.sleep(3)
        driver.quit()
        logger.info(f"[User {user_id}] Browser closed")
    except Exception as e:
        logger.error(f"[User {user_id}] Error: {e}")

if __name__ == "__main__":
    workers = 5
    with ThreadPoolExecutor(max_workers=workers) as executor:
        executor.map(run_test, range(workers))
