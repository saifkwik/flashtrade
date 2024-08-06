import hashlib
import json
import os
import pprint
from datetime import datetime
import dateparser
from telegram import send_message_list
import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image


headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}


def get_kotak_news():
    updates = []
    response = requests.get('https://lapi.kotaksecurities.com/1news/search?category=All', headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        results = response_json["data"]
        for result in results:
            data = {
                "date": dateparser.parse(result["date"]).isoformat(),
                "description": result["description"],
                "category": "".join(result["categories"]),
                "_id": hashlib.md5(f'{result["date"]}{result["description"]}'.encode()).hexdigest(),
            }
            if data not in updates and data['description']:
                updates.append(data)
    return updates


def get_ind_news():
    updates = []
    response = requests.get('https://apixt-iw.indmoney.com/wright/api/web/v1/markets/today?only_news=true', headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        live_news = response_json["data"]["live_news"]
        if live_news:
            news_list = live_news['list']
            for news in news_list:
                heading = news['heading']
                current_price = f"Rs {news['live_price']} ({news['oneD_change']}%)"
                date = f'{news["date"]} {news["time"]}'
                logo = news['logo']
                stock_name = news['stock_name']
                data = {
                    "description": heading,
                    "current_price": current_price,
                    "category": "Equity",
                    "date": dateparser.parse(date).isoformat(),
                    "logo": logo,
                    "stock_name": stock_name,
                    "_id": hashlib.md5(f'{heading}{date}'.encode()).hexdigest(),
                }
                if data not in updates:
                    updates.append(data)
    return updates


def get_existing_ids():
    ids = []
    with open('news.json', 'r') as f:
        data = json.load(f)
        for item in data:
            ids.append({"_id": item['_id'], "date": item['date']})
    return ids


def create_doc_html(doc):
    html_text = ""
    html_text += f"<b>{doc['description']}</b>\n\n"
    html_text += f"<i>time: {dateparser.parse(doc['date']).time()}</i>\n"
    if doc.get('logo'):
        html_text += f"{doc['logo']}\n"
    if doc.get('category'):
        html_text += f"category: {doc['category'].lower()}\n"
    if doc.get('stock_name'):
        html_text += f"stock: {doc['stock_name']}\n"
    if doc.get('current_price'):
        html_text += f"price: {doc['current_price']}\n"
    if doc.get('ascii_img'):
        html_text += f"{doc['ascii_img']}"
    return html_text


def sketch_image(url):
    if not "images" in os.listdir():
        os.mkdir("images")
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    width, height = image.size
    print(width, height)

    # Check the mode of the image
    if image.mode == 'L':  # Grayscale
        new_img = Image.new('L', (width, height))
        for row in range(height):
            for col in range(width):
                avg = image.getpixel((col, row))
                new_img.putpixel((col, row), avg)
    else:  # RGB or RGBA
        new_img = Image.new('RGB', (width, height))
        for row in range(height):
            for col in range(width):
                pixel = image.getpixel((col, row))
                if isinstance(pixel, tuple) and len(pixel) == 4:  # RGBA
                    r, g, b, a = pixel
                elif isinstance(pixel, tuple):  # RGB
                    r, g, b = pixel
                else:  # Grayscale but not 'L' mode
                    r = g = b = pixel
                avg = int((r + g + b) / 3)
                new_img.putpixel((col, row), (avg, avg, avg))

    hash_url = hashlib.md5(url.encode()).hexdigest()
    new_img.save(f'images/{hash_url}_sketch.png')
    return hash_url

def get_data(force_send=False):
    if not os.path.exists('news.json'):
        with open('news.json', 'w') as f:
            json.dump([], f, indent=4)
    existing_ids = get_existing_ids()
    print(f"{len(existing_ids)} existing articles found, last article date: {existing_ids[-1]['date']}") if existing_ids else print("No existing articles found")
    combined_news = []
    kotak_news = get_kotak_news()
    ind_news = get_ind_news()
    combined_news.extend(kotak_news)
    combined_news.extend(ind_news)
    _existing_ids = [_ex["_id"] for _ex in existing_ids]
    if not force_send:
        new_articles = [x for x in combined_news if x["_id"] not in _existing_ids]
    else:
        new_articles = combined_news
    print(f"{len(new_articles)} new articles found")
    new_articles = sorted(new_articles, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%dT%H:%M:%S'))
    new_articles = [{**doc, 'file_path': sketch_image(url=doc.get('logo'))} for doc in new_articles if doc.get('logo')]
    new_articles = [{**doc, 'html_text': create_doc_html(doc)} for doc in new_articles]
    with open('news.json', 'w') as f:
        json.dump(new_articles, f, indent=4)
    exit()
    msg_status = send_message_list(new_articles)
    if msg_status : print(f"Success")
    return new_articles


if __name__ == "__main__":
    data = get_kotak_news()
    news = get_data(force_send=True)
    pprint.pprint(news)
    print(len(news))
    # sketch_image(url=True)