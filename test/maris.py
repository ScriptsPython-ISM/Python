from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import numpy as np

def create_driver() -> webdriver.Chrome:
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    service = Service(executable_path="/Users/naoise.82258/homebrew/bin/chromedriver")
    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )
    return driver

simulated_users = 10
drivers = [create_driver() for _ in range(simulated_users)]

for driver in drivers:
    driver.get("https://maris.iaea.org/explore")

time.sleep(20)

for driver in drivers:
    for _ in range(np.random.randint(1,10)):
        np.random.choice(driver.find_elements(By.XPATH, '//div[@apphelpcontent and @class[contains(., "st-icon")]]')).click()

time.sleep(5)
for driver in drivers:
    np.random.choice(driver.find_elements(By.XPATH, '//div[@class="filter-group"]')).click()
time.sleep(2)

for driver in drivers:
    np.random.choice(driver.find_elements(By.XPATH, '//span[@class="tool-container" and @]')).click()
    list_items = driver.find_elements(By.XPATH, '//div[@fxlayout="column" and @class[contains(., "list-group-item")]]')
    for _ in range(np.random.randint(1, len(list_items) + 1)):
        np.random.choice(list_items).click()

input()