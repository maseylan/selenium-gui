from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.keys import Keys
from Base import Startwebdriver
import random
import string
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import logging
import sys
import os
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import random
import pandas as pd
import openpyxl

# ============================================================================= 
# Example Script: advanced_selenium.py 
#  This file will be Saved in the 'Scripts' folder 
# =============================================================================
# Script metadata (required)
SCRIPT_NAME = 'Extract Data Sudopos QR'
SCRIPT_DESCRIPTION = 'Extract Total Product'
# ================================================================================= 
user_credentials = [
    {"user": "1", "passwd": "pujadewamatahari"},
    # {"user": "user2", "passwd": "pass2"},
    # {"user": "user3", "passwd": "pass3"},
    # {"user": "user4", "passwd": "pass4"},
    # {"user": "user5", "passwd": "pass5"}
]



# Configure logging
# Force stdout to UTF-8 for StreamHandler
stream_handler = logging.StreamHandler(sys.stdout)
try:
    # stream_handler.stream.reconfigure(encoding='utf-8')  # works if real stdout
    pass
except AttributeError:
    pass  # skip if sys.stdout is not a real TextIOWrapper

# FileHandler with UTF-8
file_handler = logging.FileHandler('selenium_test.log', encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
    handlers=[stream_handler, file_handler]
)

logger = logging.getLogger(__name__)
#====================ELEMENT==============================
pos_menu=["//a[contains(text(),'Point of Sale')]","/html/body/div[1]/div[2]/div/a[9]"]
pos_session=["//button[@name='open_ui' and @class ='btn btn-primary oe_kanban_action oe_kanban_action_button']"]

#====================ELEMENT==============================
# URL = os.getenv("URL_TARGET")
URL = "https://sudoerp.id/web/qr/sale?br=1"


class Script(Startwebdriver):

    def __init__(self, user, passwd, docker, wait_time=0):
        super().__init__(browser="chrome", is_docker=docker)
        self.credentials = {
            'url': URL,
            'user': user,
            'passwd': passwd,
            'db': "test"
        }
        self.wait_time = wait_time

    def run_logic(self, user_id):
        """Simulated test steps — expand with your actual logic."""
        
        self.get_url(self.credentials['url'])
        logger.info(f"[User {user_id}] Opened {self.credentials['url']}")
        
        load_time = time.time()
        self._click_element("//*[@id='nextBtn']")
        # Add the wait_time delay if specified
        if self.wait_time > 0:
            logger.info(f"[User {user_id}] Waiting {self.wait_time} seconds...")
            time.sleep(self.wait_time)

        total_product = self.driver.find_elements(By.XPATH, "//div[@class='card']")
        # logger.info(len(total_product))
        data = []
        for i, x in enumerate(total_product, start=1):
          try:
              product_name = x.find_element(
                  By.XPATH,
                  ".//div/div[@class='name']"
              ).text
              data.append({"No": i, "Product Name": product_name})
          except Exception as e:
              print(f"[WARN] Produk {i} gagal diambil: {e}")
              # Bisa pilih: skip produk ini atau masukkan data kosong
              data.append({"No": i, "Product Name": ""})


        df = pd.DataFrame(data)
        file_path = "products.xlsx"
        df.to_excel(file_path, index=False)
            


def run_test(user_id, use_docker, headless, delay):
    """Run test for a single user"""
    try:
        # Use modulo to cycle through available credentials if more workers than credentials
        cred_index = user_id % len(user_credentials)
        creds = user_credentials[cred_index]
        
        logger.info(f"[User {user_id}] Starting test with credentials: {creds['user']}")
        script = Script(user=creds["user"], passwd=creds["passwd"], docker=use_docker, wait_time=delay)
        script.run_logic(user_id)
        
    except Exception as e:
        logger.error(f"[User {user_id}] Error occurred: {str(e)}", exc_info=True)


def main(gui_instance=None):
    use_docker = gui_instance.docker
    workers = gui_instance.workers
    headless = gui_instance.headless
    delay = gui_instance.delay
    
    logger.info(f"Starting stress test with configuration: workers={workers}, headless={headless}, delay={delay}, docker={use_docker}")
    
    # Create a partial function with the fixed parameters
    test_function = partial(run_test, use_docker=use_docker, headless=headless, delay=delay)
    
    logger.info(f"Launching {workers} concurrent test threads...")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Map only the user_id parameter
        executor.map(test_function, range(workers))
    
    logger.info("All test threads completed")