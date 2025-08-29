import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

url = "https://www.cnbc.com/world/?region=world"
response = requests.get(url, headers=headers)

with open("../data/raw_data/web_data.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("Done")

