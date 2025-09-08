from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os

EMAIL = os.getenv("TODDLE_EMAIL")
PASSWORD = os.getenv("TODDLE_PASSWORD")

def im_not_a_toddler():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("")
    global driver
    service = Service(executable_path=os.path.expanduser("~/homebrew/bin/chromedriver"))
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get("https://web.toddleapp.com/platform/7571/courses")

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '//div[@data-test-id="button-login-student"]')))

    driver.find_element(By.XPATH, '//div[@data-test-id="button-login-student"]').click()
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '//button[@data-test-id="button-login-google-button"]')))
    time.sleep(2)
    driver.find_element(By.XPATH, '//button[@data-test-id="button-login-google-button"]').click()
    try:WebDriverWait(driver, 4).until(EC.new_window_is_opened(driver.window_handles))
    except TimeoutException: pass
    driver.switch_to.window(driver.window_handles[-1])
    driver.find_element(By.XPATH, '//input[@type="email" and @name="identifier"]').send_keys(EMAIL)
    driver.find_element(By.XPATH, '//div[@id="identifierNext"]').click()
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//input[@type="password" and @name="Passwd"]')))
    time.sleep(4)
    driver.find_element(By.XPATH, '//input[@type="password" and @name="Passwd"]').send_keys(PASSWORD)
    driver.find_element(By.XPATH, '//div[@id="passwordNext"]').click()
    driver.switch_to.window(driver.window_handles[0])
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH ,'//button[.//span[text()="View all"]]')))
    driver.find_element(By.XPATH, '//button[.//span[text()="View all"]]').click()

def extract_toddle_tasks():
    global driver
    tasks = []

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='Todos__bodyContainer']"))
    )

    time.sleep(2)

    feed_bodies = driver.find_elements(By.CSS_SELECTOR, "div[class*='FeedList__body']")

    for body in feed_bodies:
        feed_items = body.find_elements(By.CSS_SELECTOR, "div[class*='FeedItem__container']")

        for item in feed_items:
            url_suffix = item.get_attribute("data-test-id")
            if url_suffix:
                url_suffix = url_suffix.removeprefix("todos-feedList-feedItem-").removesuffix("-feedItem")
            else:
                url_suffix = ""

            try:
                title = item.find_element(By.CSS_SELECTOR, "div[class*='FeedItem__assessmentName']").text.strip()
            except:
                title = ""

            try:
                course = item.find_element(By.CSS_SELECTOR, "div[class*='FeedItem__bottomTextTitle']").text.strip()
            except:
                course = ""

            try:
                due = item.find_element(By.CSS_SELECTOR, "div[class*='FeedItem__bottomTextV2']").text.strip()
            except:
                due = ""

            tasks.append({
                "title": title,
                "course": course,
                "due": due,
                "url": f"https://web.toddleapp.com/platform/7571/todos/classroom-details/289622177655817635/{url_suffix}"
            })

    return tasks

from datetime import datetime
import dateparser

def parse_due(due_str):
    dt = dateparser.parse(due_str)
    if dt:
        return {"start": dt.isoformat()}
    return None

def export_to_notion(tasks):
    from notion_client import Client
    import os

    notion = Client(auth=os.getenv("NOTION_KEY"))
    DATABASE_ID = "2680e052294a80e0bd97fa85de159d0a"

    existing_pages = []
    next_cursor = None

    while True:
        response = notion.databases.query(
            **{"database_id": DATABASE_ID, "start_cursor": next_cursor} if next_cursor else {"database_id": DATABASE_ID}
        )
        existing_pages.extend(response["results"])
        if response.get("next_cursor"):
            next_cursor = response["next_cursor"]
        else:
            break

    for task in tasks:
        match = None
        for page in existing_pages:
            props = page["properties"]
            name = props.get("Title", {}).get("title", [])
            course = props.get("Class", {}).get("rich_text", [])
            if name and course:
                name_text = name[0]["text"]["content"]
                course_text = course[0]["text"]["content"]
                if name_text == task["title"] and course_text == task["course"]:
                    match = page
                    break

        if match:
            done = match["properties"].get("Done", {}).get("checkbox", False)
            if not done:
                updated_page = notion.pages.update(
                    page_id=match["id"],
                    properties={
                        "Due Date": {"date": parse_due(task["due"])},
                        "URL": {"url": task["url"]}
                    }
                )
                print(f"Updated existing task: {task['title']}")
                existing_pages.append(updated_page)
        else:
            new_page = notion.pages.create(
                parent={"database_id": DATABASE_ID},
                properties={
                    "Title": {"title": [{"text": {"content": task["title"]}}]},
                    "Class": {"rich_text": [{"text": {"content": task["course"]}}]},
                    "Due Date": {"date": parse_due(task["due"])},
                    "URL": {"url": task["url"]},
                    "Done": {"checkbox": False}
                }
            )
            print(f"Created new task: {task['title']}")
            existing_pages.append(new_page)

    print("All tasks processed.")
    

im_not_a_toddler()
tasks = extract_toddle_tasks()
export_to_notion(tasks)