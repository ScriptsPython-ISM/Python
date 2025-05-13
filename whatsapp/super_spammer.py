from selenium import webdriver
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# === CHROME OPTIONS ===
options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=./User_Data")  # Keeps login session
options.add_argument("--profile-directory=Default")  # Use default Chrome profile
options.add_argument("--disable-dev-shm-usage")     # Prevent shared memory issues
#options.add_argument("--headless")
options.add_argument("--no-sandbox")                # Required in some setups
options.add_argument("--remote-debugging-port=9222") # Prevent DevTools error
chrome_path = "C:/Users/pmcgi/Downloads/chrome-win64/chrome-win64/chrome.exe"  # Change this to your Chrome path
options.binary_location = chrome_path

# === SERVICE AND DRIVER ===
service = Service("C:/Users/pmcgi/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

# === Your script continues here...
driver.get("https://web.whatsapp.com")
print("Please scan the QR code (if needed)...")
input("Press Enter after WhatsApp Web is ready...")

# Example: Find the chat by name and send a message
group_name = "Gabriel"  # Replace with your group name
message = "Wesh"

# === FIND GROUP CHAT ===
search_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
search_box.click()
search_box.send_keys(group_name)
search_box.send_keys(Keys.ENTER)

# === SEND MESSAGES TO GROUP ===
try:
    while True:
        msg_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        msg_box.click()
        msg_box.send_keys(message + Keys.ENTER)
        #time.sleep(0.1)  # Adjust the interval as needed
except KeyboardInterrupt:
    print("Stopped by user.")
finally:
    driver.quit()
