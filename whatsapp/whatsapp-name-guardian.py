from selenium import webdriver
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import numpy as np
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from metaphone import doublemetaphone
import difflib

def similar(word1, word2, threshold=0.8):
    sound1 = doublemetaphone(word1)
    sound2 = doublemetaphone(word2)
    ratio = difflib.SequenceMatcher(None, word1.lower(), word2.lower()).ratio()
    return sound1 == sound2 and ratio > threshold

options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=./User_Data") 
options.add_argument("--profile-directory=Default")  
options.add_argument("--disable-dev-shm-usage")
#options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--remote-debugging-port=9222")
chrome_path = "C:/Users/pmcgi/Downloads/chrome-win64/chrome-win64/chrome.exe"
options.binary_location = chrome_path

service = Service("C:/Users/pmcgi/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://web.whatsapp.com")
print("Please scan the QR code (if needed)...")

group_name = input("Target Group:")
messages = ["Wesh", "skibidi toilet", "No", "Stop", "Hey this is a family friendly groupchat buddy, watch ur language"]

search_box = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')))
search_box.click()
search_box.send_keys(group_name)
search_box.send_keys(Keys.ENTER)
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, '//div[@role="button" and @title="Profile details"]'))).click()

try:
    while True:
        time.sleep(2)
        texts = driver.find_element(By.XPATH, "//div[contains(@aria-label, 'Group profile picture for')]").get_attribute("aria-label").removeprefix("Group profile picture for \"").removesuffix("\"")
        print(texts)
        texts = texts.split()
        for text in texts:
            if similar(text, "nigger") or similar(text, "ez") or similar(text, "nigga") or similar(text, "banana") or similar(text, "nique") or similar(text, "dih"):
                driver.find_element(By.XPATH, '//button[@title="Click to edit group subject"]').click()
                textbox = driver.find_element(By.XPATH, f'//div[@role="textbox" and @title="{text}"]//span[@data-lexical-text="true"]')
                webdriver.ActionChains(driver)\
                    .key_down(Keys.SHIFT)\
                    .send_keys(Keys.PAGE_UP)\
                    .key_up(Keys.SHIFT)\
                    .perform()
                textbox.send_keys(np.random.choice(messages))
                textbox.send_keys(Keys.ENTER)
except KeyboardInterrupt:
    print("Stopped by user")
finally:
    driver.quit()
