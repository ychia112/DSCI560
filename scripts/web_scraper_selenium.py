from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import os

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")

service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

print("Loading website...")
driver.get("https://www.cnbc.com/world/?region=world")

time.sleep(5)

html = driver.page_source
driver.quit()

os.makedirs("../data/raw_data", exist_ok=True)
with open("../data/raw_data/web_data.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Web scraping done.")
