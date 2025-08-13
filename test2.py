from selenium import webdriver
from selenium.webdriver.chrome.options import Options

SELENOID_URL = "http://localhost:4444/wd/hub"

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--headless=new")

driver = webdriver.Remote(
    command_executor=SELENOID_URL,
    options=options
)

driver.get("https://www.google.com")
print(driver.title)

driver.quit()
