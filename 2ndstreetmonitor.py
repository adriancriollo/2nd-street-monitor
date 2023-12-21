import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

from config import webhook_url, webhook_url2

options = Options()
options.add_argument("--headless")

def get_items():
    with webdriver.Chrome(options=options) as driver:
        driver.get('https://ec.2ndstreetusa.com/collections/new-arrivals-order?sort_by=published')
        time.sleep(5)
        html_content = driver.page_source
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    items = soup.find_all('li', class_=lambda x: x and 'snize-product' in x and 'snize-product-in-stock' in x)

    product_details = []
    for item in items:
        title = item.find('span', class_='snize-title').get_text(strip=True) if item.find('span', class_='snize-title') else 'No Title'
        price = item.find('span', class_='snize-price').get_text(strip=True) if item.find('span', class_='snize-price') else 'No Price'
        
        link_tag = item.find('a', class_='snize-view-link')
        product_link = link_tag['href'] if link_tag else 'No Link'
        product_link = 'https://ec.2ndstreetusa.com' + product_link if product_link != 'No Link' else product_link

        product_details.append({'title': title, 'price': price, 'link': product_link})
    
    return product_details

def send_to_discord(message):
    data = {"content": message}
    response = requests.post(webhook_url, json=data)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        print(f"Error sending message: {error}")
        print("Response content:", response.content)
        raise
    response2 = requests.post(webhook_url2, json=data)
    try:
        response2.raise_for_status()
    except requests.exceptions.HTTPError as error:
        print(f"Error sending message: {error}")
        print("Response content:", response2.content)
        raise

# Scheduler Initialization
scheduler = BlockingScheduler(timezone=pytz.utc)

# Initial fetch
last_items = get_items()
print("Initial items fetched")

initial_check = True

def check_for_new_items():
    global last_items, initial_check
    current_items = get_items()

    new_items = [item for item in current_items if item not in last_items]
    last_items = current_items

    if new_items and not initial_check:
        for item in new_items:
            send_to_discord(f"New item found:\nTitle: {item['title']}\nPrice: {item['price']}\nLink: {item['link']}")
    elif initial_check:
        print("Initial check completed. Future new items will be sent to Discord.")
    else:
        print("No new items")

    initial_check = False  # Reset the flag after the first run

# Schedule the function 'check_for_new_items' to be called every 1 minute
scheduler.add_job(check_for_new_items, 'interval', minutes=1)

scheduler.start()

