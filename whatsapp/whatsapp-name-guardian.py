from selenium import webdriver
import time
import re
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import numpy as np
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from metaphone import doublemetaphone
from jellyfish import soundex
import difflib

class SuperBreak(Exception): pass

def similar(word1, word2, threshold=0.8):
    soundex1 = soundex(word1)
    soundex2 = soundex(word2)
    if soundex1 == soundex2:
        doublemetaphone1 = doublemetaphone(word1)
        doublemetaphone2 = doublemetaphone(word2)
        if doublemetaphone1 == doublemetaphone2:
            ratio1 = difflib.SequenceMatcher(None, word1.lower(), word2.lower()).ratio()
            return ratio1 > threshold
    return False

options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=./User_Data") 
options.add_argument("--profile-directory=Default")  
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-background-networking")
options.add_argument("--disable-default-apps")
options.add_argument("--disable-sync")
options.add_argument("--disable-extensions")
options.add_argument("--disable-notifications")
options.add_argument("--mute-audio")
options.add_argument("--no-default-browser-check")
options.add_argument("--disable-popup-blocking")
#options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--remote-debugging-port=9222")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
chrome_path = "C:/Users/pmcgi/Downloads/chrome-win64/chrome-win64/chrome.exe"
options.binary_location = chrome_path

service = Service("C:/Users/pmcgi/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://web.whatsapp.com")
print("Please scan the QR code (if needed)...")

group_name = input("Target Group:")
messages = ["Wesh", "skibidi toilet", "No", "Stop", "Hey this is a family friendly groupchat buddy, watch ur language"]
bad = ["nigger", "ez", "nigga", "banana", "nique", "dih"]

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
        sentence = driver.find_element(By.XPATH, "//div[contains(@aria-label, 'Group profile picture for')]").get_attribute("aria-label").removeprefix("Group profile picture for \"").removesuffix("\"")
        print(sentence)
        texts = sentence.split(' ')
        """try:
            for text in texts:
                for test in bad:
                    if similar(text, test):
                        driver.find_element(By.XPATH, '//button[@title="Click to edit group subject"]').click()
                        textbox = driver.find_element(By.XPATH, f'//div[@role="textbox" and @title="{sentence}"]//span[@data-lexical-text="true"]')
                        webdriver.ActionChains(driver)\
                            .key_down(Keys.SHIFT)\
                            .send_keys(Keys.PAGE_UP)\
                            .key_up(Keys.SHIFT)\
                            .perform()
                        textbox.send_keys(np.random.choice(messages))
                        textbox.send_keys(Keys.ENTER)
                        raise SuperBreak
        except SuperBreak:
            pass"""
        if re.search(r'nigger|nigga|ez|dih|nique|banana', sentence, re.IGNORECASE):
            driver.find_element(By.XPATH, '//button[@title="Click to edit group subject"]').click()
            textbox = driver.find_element(By.XPATH, f'//div[@role="textbox" and @title="{sentence}"]//span[@data-lexical-text="true"]')
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
