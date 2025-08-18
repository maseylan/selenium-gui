import time
from tkinter import messagebox as mb
import logging
import requests
import pyautogui
import psutil
import threading
import pandas as pd
import re
import os
import threading
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
from concurrent.futures import ThreadPoolExecutor

#Chrome Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

#Firefox Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService



class Startwebdriver():
    """
    A class to configure and handle Selenium WebDriver for automated browser testing, primarily using Google Chrome.

    This class includes functionalities such as initializing the WebDriver with custom configurations, including loading browser extensions,
    setting download directories, enabling headless execution (commented out), and other browser-specific options. The class also
    facilitates navigation, user authentication tasks, interacting with web elements, and terminating the browser instance efficiently
    while managing logs.

    Attributes
    ----------
    default_timeout : int
        Default timeout duration (in seconds) for wait operations.
    username_path : str
        XPath string of the username input field for logging in.
    password_path : str
        XPath string of the password input field for logging in.
    login_button_path : str
        XPath string of the login button.
    """
    default_timeout = 10
    username_path = "// *[ @ id = 'login']"
    password_path = "// *[ @ id = 'password']"
    login_button_path = "//*[@class='btn btn-primary']"

    def __init__(self, browser: str = "firefox", is_docker=False) :

        #Download Directory
        self.is_docker = is_docker
        # self.driver = None
        self.download_dir = os.getcwd()
        self.browser = browser
        # Extension Path For Chrome
        #Set up Logging
        self.log_file = os.path.join(self.download_dir, "Testing.log")
        logging.basicConfig(
                            # filename='Testing.log',
                            filemode='w',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            level=logging.info
                            )

        """ Headless Background Running -------------- 
        # chrome_options.add_argument('--headless=new') """

        if browser.lower() == "chrome":
            self.run_chrome_driver()

        elif browser.lower() == "firefox":
            #Options For Firefox
            self.run_firefox_driver()

        else:
            raise ValueError("Browser not supported. Choose 'chrome' or 'firefox'.")

    def run_chrome_driver(self,):

        chrome_options = Options()
        prefs = {"download.default_directory": self.download_dir,
                 "profile.default_content_setting_values.geolocation": 1
                 }
        # chrome_options.add_argument('--use-fake-ui-for-media-stream')
        # chrome_options.add_argument('--use-fake-device-for-media-stream')
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_extension(self.extension_path)
        chrome_options.add_argument("--start-maximized")
        # chrome_options.add_argument(
            # "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36")

        # chrome_options.add_experimental_option("prefs", prefs)

        #Trying to Fix ChromeDriverManager
        # path_conditional = r"C:\Users\tilabs\Downloads\chromedriver-win64 (2)\chromedriver-win64\chromedriver.exe"

        if self.is_docker == True :
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            # chrome_options.add_argument("--headless") 
            chrome_options.set_capability("browserVersion","127.0")
            chrome_options.set_capability("selenoid:options", {
                "enableVNC": True,
                "enableVideo": True,
                "sessionTimeout": "5m"
            })
            Remote_driver = os.getenv("SELENOID_URL", "http://localhost:4444/wd/hub")
            self.driver = webdriver.Remote(
                command_executor=Remote_driver,
                options= chrome_options
            )
        else :
            # Coordinates: (Latitude, Longitude, Accuracy)
            latitude = 37.7749  # Example: San Francisco
            longitude = -122.4194
            accuracy = 100

            self.driver = webdriver.Chrome(
                # service=Service(path_conditional),
                options=chrome_options)
            self.driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": accuracy
            })

        logging.info(f"{self.browser.capitalize()} browser has started.\n")

    def run_firefox_driver(self):
        # Options For Firefox
        firefox_options = FirefoxOptions()
        firefox_options.set_preference("browser.download.dir", self.download_dir)
        firefox_options.set_preference("browser.download.folderList", 2)
        firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")
        firefox_options.set_preference("media.navigator.streams.fake", True)
        firefox_options.set_preference("media.navigator.permission.disabled", True)

        self.driver = webdriver.Firefox(
            service=FirefoxService(GeckoDriverManager().install()),
            options=firefox_options
        )
        logging.info(f"{self.browser.capitalize()} browser has started.\n")



    def get_url(self, url: str = "https://github.com/maseylan/tilabs_selenium", wait_time: int = 3):
        """
        Navigate to a URL and wait for a specified amount of time before returning.

        :param url: The target URL to navigate to.
        :param wait_time: Seconds to wait after loading the page (default: 3).
        """
        try:
            self.driver.get(url)
            logging.info(f"✅ URL Yang Dituju: {url} \n")
            time.sleep(wait_time)  # Could be replaced with a more dynamic wait
        except WebDriverException as e:
            raise RuntimeError(f"❌ Failed to open URL '{url}': {e}")

    def db_select (self, db_contains_text ="QC") :
        try :
            self._click_element(f"//a[@href='/web?db={db_contains_text}']")
            return True

        except TimeoutError:
            raise TimeoutError("Timeout occurred while waiting for element to be visible.")
            return false

    def login_page(self,user :None ,password : None,username_path = None,password_path = None,login_button_path = None):

        global actions

        username_path = username_path or self.username_path
        password_path = password_path or self.password_path
        login_button_path = login_button_path or self.login_button_path

        try:
            """ These are the steps for logging in:
                Username Field
                Password Field
                Login Button 
                """
            # Email Field
            self._insert_text(username_path, user)
            #Password Field
            self._insert_text(password_path, password)
            #Login Button
            self._click_element(
                               login_button_path
                               )
        except TimeoutException as te:
            logging.exception("Timeout occurred during login.")
            raise TimeoutException("Timeout while waiting for login elements.") from te
        except AssertionError as ae:
            logging.exception("Assertion error occurred during login.")
            # raise AssertionError(f"Assertion failed during login: {ae}")
        except WebDriverException as we:
            logging.exception("WebDriver error occurred during login.")
            # raise RuntimeError(f"WebDriver error occurred during login: {we}")
        except Exception as e:
            logging.exception("Unexpected error occurred during login.")
            # raise RuntimeError(f"Unexpected error during login: {e}")


    def logout(self, timeout = None):
        """
        Logs out the user from the application using web driver. It interacts with the user button
        and logout button on the web page. If a timeout occurs while locating the elements
        or any other exception happens during the logout process, relevant errors are raised.

        Arguments:
            timeout: Optional[int]
                The maximum amount of time to wait for elements to be visible before triggering a timeout error.
                If not provided, the default timeout will be used.

        Raises:
            Exception: Raised with a descriptive error message if any issue other than a timeout occurs
            during the logout process.
            TimeoutError: Raised when the specified amount of time is exceeded while waiting
            for the elements to become visible.
        """
        self.default_timeout = timeout or self.default_timeout
        global actions
        try:
            # button user
            user_button = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.XPATH, "/html/body/header/nav/div[3]/div[10]/button]"))
            )
            actions = ActionChains(self.driver)
            actions.move_to_element(user_button).click().perform()

            #Button Logout
            user_button = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.XPATH, "/html/body/header/nav/div[3]/div[10]/div/a[3]"))
            )
            actions = ActionChains(self.driver)
            actions.move_to_element(user_button).click().perform()

        except Exception as e:
            logging.exception("Error occurred during logout.")
            raise Exception(f"Error occurred: {str(e)} \n Gagal Logout ")
        except TimeoutError:
            logging.exception("Timeout occurred during logout.")
            raise TimeoutError("Timeout occurred while waiting for element to be visible.")

    def get_text_numeric(self,select_xpath):
        """
        Extracts numeric value from the text of a web element identified by the provided
        XPATH. It waits for the element to be visible, retrieves its text, searches for
        numeric characters, and converts it to an integer. If no numeric value is found
        or an error occurs, it returns None.

        Args:
            select_xpath (str): The XPATH of the element to extract numeric text from.

        Returns:
            Optional[int]: The extracted integer value if found, otherwise None.

        Raises:
            No additional errors are specified beyond logging the exception in case
            of any runtime issue.
        """
        try:

            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, select_xpath))
            )
            new = element.text
            number = re.search(r'\d+', new)
            # number = re.search(r'[-+]?[0-9,]*\.?[0-9]+', new)


            if number:
                clean_number = number.group().replace(',', '').strip()
                return int(clean_number)
            else:
                return None
        except Exception as e:
            logging.exception("Error occurred during get_text_numeric.")
            logging.info(f"Error occurred: {str(e)}")
            return None

    def get_text_numeric2(self, select_xpath):
        try:
            # Wait for the element to be visible
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, select_xpath))
            )

            # Extract the text from the element
            new = element.text
            number = re.search(r'\((\d+)\)', new)  # Match the first sequence of digits

            if number:
                # Clean the number and return as an integer
                clean_number = number.group(1)  # Get the captured number
                logging.info(f"Number: {clean_number}")  # Debugging the cleaned number
                return int(clean_number)  # Convert it to an integer and return
            else:
                logging.info("No numeric value found.")
                return None  # Return None if no number is found

        except Exception as e:
            logging.info(f"Error occurred: {str(e)}")
            return None


    def _click_element(self, element_paths, timeout=None, record_time = False, **kwargs):
        """
        Attempts to locate and click on elements by automatically detecting the appropriate
        locator strategy based on the format of the element path string.

        :param element_paths: Single string or list of strings with element locators
        :type element_paths: str or list of str
        :param timeout: Optional timeout value in seconds
        :type record_time: bool, Optional 
        :type timeout: float, optional
        :param kwargs: Additional keyword arguments
            - attempt_max: Maximum number of attempts for clicking stale elements (default: 2)
            - log_clicks: Whether to log click actions (default: True)
            - scroll_into_view: Whether to scroll element into view before clicking (default: False)
            - use_action_chains: Whether to use ActionChains for clicking (default: True)
            - wait_condition: Which wait condition to use ('visibility', 'clickable', 'presence')
        :return: Boolean indicating success (True) or failure (False)
        :rtype: bool
        """
        if record_time :
            start_time = time.time()
        # Handle single element path
        if not isinstance(element_paths, list):
            element_paths = [element_paths]

        # Default Kwargs Value
        timeout = timeout or self.default_timeout
        attempt_max = kwargs.get('attempt_max', 2)
        log_clicks = kwargs.get('log_clicks', True)
        scroll_into_view = kwargs.get('scroll_into_view', True)
        use_action_chains = kwargs.get('use_action_chains', True)
        wait_condition = kwargs.get('wait_condition', 'visibility')

        success = False

        # Try each element path
        for element_path in element_paths:
            # Auto-detect locator type based on the format of element_path
            by_element = self._detect_locator_type(element_path)


            # Get readable locator name for logging
            locator_name = "UNKNOWN"
            if by_element == By.XPATH:
                locator_name = "XPATH"
            elif by_element == By.CSS_SELECTOR:
                locator_name = "CSS_SELECTOR"
            elif by_element == By.ID:
                locator_name = "ID"
            elif by_element == By.NAME:
                locator_name = "NAME"
            elif by_element == By.TAG_NAME:
                locator_name = "TAG_NAME"
            elif by_element == By.LINK_TEXT:
                locator_name = "LINK_TEXT"
            elif by_element == By.PARTIAL_LINK_TEXT:
                locator_name = "PARTIAL_LINK_TEXT"

            logging.info(f"Trying with auto-detected locator: {locator_name} - {element_path}")

            for attempt in range(attempt_max):
                try:
                    # Select wait condition based on parameter
                    if wait_condition == 'clickable':
                        wait_condition_ec = EC.element_to_be_clickable((by_element, element_path))
                    elif wait_condition == 'presence':
                        wait_condition_ec = EC.presence_of_element_located((by_element, element_path))
                    else:  # default to visibility
                        wait_condition_ec = EC.visibility_of_element_located((by_element, element_path))

                    # Wait for element according to selected condition
                    element = WebDriverWait(self.driver, timeout).until(wait_condition_ec)

                    # Scroll element into view if requested
                    if scroll_into_view:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

                    # Check if element is interactable
                    if not (element.is_displayed() and element.is_enabled()):
                        logging.warning(f"Element found at {element_path} is not interactable")
                        logging.info(f"⚠️ Element found at {element_path} is not interactable, attempting click anyway")

                    

                    # ✅ Log AFTER successful click
                    if log_clicks:
                        try:
                            field_text = self.save_existing_text_field(element_path)
                            if field_text:
                                logging.info(f"✅ {field_text} Element Clicked: <Element> {element_path}\n")
                            else:
                                logging.info(f"✅ Element Clicked with Path: {element_path}\n")
                        except Exception as e:
                            # logging.warning(f"Couldn't get text field info for {element_path}: {e}")
                            logging.info(f"✅ Element Clicked (but couldn't fetch text field info): {element_path}")
                   
                    # Perform click with appropriate method
                    if use_action_chains:
                        ActionChains(self.driver).move_to_element(element).click().perform()
                    else:
                        element.click()

                         # ⏱️ Record elapsed time inside log_clicks
                        if record_time:
                            end_time = time.time()
                            elapsed_time = end_time - start_time
                            logging.info(f"Element Click completed in {elapsed_time:.2f} seconds")

                    success = True
                    return True
    
                # Handle specific exceptions
                except StaleElementReferenceException:
                    logging.warning(f"Attempt {attempt + 1}: Element became stale. Retrying...")
                    logging.info(f"⚠️ Attempt {attempt + 1}: Element became stale. Retrying...")
                    if attempt + 1 == attempt_max:
                        logging.error(
                            f"StaleElementReferenceException: Element at '{element_path}' remained stale after {attempt_max} attempts")
                        logging.info(f"⚠️ Element at '{element_path}' remained stale after {attempt_max} attempts")

                except TimeoutException:
                    logging.error(
                        f"TimeoutException: Timeout while waiting for element at '{element_path}' to become visible")
                    logging.info(f"⚠️ Timeout while waiting for element at '{element_path}' to become visible")
                    break  # Try next locator

                except WebDriverException as we:
                    # logging.error(f"WebDriverException while interacting with '{element_path}': {we}")
                    # logging.info(f"⚠️ Selenium WebDriver error while interacting with '{element_path}': {we}")
                    break  # Try next locator

                except Exception as e:
                    # logging.error(f"Unexpected error in click_element for '{element_path}': {type(e).__name__} - {e}")
                    # logging.info(f"⚠️ Unexpected error in click_element for '{element_path}': {type(e).__name__} - {e}")
                    break  # Try next locator

       
        # Return success status instead of raising exceptions
        return success

    def _detect_locator_type(self, element_path):
        """
        Automatically detects the appropriate locator type based on the format of the element path.

        :param element_path: The element locator string
        :type element_path: str
        :return: Appropriate By locator
        :rtype: selenium.webdriver.common.by.By
        """
        # from selenium.webdriver.common.by import By
        # Check for XPath patterns
        if element_path.startswith('//') or element_path.startswith('(//') or element_path.startswith('(/') or element_path.startswith('/'):
            return By.XPATH

        # Check for CSS ID selector
        elif element_path.startswith('#'):
            return By.CSS_SELECTOR

        # Check for CSS class selector
        elif element_path.startswith('.'):
            return By.CSS_SELECTOR

        # Check for other CSS selector patterns (contains square brackets or specific operators)
        elif any(char in element_path for char in ['>', '+', '~', '[', ':']):
            return By.CSS_SELECTOR

        # Check if it's likely a name attribute
        elif element_path.startswith('name='):
            return By.NAME

        # Check if it's likely a full link text
        elif element_path.lower().startswith('link='):
            return By.LINK_TEXT

        # Check if it's likely a partial link text
        elif element_path.lower().startswith('partiallink='):
            return By.PARTIAL_LINK_TEXT

        # If it looks like a simple tag name
        elif element_path.isalpha() and element_path.islower():
            return By.TAG_NAME

        # Default to ID for short simple strings without spaces
        elif ' ' not in element_path and len(element_path) < 50:
            return By.ID

        # Fall back to XPath for anything else
        else:
            return By.XPATH

        return success

    def _insert_text(self, element_paths, text_to_insert, timeout=None, record_time =False, **kwargs):
        """
        Attempts to locate and insert text into elements by automatically detecting the appropriate
        locator strategy based on the format of the element path string.

        :param element_paths: Single string or list of strings with element locators
        :type element_paths: str or list of str
        :param text_to_insert: Text to insert into the element
        :type text_to_insert: str
        :param timeout: Optional timeout value in seconds
        :param record_time: Whether to record the time taken for the operation (default: False)
        :type timeout: float, optional
        :param kwargs: Additional keyword arguments
            - attempt_max: Maximum number of attempts for interacting with stale elements (default: 2)
            - log_actions: Whether to log text insertion actions (default: True)
            - scroll_into_view: Whether to scroll element into view before interacting (default: False)
            - use_action_chains: Whether to use ActionChains for clicking (default: True)
            - wait_condition: Which wait condition to use ('visibility', 'clickable', 'presence')
            - clear_first: Whether to clear the field before inserting text (default: True)
            - press_enter: Whether to press Enter after inserting text (default: False)
        :return: Boolean indicating success (True) or failure (False)
        :rtype: bool
        """
        if record_time :
            start_time = time.time()
            # logging.info(f"Starting text insertion at {start_time} for element(s): {element_paths}")

        # Handle single element path
        if not isinstance(element_paths, list):
            element_paths = [element_paths]

        # Default Kwargs Value
        timeout = timeout or self.default_timeout
        attempt_max = kwargs.get('attempt_max', 2)
        log_actions = kwargs.get('log_actions', True)
        scroll_into_view = kwargs.get('scroll_into_view', False)
        use_action_chains = kwargs.get('use_action_chains', True)
        wait_condition = kwargs.get('wait_condition', 'visibility')
        clear_first = kwargs.get('clear_first', True)
        press_enter = kwargs.get('press_enter', False)

        success = False

        # Try each element path
        for element_path in element_paths:
            # Auto-detect locator type based on the format of element_path
            by_element = self._detect_locator_type(element_path)

            # Get readable locator name for logging
            locator_name = "UNKNOWN"
            if by_element == By.XPATH:
                locator_name = "XPATH"
            elif by_element == By.CSS_SELECTOR:
                locator_name = "CSS_SELECTOR"
            elif by_element == By.ID:
                locator_name = "ID"
            elif by_element == By.NAME:
                locator_name = "NAME"
            elif by_element == By.TAG_NAME:
                locator_name = "TAG_NAME"
            elif by_element == By.LINK_TEXT:
                locator_name = "LINK_TEXT"
            elif by_element == By.PARTIAL_LINK_TEXT:
                locator_name = "PARTIAL_LINK_TEXT"

            logging.info(f"Trying to insert text using auto-detected locator: {locator_name} - {element_path}")

            for attempt in range(attempt_max):
                try:
                    # Select wait condition based on parameter
                    if wait_condition == 'clickable':
                        wait_condition_ec = EC.element_to_be_clickable((by_element, element_path))
                    elif wait_condition == 'presence':
                        wait_condition_ec = EC.presence_of_element_located((by_element, element_path))
                    else:  # default to visibility
                        wait_condition_ec = EC.visibility_of_element_located((by_element, element_path))

                    # Wait for element according to selected condition
                    element = WebDriverWait(self.driver, timeout).until(wait_condition_ec)

                    # Scroll element into view if requested
                    if scroll_into_view:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

                    # Check if element is interactable
                    if not (element.is_displayed() and element.is_enabled()):
                        logging.warning(f"Element found at {element_path} is not interactable")
                        logging.info(f"⚠️ Element found at {element_path} is not interactable, attempting interaction anyway")

                    # Click on the element first to focus it
                    if use_action_chains:
                        ActionChains(self.driver).move_to_element(element).click().perform()
                    else:
                        element.click()

                    # Clear the field if requested
                    if clear_first:
                        element.clear()

                    # Insert the text
                    element.send_keys(text_to_insert)

                    # Press Enter if requested
                    if press_enter:
                        time.sleep(0.5)
                        element.send_keys(Keys.ENTER)

                    # Log action if enabled
                    if log_actions:
                        if record_time:
                            end_time = time.time()
                            elapsed_time = end_time - start_time
                            logging.info(
                                f"✅ Inserted text: '{text_to_insert}' into element(s): {element_path} "
                                f"in {elapsed_time:.2f} seconds\n"
                            )
                        else:
                            logging.info(
                                f"✅ Inserted text: '{text_to_insert}' into element(s): {element_paths}\n"
                            )
                        success = True

                    return True  # Return immediately on first successful insertion

                except StaleElementReferenceException:
                    logging.warning(f"Attempt {attempt + 1}: Element became stale. Retrying...")
                    logging.info(f"⚠️ Attempt {attempt + 1}: Element became stale. Retrying...")
                    if attempt + 1 == attempt_max:
                        logging.error(
                            f"StaleElementReferenceException: Element at '{element_path}' remained stale after {attempt_max} attempts")
                        logging.info(f"⚠️ Element at '{element_path}' remained stale after {attempt_max} attempts")

                except TimeoutException:
                    logging.error(
                        f"TimeoutException: Timeout while waiting for element at '{element_path}' to become visible")
                    logging.info(f"⚠️ Timeout while waiting for element at '{element_path}' to become visible")
                    break  # Try next locator

                except WebDriverException as we:
                    logging.error(f"WebDriverException while interacting with '{element_path}': {we}")
                    logging.info(f"⚠️ Selenium WebDriver error while interacting with '{element_path}': {we}")
                    break  # Try next locator

                except Exception as e:
                    logging.error(f"Unexpected error in insert_text for '{element_path}': {type(e).__name__} - {e}")
                    logging.info(f"⚠️ Unexpected error in insert_text for '{element_path}': {type(e).__name__} - {e}")
                    break  # Try next locator

        
        # Return success status instead of raising exceptions
        return success

    def get_all_elements(self) -> list:
        # Get all elements on the page
        elements = self.driver.find_elements(By.XPATH, "//*")  # Get all elements in the DOM
        return elements



    def inserttext(self, element_xpath, text_to_insert):
        try:
            element = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((By.XPATH, element_xpath))
            )
            actions = ActionChains(self.driver)
            actions.move_to_element(WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.XPATH, element_xpath)))).click().perform()
            element.clear()  # Clear field
            element.send_keys(text_to_insert)  # Insert text
            time.sleep(1)
            logging.info(f"Inserted text: {text_to_insert} into element: {element_xpath}\n")
        except Exception as e:
            logging.info(f"Error: {e}. Could not insert text into element with XPath {element_xpath}.")

    def insert_text_new(self, by, element_selector : str, text_to_insert : str) -> None:
        """
        Insert text into a specified web element using Selenium WebDriver. This method waits for the visibility
        of the target element, moves to it, clears its content, and inserts the provided text. It ensures
        interactions are performed after the element is fully visible and compatible for user actions.

        Parameters:
            by: The method to locate elements using Selenium By methods.
            element_selector: str
                A string that represents the selector or locator for the target element.
            text_to_insert: str
                The text to input into the specified web element.

        Raises:
            Exception: If any failure occurs during locating the element, interacting, or inserting the text.
        """
        try:

            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((by, element_selector))
            )
            actions = ActionChains(self.driver)
            actions.move_to_element(WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((by, element_selector)))).click().perform()
            element.clear()  # Clear field
            element.send_keys(text_to_insert)  # Insert text
            time.sleep(1)
            logging.info(f"✅ Inserted text: {text_to_insert} into element: {element_selector}\n")
        except Exception as e:
            logging.info(f"⚠️ Error: {e}.")

    def insert_image(self,by_what,element_path,file_path):
        try:
            element = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((by_what, element_path))
            )
            element.send_keys(file_path)
            time.sleep(1)
            logging.info(f"Inserted Image: {file_path} into element: {element_path}")
        except NoSuchElementException as e:
            logging.info(f"Error: {e}.")


    def insert_text_without_click(self, element_xpath, text_to_insert):
        try:
            element = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((By.XPATH, element_xpath))
            )
            element.clear()  # Clear field
            element.send_keys(text_to_insert)  # Insert text
            time.sleep(1)
            logging.info(f"Inserted text: {text_to_insert} into element: {element_xpath}")
        except Exception as e:
            logging.info(f"Error: {e}. Could not insert text into element with XPath {element_xpath}.")

    def inserttext_dropdown(self, element_xpath, text_to_insert):
        try:
            element = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((By.XPATH, element_xpath))
            )
            actions = ActionChains(self.driver)
            actions.move_to_element(element).click().perform()
            element.clear()  # Clear field
            element.send_keys(text_to_insert)  # Insert text
            actions.send_keys(Keys.ENTER)
            logging.info(f"Inserted text: {text_to_insert} into element: {element_xpath}")
        except Exception as e:
            logging.info(f"Error: {e}. Could not insert text into element with XPath {element_xpath}.")

    def send_hotkeys(self,key1,key2):
        multiactions = ActionChains(self.driver)
        multiactions.key_down(key1).send_keys(key2).key_up(key1).perform()
        logging.info(f"Hotkeys send {key1} + {key2}")
        time.sleep(1)

    def send_key(self,key1,path):
        element = self.driver.find_element(By.XPATH,path)
        element.send_keys(key1)
        logging.info(f"Keys Send {key1}")

    def java_script_args(self, java_script_ex : str, path : str) -> None:
        """
        Executes JavaScript code on a web element identified by a given XPath.

        This method attempts to locate a web element using an XPath selector and executes
        the provided JavaScript code on the located element. If the element cannot
        be found or if interaction with the element fails, an error message is logging.infoed.

        Attributes:
            driver: A WebDriver instance used to interact with the web page.

        Args:
            java_script_ex: The JavaScript code to be executed as a string.
            path: The XPath selector of the web element on which the script will be executed.

        Raises:
            NoSuchElementException: If the specified element cannot be found.
            TimeoutException: If the action times out.
        """
        try:
            element = self.driver.find_element(By.XPATH, path)
            self.driver.execute_script(java_script_ex,element)
        except (NoSuchElementException, TimeoutException) as e:
            logging.info(f"{e} Cant Interact")

    def java_script_args_no_path(self, java_script_ex, timeout = None):
        timeout = timeout or self.default_timeout
        """
        Executes JavaScript code in the context of the current browser window or frame,
        without requiring a specific path argument for the JavaScript snippet.

        Parameters:
            java_script_ex: str
                The JavaScript expression to be executed in the browser.

        Raises:
            NoSuchElementException
                If the specified element is not found during execution.
            TimeoutException
                If the page does not load completely within the specified timeout.
        """
        try:
            WebDriverWait(self.driver,timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            # element = self.driver.execute_script(java_script_ex)
            self.driver.execute_script(java_script_ex)
            logging.info(f"Success Interact with {java_script_ex}")
        except (NoSuchElementException, TimeoutException) as e:
            logging.info(f"{e}")

    def handle_switch_window(self, window_index : int) -> None:
        """
        Handles switching to a specific window based on its index.
        This method switches the driver's focus to a browser window specified by the index.
        It validates the given index against the available window handles and raises
        an IndexError if the index is out of range.

        Args:
            window_index (int): The index of the window to switch to.

        Raises:
            IndexError: If the window_index is not within the valid range of window handles.
        """
        try:
            # Get all the window handles
            window_handles = self.driver.window_handles

            # Check if the window_index is within the valid range
            if window_index < 0 or window_index >= len(window_handles):
                raise IndexError("Window index out of range")

            #Change Window
            self.driver.switch_to.window(window_handles[window_index])
            logging.info(f"Switched to window: {self.driver.title}")

        except Exception as e:
            logging.info(f"Error: {e} \n Can't switch window")

    def print_existing_text_field(self, path : str) -> str :
        """
        Fetches and returns the text content from a visible text field located by the given XPath.

        Parameters
        ----------
        path : str
            The XPath of the target text field.

        Returns
        -------
        str
            The stripped text content of the located text field.

        Raises
        ------
        NoSuchElementException
            If the element cannot be found.
        TimeoutException
            If the element does not become visible within the specified wait time.
        """
        text_field = WebDriverWait(self.driver,10).until(
            EC.visibility_of_element_located((By.XPATH, path))
        )
        text = text_field.text.strip()
        return text

    def take_screenshot(self, path : str = "/html/body") -> None:
        """
        Takes a screenshot of a specified web element and temporarily displays it.

        Waits for the visibility of the web element located by the given path, captures
        a screenshot of the element, temporarily saves the file, displays it, and then
        deletes it after a specified amount of time.

        Parameters
        ----------
        path : str
            The XPath of the web element to capture.

        Raises
        ------
        TimeoutException
            If the web element is not found within 10 seconds.

        Notes
        -----
        The screenshot file is named "Element_SS.png" and is temporarily displayed using
        the default system application for image files. The file is removed after 10 seconds.
        """
        text_field = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, path))
        )
        screenshot_file = "Element_SS.png"
        text_field.screenshot(screenshot_file)

        os.startfile(screenshot_file)
        logging.info(f"📷 ScreenShoot taken for element {text_field} \n")
        time.sleep(10)
        os.remove(screenshot_file)

    def open_file_current_folder(self,file_name : str) -> None:
        try :
            time.sleep(4)
            os.startfile(file_name)
            logging.info(f"File Succesfuly Opened")
        except Exception as e:
            raise f"Error Opening File {file_name} with Error: {e}"

    def open_file_in_new_tab(self, file_path : str) ->None:
        # Normalize the file path
        file_path = os.path.abspath(file_path).replace("\\", "/")  # Get absolute path and ensure slashes
        if os.name == 'nt':  # For Windows
            file_url = f'file:///{file_path}'
        else:  # For macOS or Linux
            file_url = f'file://{file_path}'
        logging.info(file_url)
        logging.info(f"Attempting to open file: {file_url}")  # Debugging line to check the URL

        # Open the file in a new tab within the Selenium WebDriver
        try:
            self.driver.get(file_url)
            time.sleep(2)
        except Exception as e:
            raise Exception(f"Error opening file: {e}")
        except TimeoutError:
            raise TimeoutError("Timeout occurred while waiting for element to be visible.")

    def file_explorer_handler(self,path_file : str) -> None:
        """
        Handles the process of opening a file or dirctory in a file explorer by
        automating keyboard input. Ensures fast and efficient interaction with
        the user's file management syste
        Parameters:
        path_file (str): The full path to the file or directory that should be accessed.

        Raises:
        None
        """
        pyautogui.FAILSAFE = False
        pyautogui.write(path_file)
        pyautogui.press("enter")

    def move_to_element(self,path : str) ->None:
        """
        Perform a hover action over a specific web element located by the given XPath.

        This function locates a web element on a webpage using its XPath and triggers
        a hover action over the element. It utilizes WebDriverWait to ensure the element
        is visible before performing the hover action.

        Arguments:
            path (str): The XPath string of the target web element to hover over.
        """
        element = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, path)))
        action_start =ActionChains(self.driver)
        action_start.move_to_element(element).perform()

    def select_option(self,by_what,element: str,visible_text : str) :
        """
        Selects an option with the provided visible text from a dropdown menu.

        This method waits until the dropdown menu element is located on the web page
        and then selects an option by matching the visible text provided.

        Parameters:
        by_what : object
            The type of locator strategy used, such as By.ID, By.XPATH, etc.
        element : object
            The locator of the target dropdown menu element.
        visible_text : str
            The visible text of the option to be selected from the dropdown menu.
        """
        select_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((by_what, element))  # Replace with the correct locator
        )
        select = Select(select_element)
        select.select_by_visible_text(visible_text)

    def article_handler(self,path_id :str, print_file = None) -> pd.DataFrame:
        """
        Extracts and processes elements from a web page based on the provided XPATH and creates
        a dataframe containing the extracted data.

        Args:
            path_id: str
                The XPATH of the elements to be located on the webpage.

        Raises:
            Exception:
                If an unspecified error occurs during the operation.
            TimeoutError:
                If the operation times out while waiting for the elements to be visible.

        Returns:
            pandas.DataFrame
                A dataframe containing a single column 'Name' with the extracted text from
                the located web elements.
        """
        try :
            # WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_all_elements_located((By.XPATH, path_id))
            # )

            # Find all rows with the class "o_data_row" "//tr[@class='o_data_row']"
            rows = self.driver.find_elements(By.XPATH, path_id)

            # Extract the data_id attributes and display them
            total_article = []
            for row in rows:
                text_printed = row.text.strip()
                logging.info(row.text)
                total_article.append(text_printed)

            self.article_df = pd.DataFrame(total_article,
                                      columns=['Name'])
            if logging.info_file is not None:
                # Save to Excel
                self.article_df.to_excel("table_output.xlsx", index=False)
                os.startfile("table_output.xlsx")
                time.sleep(12)

        except Exception as e:
            raise Exception(f"Error occurred: {str(e)}")
        except TimeoutError:
            raise TimeoutError("Timeout occurred while waiting for element to be visible.")

        return self.article_df

    def table_extract(self, print_file=None, **kwargs):
        """
        Extract data from a dynamically loading table with improved wait mechanism.

        Args:
            logging.info_file: Optional file to save the extracted data
            **kwargs: Additional keyword arguments:
                max_retries: Maximum number of retries for stale elements (default: 3)
                retry_delay: Delay between retries in seconds (default: 1)
                wait_time: Maximum wait time for elements to load in seconds (default: 20)
                scroll_pause: Time to pause after scrolling in seconds (default: 2)
                initial_pause: Time to pause after finding table in seconds (default: 3)
                use_js: Whether to use JavaScript for extraction (default: True)

        Returns:
            DataFrame containing the extracted table data
        """
        # Set default params that can be overridden by kwargs
        params = {
            'max_retries': 3,
            'retry_delay': 1,
            'wait_time': 20,
            'scroll_pause': 2,
            'initial_pause': 3,
            'use_js': True
        }

        # Update with any provided kwargs
        params.update(kwargs)

        # Extract params for readability
        max_retries = params['max_retries']
        retry_delay = params['retry_delay']
        wait_time = params['wait_time']
        scroll_pause = params['scroll_pause']
        initial_pause = params['initial_pause']
        use_js = params['use_js']
        for attempt in range(max_retries):
            try:
                # Initialize WebDriverWait with longer timeout for dynamic content
                wait = WebDriverWait(self.driver, wait_time)

                # Find the table - wait until it's present in the DOM
                table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

                # Wait for rows to be visible - this helps with dynamic loading
                wait.until(EC.visibility_of_element_located((By.TAG_NAME, "tr")))

                # Try to detect when the table is fully loaded
                # Often there's a loading indicator that disappears or the number of rows stabilizes
                # Wait a bit more after finding the table
                time.sleep(initial_pause)  # Additional wait for dynamic content to fully render

                # Use JavaScript to get table rows count - helps with stability
                rows_count = self.driver.execute_script("return arguments[0].rows.length;", table)
                logging.info(f"Found {rows_count} rows in the table")

                # Try to scroll the table into view completely - helps with lazy loading
                self.driver.execute_script("arguments[0].scrollIntoView(true);", table)

                # Scroll to the bottom of the table to trigger any lazy loading
                self.driver.execute_script("""
                    arguments[0].scrollTop = arguments[0].scrollHeight;
                """, table)

                # Wait a bit more after scrolling
                time.sleep(scroll_pause)

                # Extract data using the appropriate method based on the use_js parameter
                data = []

                if use_js:
                    # Extract data using JavaScript for better reliability with dynamic content
                    data = self.driver.execute_script("""
                        const table = arguments[0];
                        const data = [];

                        // Get all rows
                        const rows = table.querySelectorAll('tr');

                        // Process each row
                        for (let i = 0; i < rows.length; i++) {
                            const row = rows[i];
                            const cells = row.querySelectorAll('td');

                            // Skip rows with no td elements (like headers)
                            if (cells.length > 0) {
                                const rowData = [];
                                for (let j = 0; j < cells.length; j++) {
                                    rowData.push(cells[j].textContent.trim());
                                }
                                data.push(rowData);
                            }
                        }

                        return data;
                    """, table)

                    # Get headers separately if they exist (th elements)
                    headers = self.driver.execute_script("""
                        const table = arguments[0];
                        const headers = [];
                        const headerCells = table.querySelectorAll('th');

                        for (let i = 0; i < headerCells.length; i++) {
                            headers.push(headerCells[i].textContent.trim());
                        }

                        return headers;
                    """, table)
                else:
                    # Traditional Selenium approach
                    headers = []
                    header_cells = table.find_elements(By.TAG_NAME, "th")
                    if header_cells:
                        headers = [cell.text.strip() for cell in header_cells]

                    # Get all rows
                    rows = table.find_elements(By.TAG_NAME, "tr")

                    for row in rows:
                        # Try to get all columns at once for this row
                        try:
                            cols = row.find_elements(By.TAG_NAME, "td")
                            if cols:  # skip header if no <td>
                                row_data = [col.text.strip() for col in cols]
                                data.append(row_data)
                        except Exception as e:
                            logging.info(f"Error processing row: {e}")
                            continue

                # Create DataFrame
                self.article_df = pd.DataFrame(data)
                logging.info(self.article_df)

                # If headers were found, use them as column names
                if headers and len(headers) == self.article_df.shape[1]:
                    self.article_df.columns = headers

                # Log success message with data shape
                logging.info(f"Successfully extracted table data with shape: {self.article_df.shape}")

                # Save to Excel if requested
                if logging.info_file is not None:
                    try:
                        # Save to Excel
                        self.article_df.to_excel("table_output.xlsx", index=False, mode='w')
                        os.startfile("table_output.xlsx")
                        time.sleep(12)
                        os.remove("table_output.xlsx")
                    except Exception as e:
                        logging.info(f"Error saving Excel file: {e}")

                return self.article_df

            except Exception as e:
                if attempt < max_retries - 1:
                    logging.info(f"Attempt {attempt + 1} failed with error: {e}. Retrying...")
                    time.sleep(retry_delay)
                else:
                    logging.info(f"Failed to extract table after {max_retries} attempts. Last error: {e}")
                    # Return empty DataFrame if all attempts fail
                    self.article_df = pd.DataFrame()
                    return self.article_df

    def close_log_file_handlers(self):
        for handler in logging.root.handlers[:]:
            if isinstance(handler, logging.FileHandler) and handler.baseFilename == self.log_file:
                handler.close()
                logging.root.removeHandler(handler)

    def delete_log_file(self, delay: int = 5) -> None:
        time.sleep(delay)
        retries = 5  # Number of retries before giving up
        for attempt in range(retries):
            try:
                if os.path.exists(self.log_file):
                    os.remove(self.log_file)
                    logging.info(f"Log file deleted: {self.log_file}")
                break  # Exit if file is successfully deleted
            except PermissionError:
                logging.info(f"File is locked, retrying... (Attempt {attempt + 1}/{retries})")
                time.sleep(1)

    def quit_driver(self, wait_time=10):
        """
        Kill all processes and delete log file.
        """
        if self.driver:
            self.driver.quit()
            logging.info("Web browser has stopped")

            # Kill ChromeDriver before deleting log file
            self.kill_all_chrome_processes()

            # Close logging handlers before deleting the file
            self.close_log_file_handlers()

            # Start the deletion in a background thread
            threading.Thread(target=self.delete_log_file, args=(5,), daemon=True).start()

    def kill_all_chrome_processes(self):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] == 'chromedriver':
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def save_existing_text_field(self, path: str) -> str:
        """
        Fetches and returns the text content from a visible text field located by the given XPath.
        """
        try:
            text_field = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, path))
            )

            # First try getting text
            text = text_field.text.strip()

            if not text:
                # If text is empty, try getting 'value' attribute (for input fields)
                text = text_field.get_attribute("value") or ""

            return text

        except (TimeoutException, NoSuchElementException) as e:
            logging.info(f"Error: {e}")
            raise

