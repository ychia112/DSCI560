import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

url = "https://www.cnbc.com/world/?region=world"
response = requests.get(url, headers=headers)

with open("../data/raw_data/web_data.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("Done")

