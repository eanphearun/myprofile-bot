import os
import requests
from flask import Flask, request

TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))

app = Flask(__name__)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    return requests.post(url, json=payload, timeout=10)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"RAW UPDATE: {data}")

    # Extract chat_id from any type of update
    chat_id = None
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
    elif "business_message" in data and "text" in data["business_message"]:
        chat_id = data["business_message"]["chat"]["id"]
    elif "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]

    if chat_id:
        print(f"Attempting to send message to {chat_id}")
        resp = send_message(chat_id, "Hello from bot! (test)")
        print(f"Telegram response: {resp.status_code} - {resp.text}")

    return 'ok', 200

@app.route('/')
def home():
    return 'Bot is running'