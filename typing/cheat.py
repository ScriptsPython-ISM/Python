from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def create_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(executable_path="/Users/naoise.82258/homebrew/bin/chromedriver")
    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )
    return driver

def auto_typing_com():
    driver = create_driver()
    driver.get("https://www.typing.com/en-gb/student/tests")
    time.sleep(2)
    driver.find_element(By.XPATH, '//div[@data-id="1-page"]').click()
    time.sleep(2)
    driver.find_element(By.XPATH, '//button[@class="js-continue-button btn btn--a has-tooltip"]').click()

    time.sleep(2)
    input_area = driver.find_element(By.TAG_NAME, "body")
    while True:
        try:
            ch = driver.find_element(By.XPATH, '//div[contains(@class,"letter") and contains(@class,"active")]').text

            if ch == "" or ch == " ":
                ch = " "

            input_area.send_keys(ch)

        except NoSuchElementException:
            break

    input()
    driver.quit()

while True:
    auto_typing_com()
