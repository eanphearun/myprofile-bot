import os
import requests
from flask import Flask, request

# ---------- Config ----------
TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
BIRD_BOT_LINK = "https://t.me/bird_nest_house_bot"

app = Flask(__name__)

# ---------- Global state ----------
CURRENT_MODE = "business"       # "business" ឬ "daily"
user_state = {}                 # wholesale form
tutorial_step = {}              # tutorial navigation

# ---------- Telegram API helpers ----------
def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
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

# ---------- Keyboards ----------
def main_keyboard():
    """ក្ដារចុចមេសម្រាប់របៀបពាណិជ្ជកម្ម"""
    return {
        "inline_keyboard": [
            [{"text": "🛒 បើក Mini App ទិញទំនិញ", "url": BIRD_BOT_LINK}],
            [{"text": "📖 របៀបប្រើ Mini App", "callback_data": "tutorial_start"}],
            [{"text": "📦 សាកសួរបោះដុំ", "callback_data": "wholesale"}],
            [{"text": "💬 និយាយជាមួយបុគ្គលិក", "callback_data": "human"}]
        ]
    }

def tutorial_nav_keyboard(step, max_step):
    """ប៊ូតុងត្រឡប់/បន្ទាប់ និងបិទមេរៀន"""
    buttons = []
    if step > 1:
        buttons.append({"text": "⬅ ត្រឡប់ក្រោយ", "callback_data": f"tutorial_{step-1}"})
    if step < max_step:
        buttons.append({"text": "បន្ទាប់ ➡", "callback_data": f"tutorial_{step+1}"})
    return {
        "inline_keyboard": [
            buttons,  # អាចទទេប្រសិនបើគ្មានប៊ូតុង
            [{"text": "❌ បិទមេរៀន", "callback_data": "tutorial_close"}]
        ]
    }

# ---------- Tutorial content (5 steps) ----------
TUTORIAL_TEXTS = {
    1: (
        "📖 *មេរៀនទី១៖ ស្វាគមន៍!*\n\n"
        "🍃 *សំបុកត្រចៀកកាំ Bird Nest House* ជាហាងផលិតផលត្រចៀកកាំ!\n"
        "យើងផ្តល់ជូនការបញ្ជាទិញតាម Telegram Mini App ដែលងាយស្រួល និងមានប្រម៉ូសិនពិសេសៗជាច្រើន។\n\n"
        "📌 *ហេតុអ្វីត្រូវប្រើ Mini App?*\n"
        "• បញ្ជាទិញដោយមិនចាំបាច់ទាក់ទងផ្ទាល់\n"
        "• មានពិន្ទុសន្សំ បញ្ចុះតម្លៃ\n"
        "• ការដឹកជញ្ជូនឥតគិតថ្លៃលើសពី ៣០ដុល្លារក្នុងក្រុង\n"
        "• ការទូទាត់ងាយស្រួលតាម KHQR / សាច់ប្រាក់\n\n"
        "ចុច *បន្ទាប់ ➡* ដើម្បីមើលជំហានបន្ត។"
    ),
    2: (
        "📖 *មេរៀនទី២៖ ចាប់ផ្តើម*\n\n"
        "1. ចុចលើប៊ូតុង *ចាប់ផ្តើម* នៅក្នុង @bird_nest_house_bot\n"
        "2. រួចចុច *🍽️ Open Order Menu* ដើម្បីបើក Mini App\n\n"
        "👉 អ្នកក៏អាចចុច *🛒 បើក Mini App* ខាងក្រោមដោយផ្ទាល់។"
    ),
    3: (
        "📖 *មេរៀនទី៣៖ ជ្រើសរើសផលិតផល*\n\n"
        "នៅក្នុង Mini App អ្នកនឹងឃើញ៖\n"
        "• 🥤 ទឹកត្រចៀកកាំ (75ml, 100ml, 150ml...)\n"
        "• 🥚 សំបុកត្រចៀកកាំស្ងួត (ថ្នាក់ A, Konkat)\n"
        "• 🎁 ឈុតអំណោយ\n\n"
        "អ្នកអាចស្វែងរក ឬជ្រើសរើសតាមប្រភេទ។\n"
        "ផលិតផលដែលមានប្រម៉ូសិននឹងបង្ហាញផ្លាក *\"-10% OFF\"* ជាដើម។"
    ),
    4: (
        "📖 *មេរៀនទី៤៖ ដាក់ក្នុងកន្ត្រក និងប្រើពិន្ទុ*\n\n"
        "• ចុច '+' ដើម្បីបង្កើនចំនួន\n"
        "• ចុច 'Add to Cart' ដើម្បីបញ្ចូល\n"
        "• នៅផ្ទាំង 🛒 Cart អ្នកអាចឃើញសរុបថ្លៃ ការបញ្ចុះតម្លៃ និងថ្លៃដឹក។\n"
        "• បើមានពិន្ទុគ្រប់ អ្នកអាចធីកប្រើពិន្ទុដើម្បីបញ្ចុះតម្លៃ (100pts = $1)។"
    ),
    5: (
        "📖 *មេរៀនទី៥៖ បញ្ជាទិញ និងទូទាត់*\n\n"
        "• ជ្រើសរើសពេលវេលាដឹកជញ្ជូន\n"
        "• ចុច 'Proceed to Payment'\n"
        "• ជ្រើសរើសវិធីទូទាត់៖ KHQR / សាច់ប្រាក់ / កាត\n"
        "• បើជ្រើស KHQR សូមស្កេន QR និងផ្ទេរប្រាក់\n"
        "• ចុច 'I've Paid — Confirm Order'\n\n"
        "✅ ការបញ្ជាទិញរបស់អ្នកត្រូវបានបញ្ជូនទៅអ្នកលក់ហើយ!\n"
        "សូមចាំថា អ្នកអាចជជែកជាមួយអ្នកលក់បានគ្រប់ពេល។"
    )
}
MAX_TUTORIAL = 5

# ---------- Core message processing ----------
def process_message(chat_id, text, user_first_name, user_username):
    """ដំណើរការសារចូល (ទាំងពី Private Chat និង Profile)"""
    # មិនឆ្លើយតបទៅខ្លួនឯង
    if chat_id == OWNER_ID:
        return

    # បើកំពុងស្ថិតក្នុងទម្រង់លក់ដុំ
    if chat_id in user_state:
        handle_wholesale_step(chat_id, text, user_first_name, user_username)
        return

    # តាមរបៀបដែលបានកំណត់
    if CURRENT_MODE == "business":
        send_message(
            chat_id,
            f"សួស្ដី {user_first_name}! 👋\n\n"
            "ខ្ញុំជាជំនួយការរបស់លោកភារុន *ផ្ទះត្រចៀកកាំ Bird Nest House*។\n"
            "ខាងក្រោមនេះជាជម្រើសដែលអ្នកអាចជ្រើសរើស៖",
            reply_markup=main_keyboard(),
            parse_mode="Markdown"
        )
    else:  # daily mode
        send_message(
            chat_id,
            "👋 សួស្តី! ខ្ញុំឃើញសាររបស់អ្នក – ខ្ញុំនឹងឆ្លើយតបវិញភ្លាមៗពេលទំនេរ។\n"
            "បើបន្ទាន់ សូមផ្ញើ 🔥 មក។"
        )

# ---------- Wholesale form handlers ----------
def handle_wholesale_step(chat_id, text, first_name, username):
    state = user_state[chat_id]
    step = state["step"]

    if step == "ask_name":
        state["name"] = text.strip()
        state["step"] = "ask_company"
        send_message(chat_id, "អរគុណ! តើឈ្មោះក្រុមហ៊ុនរបស់អ្នកជាអ្វី?")
    elif step == "ask_company":
        state["company"] = text.strip()
        state["step"] = "ask_quantity"
        send_message(chat_id, "តើអ្នកត្រូវការក្នុងបរិមាណប៉ុន្មានក្នុងមួយខែ?")
    elif step == "ask_quantity":
        state["quantity"] = text.strip()
        summary = (
            f"📦 *អតិថិជនបោះដុំថ្មី*\n"
            f"ឈ្មោះ: {state.get('name')}\n"
            f"ក្រុមហ៊ុន: {state.get('company')}\n"
            f"បរិមាណប៉ាន់ស្មាន: {state.get('quantity')}\n"
            f"លេខសម្គាល់: `{chat_id}`"
            f"{(' @' + username) if username else ''}"
        )
        send_message(OWNER_ID, summary, parse_mode="Markdown")
        send_message(chat_id, "✅ អរគុណ! សំណើរបស់អ្នកត្រូវបានបញ្ជូនទៅម្ចាស់ហាង។ ពួកគេនឹងទាក់ទងអ្នកឆាប់ៗនេះ។")
        del user_state[chat_id]

# ---------- Callback query handler (inline buttons) ----------
def handle_callback(callback):
    data = callback["data"]
    cb_id = callback["id"]
    msg = callback.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    user_info = callback.get("from", {})
    first_name = user_info.get("first_name", "អ្នក")

    # -------- Tutorial navigation --------
    if data.startswith("tutorial_"):
        if data == "tutorial_start":
            tutorial_step[chat_id] = 1
            step = 1
        elif data == "tutorial_close":
            tutorial_step.pop(chat_id, None)
            send_message(chat_id, "មេរៀនត្រូវបានបិទ។ អ្នកអាចចុចប៊ូតុងណាមួយខាងក្រោម។", reply_markup=main_keyboard())
            answer_callback(cb_id)
            return
        else:  # tutorial_<step>
            step = int(data.split("_")[1])
            tutorial_step[chat_id] = step

        text = TUTORIAL_TEXTS.get(step, "មិនមានមេរៀននេះទេ")
        send_message(chat_id, text, reply_markup=tutorial_nav_keyboard(step, MAX_TUTORIAL), parse_mode="Markdown")
        answer_callback(cb_id)
        return

    # -------- Wholesale start --------
    if data == "wholesale":
        user_state[chat_id] = {"step": "ask_name"}
        send_message(chat_id, "📋 តោះបង្កើតគណនីបោះដុំ។ សូមប្រាប់ឈ្មោះពេញរបស់អ្នក។")
        answer_callback(cb_id)
        return

    # -------- Human contact --------
    if data == "human":
        username = user_info.get("username", "")
        send_message(
            OWNER_ID,
            f"📩 *សំណើទាក់ទងផ្ទាល់ពី* {first_name}"
            f"{(' @' + username) if username else ''}\n"
            f"លេខសម្គាល់: `{chat_id}`",
            parse_mode="Markdown"
        )
        send_message(chat_id, "អរគុណ! ខ្ញុំបានជូនដំណឹងទៅម្ចាស់ហាង ហើយពួកគេនឹងទាក់ទងអ្នកផ្ទាល់ក្នុងពេលឆាប់ៗ។")
        answer_callback(cb_id)
        return

    # default fallback
    answer_callback(cb_id)

# ---------- Command handler (private, owner only) ----------
def handle_command(chat_id, text):
    if chat_id != OWNER_ID:
        return  # មិនអនុញ្ញាតឱ្យអ្នកដទៃប្រើពាក្យបញ្ជា
    parts = text.split()
    cmd = parts[0].lower()
    global CURRENT_MODE

    if cmd == "/mode" and len(parts) > 1:
        if parts[1] in ("business", "daily"):
            CURRENT_MODE = parts[1]
            send_message(chat_id, f"✅ បានប្តូររបៀបទៅ *{CURRENT_MODE}*", parse_mode="Markdown")
        else:
            send_message(chat_id, "សូមប្រើ /mode business ឬ /mode daily")

    elif cmd == "/myid":
        send_message(chat_id, f"Your chat ID: `{chat_id}`", parse_mode="Markdown")

    # អាចបន្ថែមពាក្យបញ្ជាផ្សេងទៀតនៅទីនេះ

# ---------- Webhook (main entry point) ----------
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    # 1) Callback query (inline button presses)
    if "callback_query" in data:
        handle_callback(data["callback_query"])
        return 'ok', 200

    # 2) Normal message (private chat)
    msg = data.get("message", {})
    if msg:
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "").strip()

        if text.startswith("/"):
            handle_command(chat_id, text)
        else:
            user = msg.get("from", {})
            process_message(chat_id, text,
                            user.get("first_name", "អ្នក"),
                            user.get("username"))
        return 'ok', 200

    # 3) Business message (Secretary Mode / Profile Automation)
    bmsg = data.get("business_message", {})
    if bmsg:
        chat_id = bmsg.get("chat", {}).get("id")
        text = bmsg.get("text", "").strip()

        # Business messages usually come from non-contacts, we process them like normal
        if not text.startswith("/"):
            user = bmsg.get("from", {})
            process_message(chat_id, text,
                            user.get("first_name", "អ្នក"),
                            user.get("username"))
        return 'ok', 200

    return 'ok', 200

@app.route('/')
def home():
    return 'Bot is running'