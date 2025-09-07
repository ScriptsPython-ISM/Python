from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def im_not_a_toddler():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("")

    service = Service(executable_path="/Users/naoise.82258/homebrew/Caskroom/chromedriver/140.0.7339.80/chromedriver-mac-arm64/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get("https://web.toddleapp.com/platform/7571/courses")

im_not_a_toddler()