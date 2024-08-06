import time
from pyrogram import Client
import os
from dotenv import load_dotenv

load_dotenv()
session_string = os.getenv('session_string')
channel_id = os.getenv('telegram_channel')


def send_message_list(message_list):
    count = 0
    app = Client(session_string=session_string, name='pyrogram')
    if message_list:
        with app:
            for message in message_list:
                count += 1
                app.send_message(int(channel_id), message.get('html_text'))
                print(f"Message sent : {count} / {len(message_list)}")
                time.sleep(1)
    return True
