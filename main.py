import telebot
import json
import os
from flask import Flask, request

# ---------- تنظیمات ----------
TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "@Specialcoach1"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ---------- مدیریت دیتای کاربران ----------
def get_user(user_id):
    try:
        with open(f"users/{user_id}.json", "r") as f:
            return json.load(f)
    except:
        return None

def save_user(user_id, data):
    os.makedirs("users", exist_ok=True)
    with open(f"users/{user_id}.json", "w") as f:
        json.dump(data, f)

# ---------- استارت ----------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    # عضویت اجباری
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            bot.send_message(user_id, f"🔒 برای ادامه، عضو کانال {CHANNEL_USERNAME} شو و بعد /start بزن.")
            return
    except:
        bot.send_message(user_id, f"🔒 برای ادامه، عضو کانال {CHANNEL_USERNAME} شو و بعد /start بزن.")
        return

    user = get_user(user_id)
    if not user:
        bot.send_message(user_id, "⚽️ خوش اومدی به لیگ مربیان!\nاسم تیمت چیه؟")
        bot.register_next_step_handler(message, save_name)
    else:
        show_main_menu(user_id)

def save_name(message):
    user_id = message.from_user.id
    name = message.text

    user_data = {
        "name": name,
        "coins": 0,
        "gems": 0,
        "players": [],
        "tactic": "۴-۴-۲"
    }
    save_user(user_id, user_data)
    show_main_menu(user_id)

# ---------- منوی اصلی ----------
def show_main_menu(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎮 ترکیب و تاکتیک", "🛒 فروشگاه")
    markup.row("📋 لیست بازیکنان", "💰 کیف پول")
    bot.send_message(user_id, "🏠 منوی اصلی:", reply_markup=markup)

# ---------- تایید رسید سکه توسط ادمین ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_receipt:"))
def confirm_receipt(call):
    try:
        parts = call.data.split(":")
        user_id = int(parts[1])
        admin_id = int(parts[2])
        amount = int(parts[3])

        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ فقط ادمین می‌تونه تایید کنه.")
            return

        user = get_user(user_id)
        if not user:
            bot.answer_callback_query(call.id, "❌ کاربر پیدا نشد.")
            return

        user['coins'] = user.get('coins', 0) + amount
        save_user(user_id, user)

        bot.answer_callback_query(call.id, "✅ تایید شد.")
        bot.send_message(user_id, f"✅ {amount} سکه به حسابت اضافه شد.")
        bot.edit_message_text("✅ رسید تایید شد و سکه اضافه شد.", call.message.chat.id, call.message.message_id)

    except Exception as e:
        print("❌ خطا در confirm_receipt:", e)
        bot.answer_callback_query(call.id, "❌ خطا در تایید رسید.")

# ---------- روت‌ها برای Render ----------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "🏃‍♂️ Bot is running!"

# ---------- اجرای برنامه ----------
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
