import requests
from bs4 import BeautifulSoup

url = "https://www.cnbc.com/world/?region=world"
response = requests.get(url)

with open("../data/raw_data/web_data.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("Done")
