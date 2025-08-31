import csv
from bs4 import BeautifulSoup
import os
import re

print("Loading html file...")

html_file = "../data/raw_data/web_data.html"
with open(html_file, 'r', encoding='utf-8') as file:
    html_content = file.read()

soup = BeautifulSoup(html_content, 'html.parser')

os.makedirs("../data/processed_data", exist_ok=True)
print("Start filtering market data...")

market_data = []

market_banner = soup.find('div', class_='MarketsBanner-main')
market_data_container = market_banner.find('div', class_='MarketsBanner-marketData')
if not market_data_container:
    print("no market data")
market_containers = market_data_container.find_all('a', class_=lambda x: x and 'MarketCard-container' in x)

for container in market_containers:
    try:
        first_row = container.find('div', class_='MarketCard-row')
        symbol = first_row.find('span', class_='MarketCard-symbol').get_text(strip=True)
        position = first_row.find('span', class_='MarketCard-stockPosition').get_text(strip=True)

        rows = container.find_all('div', class_='MarketCard-row')
        second_row = rows[1]
        change_data = second_row.find('div', class_='MarketCard-changeData')
        change_pct = change_data.find('span', class_='MarketCard-changesPct').get_text(strip=True)

        market_data.append({
            'marketCard_symbol': symbol,
            'marketCard_stockPosition': position,
            'marketCard_changesPct': change_pct
        })
    except Exception as e:
        print(e)
        continue

print(f"Found {len(market_data)} market entries")
print("Storing Market data...")

with open("../data/processed_data/market_data.csv", 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['marketCard_symbol', 'marketCard_stockPosition', 'marketCard_changesPct']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(market_data)

print("Start filtering LatestNews...")

news_data = []

news_list_container = soup.find('ul', class_='LatestNews-list')

if news_list_container:
    print("Found LatestNews-list conatiner")
    news_items = news_list_container.find_all('li', class_='LatestNews-item')
    print(f"Found {len(news_items)} news")
    for i, item in enumerate(news_items):
        news_container = item.find('div', class_='LatestNews-container')
        headline_wrapper = news_container.find('div', class_='LatestNews-headlineWrapper')
        timestamp_elem = headline_wrapper.find('time', class_='LatestNews-timestamp')
        timestamp_text = timestamp_elem.get_text(strip=True) if timestamp_elem else "no timestamp"
        headline_link = headline_wrapper.find('a', class_='LatestNews-headline') if headline_wrapper else "no headline wrapper"
        title = headline_link.get('title','')
        href = headline_link.get('href', '')

        news_data.append({
            'LatestNews_timestamp': timestamp_text,
	    'title': title,
	    'link': href
	    })


print("Storing News data...")
news_csv_path = "../data/processed_data/news_data.csv"
with open(news_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['LatestNews_timestamp', 'title', 'link']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(news_data)

print("CSV created: news_data.csv")
print("Data filtering process completed.")
