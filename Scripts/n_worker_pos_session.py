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

SCRIPT_NAME = "Docker Selenium Stress Test"
SCRIPT_DESCRIPTION = "Stress Test using Docker"
is_docker = True
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
pos_menu=[
    # "//a[contains(text(),'Point of Sale')]",
          "/html/body/div[1]/div[2]/div/a[9]"]
pos_session=["//button[@name='open_ui' and @class ='btn btn-primary oe_kanban_action oe_kanban_action_button']"]

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
        start_time = time.time()

        self.get_url(self.credentials['url'])
        logger.info(f"[User {user_id}] Opened {self.credentials['url']}")
        
        
        # Add the wait_time delay if specified
        if self.wait_time > 0:
            logger.info(f"[User {user_id}] Waiting {self.wait_time} seconds...")
            time.sleep(self.wait_time)
        
        #Get DB (DEV ONLY)
        # self.db_select("STRTEST")
        
        #Login Page
        self.login_page(user=self.credentials['user'],
                        password=self.credentials['passwd'])
        
        self._click_element(pos_menu)
        self._click_element(pos_session) # Open POS Session
        #select employee
        self._click_element("//button[contains(text(),'Select Cashier')]",
                            # wait_condition="presence",
                            timeout=100)        
        self._click_element(f"/html/body/body/div[1]/div[4]/div/div/div/div[{user_id+2}]",
                            # wait_condition="presence",
                            timeout=100)
        # time.sleep()
        open_session_control = EC.visibility_of_element_located((By.CSS_SELECTOR, "body > div.pos > div.popups > div > div"))
        try :
            cahs_control = WebDriverWait(self.driver, timeout=5).until(open_session_control)
        except Exception :
            cahs_control = None
            pass 
        
        if cahs_control and cahs_control.is_displayed():
            logger.info(f"[User {user_id}] Opening Cash Control, ")
            self._click_element("/html/body/body/div[1]/div[4]/div/div/footer/div")
        else:
            logger.error(f"[User {user_id}] No Cash Control Displayed, Already Opened")
            
        while True:
            try :
                #Table
                self._click_element(f"/html/body/body/div[1]/div[3]/div[1]/div/div/div/div/div/div/div/div[{user_id+1}]",
                                    timeout=10) 
                
                #Modal Customer Name
                self._insert_text("/html/body/body/div[1]/div[4]/div/div/div/textarea",
                                ''.join(random.choice(string.ascii_letters) for _ in range(10)))
                self._click_element("/html/body/body/div[1]/div[4]/div[3]/div/footer/div[1]",) # Submit Modal Guest Name

                #Select Order Type
                assert self.driver.find_element(By.CSS_SELECTOR, "body > div.pos > div.popups > div:nth-child(2) > div > header").is_displayed()
                self._click_element("body > div.pos > div.popups > div:nth-child(2) > div > div > div")

                # Submit modal guest total
                self._click_element(["/html/body/body/div[1]/div[4]/div/div/footer/div[2]","body > div.pos > div.popups > div > div > footer > div.button.confirm.highlight"]) 

                elements = "//article[@class='product']"
                products = self.driver.find_elements(By.XPATH, elements)
                
                many_click = random.randint(1, 50)
                for _ in range(many_click):
                    self._click_element(elements+f"[{random.randint(1, len(products))}]")
                

                self._click_element("//button[contains(text(),'Save Order')]") # Click Save Order Button
                self._click_element(f"/html/body/body/div[1]/div[3]/div[1]/div/div/div/div/div/div/div/div[{user_id+1}]",
                                    timeout=10) # Meja
                self._click_element("//button[contains(text(),'Payment')]","//button[@class='button pay validation']")
                # payment_meth list
                elem_pm = "//div[@class='button paymentmethod']"
                payment_method = self.driver.find_elements(By.XPATH, "//div[@class='button paymentmethod']")
                self._click_element(elem_pm+f"[{random.randint(1, len(payment_method))}]") # Random Payment Method
                self._click_element("/html/body/body/div[1]/div[3]/div[1]/div/div/div/div/div/div[2]/div[1]/div[2]","body > div.pos > div.pos-content > div.window > div > div > div > div > div > div.main-content > div.left-content > div.button.next.validation.highlight")

                self._click_element("/html/body/body/div[1]/div[3]/div[1]/div/div/div/div/div/div[3]") # New  Order
            except Exception as e:
                logger.error(f"[User {user_id}] Error during order processing: {str(e)}")
                break   

        
        elapsed_time = time.time() - start_time
        time.sleep(300)
        self.quit_driver()
        logger.info(elapsed_time)
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