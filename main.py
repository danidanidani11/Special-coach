import telebot
from telebot import types
import json
import os
from flask import Flask, request
import random
import datetime
import threading

# تنظیمات اولیه
TOKEN = '7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

ADMIN_ID = 5542927340
CHANNEL_USERNAME = "Specialcoach1"

# مسیر فایل‌ها
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")

# ایجاد پوشه داده اگر وجود نداشته باشد
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# توابع مدیریت داده
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_players():
    if os.path.exists(PLAYERS_FILE):
        with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# بارگذاری داده‌ها
users = load_users()
players = load_players()

# اختصاص بازیکنان اولیه
def assign_starting_players(user_id):
    starting_players = [p["id"] for p in players if p.get("is_starting", False)]
    if str(user_id) in users:
        users[str(user_id)]["team_players"] = starting_players
        save_users()

# منوها
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚽ ترکیب و تاکتیک", "🛒 فروشگاه بازیکن")
    markup.row("🎮 بازی شبانه", "🏆 برترین‌ها")
    markup.row("👛 کیف پول", "🎁 پاداش روزانه")
    return markup

def back_to_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بازگشت به منو")
    return markup

# هندلرهای ثبت‌نام
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = str(msg.from_user.id)
    
    # بررسی عضویت در کانال
    try:
        chat_member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", msg.from_user.id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}"))
            markup.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_sub"))
            bot.send_message(msg.chat.id, "🔒 برای استفاده از ربات، ابتدا در کانال عضو شوید:", reply_markup=markup)
            return
    except Exception as e:
        bot.send_message(msg.chat.id, "⚠️ خطا در بررسی عضویت. لطفا بعدا تلاش کنید.")
        return
    
    # اگر کاربر ثبت‌نام کرده
    if user_id in users and users[user_id].get("registered"):
        bot.send_message(msg.chat.id, "👋 خوش آمدید!", reply_markup=main_menu())
        return
    
    # شروع ثبت‌نام جدید
    users[user_id] = {
        "step": "ask_team",
        "registered": False,
        "wallet": {"coins": 100, "gems": 5},
        "score": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0
    }
    save_users()
    bot.send_message(msg.chat.id, "🏟 لطفا نام تیم خود را وارد کنید:")

@bot.message_handler(func=lambda m: users.get(str(m.from_user.id), {}).get("step") == "ask_team")
def ask_team(msg):
    user_id = str(msg.from_user.id)
    team_name = msg.text.strip()
    
    if len(team_name) < 3:
        bot.send_message(msg.chat.id, "❌ نام تیم باید حداقل ۳ کاراکتر باشد.")
        return
    
    users[user_id]["team_name"] = team_name
    users[user_id]["step"] = "ask_contact"
    save_users()
    
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("ارسال شماره تماس", request_contact=True))
    bot.send_message(msg.chat.id, "📱 لطفا شماره تماس خود را ارسال کنید:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(msg):
    user_id = str(msg.from_user.id)
    if users.get(user_id, {}).get("step") != "ask_contact":
        return
    
    if not msg.contact or msg.contact.user_id != msg.from_user.id:
        bot.send_message(msg.chat.id, "⚠️ لطفا شماره تماس خود را ارسال کنید.")
        return
    
    users[user_id]["phone"] = msg.contact.phone_number
    users[user_id]["registered"] = True
    users[user_id]["step"] = None
    assign_starting_players(user_id)
    save_users()
    
    bot.send_message(msg.chat.id, f"✅ ثبت‌نام شما با موفقیت انجام شد!\n\nبه تیم {users[user_id]['team_name']} خوش آمدید!", reply_markup=main_menu())

# بخش فروشگاه بازیکن
@bot.message_handler(func=lambda m: m.text == "🛒 فروشگاه بازیکن")
def player_store(msg):
    user_id = str(msg.from_user.id)
    if user_id not in users or not users[user_id].get("registered"):
        bot.send_message(msg.chat.id, "❌ لطفا ابتدا ثبت‌نام کنید.")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    text = "🛒 فروشگاه بازیکنان:\n\n"
    
    for player in players:
        owned = "✅ (دارید)" if player["id"] in users[user_id].get("team_players", []) else ""
        text += f"⚽ {player['name']} ({player['position']})\n"
        text += f"🏷 قدرت: {player['overall']} | قیمت: {player['price_gems']} جم یا {player['price_coins']} سکه {owned}\n\n"
        markup.add(f"خرید {player['name']}")
    
    markup.add("بازگشت به منو")
    bot.send_message(msg.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text.startswith("خرید "))
def buy_player(msg):
    user_id = str(msg.from_user.id)
    if user_id not in users or not users[user_id].get("registered"):
        bot.send_message(msg.chat.id, "❌ لطفا ابتدا ثبت‌نام کنید.")
        return
    
    player_name = msg.text.replace("خرید ", "").strip()
    player = next((p for p in players if p["name"] == player_name), None)
    
    if not player:
        bot.send_message(msg.chat.id, "❌ بازیکن مورد نظر یافت نشد.")
        return
    
    if player["id"] in users[user_id].get("team_players", []):
        bot.send_message(msg.chat.id, "⚠️ شما قبلا این بازیکن را خریداری کرده‌اید.")
        return
    
    if len(users[user_id].get("team_players", [])) >= 8:
        bot.send_message(msg.chat.id, "❌ شما حداکثر تعداد بازیکن (۸ نفر) را دارید.")
        return
    
    wallet = users[user_id]["wallet"]
    
    # بررسی موجودی
    if wallet["gems"] >= player["price_gems"]:
        wallet["gems"] -= player["price_gems"]
        payment_method = "جم"
    elif wallet["coins"] >= player["price_coins"]:
        wallet["coins"] -= player["price_coins"]
        payment_method = "سکه"
    else:
        bot.send_message(msg.chat.id, "❌ موجودی کافی ندارید.")
        return
    
    # اضافه کردن بازیکن به تیم
    if "team_players" not in users[user_id]:
        users[user_id]["team_players"] = []
    
    users[user_id]["team_players"].append(player["id"])
    users[user_id]["wallet"] = wallet
    save_users()
    
    bot.send_message(msg.chat.id, f"✅ بازیکن {player['name']} با موفقیت خریداری شد! (پرداخت با {payment_method})", reply_markup=back_to_menu())

# بقیه بخش‌های ربات (کیف پول، بازی شبانه، ...) مانند کد قبلی

if __name__ == "__main__":
    # برای اجرا در Render
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
