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

SCRIPT_NAME = "Docker Selenium Stress Test"
SCRIPT_DESCRIPTION = "Stress Test using Docker"
is_docker = True
user_credentials = [
    {"user": "user1", "passwd": "pass1"},
    {"user": "user2", "passwd": "pass2"},
    {"user": "user3", "passwd": "pass3"},
    {"user": "user4", "passwd": "pass4"},
    {"user": "user5", "passwd": "pass5"}
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
#====================ELEMENT==============================
URL = os.getenv("URL_TARGET")


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
        
        
        # Add the wait_time delay if specified
        if self.wait_time > 0:
            logger.info(f"[User {user_id}] Waiting {self.wait_time} seconds...")
            time.sleep(self.wait_time)
        
        #Get DB (DEV ONLY)
        self.db_select("STRTEST")
        
        #Login Page
        self.login_page(user=self.credentials['user'],
                        password=self.credentials['passwd'])
        
        self._click_element(pos_menu)
        
        self.quit_driver()
        logger.info(f"[User {user_id}] Test completed")





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