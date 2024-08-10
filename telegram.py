import asyncio
import time
from pyrogram import Client
import os
from dotenv import load_dotenv

load_dotenv()
session_string = os.getenv('session_string')
channel_id = os.getenv('telegram_channel')


def send_message_list(message_list):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    app = Client(session_string=session_string, name='pyrogram')
    count = 0
    if message_list:
        with app:
            for message in message_list:
                count += 1
                if not message.get('file_path'):
                    app.send_message(chat_id=int(channel_id), text=message.get('html_text'))
                else:
                    app.send_photo(chat_id=int(channel_id), photo=message.get('file_path'), caption=message.get('html_text'))
                print(f"Message sent : {count} / {len(message_list)}")
                time.sleep(1)
    return True