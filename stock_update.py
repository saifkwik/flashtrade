import hashlib
import json
import os
import pprint
from datetime import datetime
import requests
import dateparser
from telegram import send_message_list
from ascii_magic import AsciiArt, Front, Back
from ascii_magic import AsciiArt
from PIL import ImageEnhance
from PIL import Image, ImageDraw

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


def convert_img_ascii(img_url):
    hash_url = hashlib.md5(img_url.encode()).hexdigest()
    if not os.path.exists(f'images/{hash_url}.png'):
        with open(f'images/{hash_url}.png', 'wb') as f:
            f.write(requests.get(img_url).content)
    my_art = AsciiArt.from_image(f'images/{hash_url}.png')
    # my_art.image = ImageEnhance.Brightness(my_art.image).enhance(1)
    img_width, img_height = my_art.image.size
    img = Image.new('RGB', (img_width, img_height), color='white')
    img_draw = ImageDraw.Draw(img)
    img_draw.text((100, 100), my_art.to_ascii(columns=200), fill='black')
    output_image_path = f'images/{hash_url}_ascii.png'
    img.save(output_image_path)
    print(f"Saved ASCII art as {output_image_path}")


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
    new_articles = [{**doc, 'ascii_img': convert_img_ascii(doc['logo'])} for doc in new_articles if doc.get('logo')]

    new_articles = [{**doc, 'html_text': create_doc_html(doc)} for doc in new_articles]
    with open('news.json', 'w') as f:
        json.dump(new_articles, f, indent=4)
    msg_status = send_message_list(new_articles)
    if msg_status : print(f"Success")
    return new_articles


if __name__ == "__main__":
    data = get_kotak_news()
    news = get_data(force_send=True)
    pprint.pprint(news)
    print(len(news))
    # img_ascii()