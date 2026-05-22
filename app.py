import os
import requests
from flask import Flask, request

TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
BIRD_BOT_LINK = "https://t.me/bird_nest_house_bot"

app = Flask(__name__)

CURRENT_MODE = "business"           # or "daily"
user_state = {}                     # wholesale multi-step form data

# ---------- Telegram API helpers ----------
def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return requests.post(url, json=payload, timeout=10)

def answer_callback(callback_id, text=None):
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": callback_id}
    if text:
        payload["text"] = text
    requests.post(url, json=payload, timeout=10)

# ---------- Inline keyboard generators ----------
def business_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🛒 Buy Now", "url": BIRD_BOT_LINK},
             {"text": "📦 Wholesale Inquiry", "callback_data": "wholesale"}],
            [{"text": "❓ Learn More", "callback_data": "learn"},
             {"text": "💬 Talk to Human", "callback_data": "human"}]
        ]
    }

# ---------- Core message processor ----------
def process_message(chat_id, text, user_first_name, user_username):
    global user_state

    # Never auto-reply to yourself
    if chat_id == OWNER_ID:
        return

    # Continue wholesale form if active
    if chat_id in user_state:
        handle_wholesale_step(chat_id, text, user_first_name, user_username)
        return

    # Business mode
    if CURRENT_MODE == "business":
        send_message(
            chat_id,
            "👋 *Welcome to Bird's Nest House!*\n\n"
            "I'm an automated assistant. How can I help you today?",
            reply_markup=business_keyboard(),
            parse_mode="Markdown"
        )
    else:  # daily
        send_message(
            chat_id,
            "Hey! I saw your message – I'll get back to you as soon as I'm free.\n"
            "If it's urgent, send a 🔥 and I'll be notified."
        )

# ---------- Wholesale form steps ----------
def handle_wholesale_step(chat_id, text, first_name, username):
    state = user_state[chat_id]
    step = state["step"]

    if step == "ask_name":
        state["name"] = text.strip()
        state["step"] = "ask_company"
        send_message(chat_id, "Great, thanks! What's your company name?")
    elif step == "ask_company":
        state["company"] = text.strip()
        state["step"] = "ask_quantity"
        send_message(chat_id, "And roughly how many kilograms per month are you looking for?")
    elif step == "ask_quantity":
        state["quantity"] = text.strip()
        summary = (
            f"📦 *New Wholesale Lead*\n"
            f"Name: {state.get('name')}\n"
            f"Company: {state.get('company')}\n"
            f"Estimated monthly qty: {state.get('quantity')}\n"
            f"User ID: `{chat_id}`"
            f"{(' @' + username) if username else ''}"
        )
        send_message(OWNER_ID, summary, parse_mode="Markdown")
        send_message(chat_id, "✅ Thank you! Your enquiry has been forwarded. The owner will contact you shortly.")
        del user_state[chat_id]

# ---------- Callback query handler ----------
def handle_callback(callback):
    data = callback["data"]
    cb_id = callback["id"]
    msg = callback.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    user_info = callback.get("from", {})
    first_name = user_info.get("first_name", "there")
    username = user_info.get("username")

    if data == "learn":
        send_message(
            chat_id,
            "🍃 *Edible Bird's Nest* is a premium superfood known for:\n"
            "• Boosting immunity\n"
            "• Improving skin complexion\n"
            "• Supporting respiratory health\n\n"
            "All our nests are 100% natural, hand‑cleaned, and sourced sustainably.\n"
            "Ready to try? Tap *Buy Now* to visit our shop!",
            reply_markup=business_keyboard(),
            parse_mode="Markdown"
        )
        answer_callback(cb_id)

    elif data == "wholesale":
        user_state[chat_id] = {"step": "ask_name"}
        send_message(chat_id, "📋 Let's set up a wholesale account. First, what's your full name?")
        answer_callback(cb_id)

    elif data == "human":
        send_message(
            OWNER_ID,
            f"📩 *Human reply requested* by {first_name}"
            f"{(' @' + username) if username else ''}\n"
            f"User ID: `{chat_id}`",
            parse_mode="Markdown"
        )
        send_message(chat_id, "Thanks! I've notified the owner and they'll reply personally soon.")
        answer_callback(cb_id)

# ---------- Command handler (private chats only) ----------
def handle_command(chat_id, text):
    if chat_id != OWNER_ID:
        return

    parts = text.split()
    cmd = parts[0].lower()

    if cmd == "/mode" and len(parts) > 1 and parts[1] in ["business", "daily"]:
        global CURRENT_MODE
        CURRENT_MODE = parts[1]
        send_message(chat_id, f"✅ Mode switched to *{CURRENT_MODE}*", parse_mode="Markdown")

    elif cmd == "/myid":
        send_message(chat_id, f"Your chat ID: `{chat_id}`", parse_mode="Markdown")

# ---------- Main webhook ----------
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"UPDATE: {data}")

    # 1) Callback query (inline button press)
    if "callback_query" in data:
        handle_callback(data["callback_query"])
        return 'ok', 200

    # 2) Normal message
    msg = data.get("message", {})
    if msg:
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "").strip()

        # Check if it's a command
        if text.startswith("/"):
            handle_command(chat_id, text)
        else:
            user = msg.get("from", {})
            process_message(chat_id, text,
                            user.get("first_name", "there"),
                            user.get("username"))
        return 'ok', 200

    # 3) Business message (Secretary Mode)
    bmsg = data.get("business_message", {})
    if bmsg:
        chat_id = bmsg.get("chat", {}).get("id")
        text = bmsg.get("text", "").strip()

        if not text.startswith("/"):
            user = bmsg.get("from", {})
            process_message(chat_id, text,
                            user.get("first_name", "there"),
                            user.get("username"))
        return 'ok', 200

    return 'ok', 200

@app.route('/')
def home():
    return 'Bot is running'