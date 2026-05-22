import os
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
BIRD_BOT_LINK = "https://t.me/bird_nest_house_bot"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

CURRENT_MODE = "business"
user_state = {}

# ---------- TEMPORARY ECHO HANDLER (catch everything first) ----------
@bot.message_handler(func=lambda m: True, content_types=['text'])
def echo_all(message):
    print(f"ECHO received from {message.chat.id}: {message.text}")
    try:
        bot.reply_to(message, f"Echo: {message.text}")
        print("ECHO reply sent")
    except Exception as e:
        print(f"ECHO error: {e}")

# ---------- (Your other handlers are still here but overridden by echo) ----------
# I'll keep them commented out for now. We'll restore later.
# The business keyboard, /mode, /myid, etc. are inactive while echo is present.

# ---------- Flask routes ----------
@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    print(f"FULL UPDATE: {update}")
    bot.process_new_updates([update])
    return 'ok', 200

@app.route('/')
def home():
    return 'Bot is running'