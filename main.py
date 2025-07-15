import telebot
from telebot import types
import json
import os
import random
import datetime
import threading
from flask import Flask, request

# تنظیمات اولیه
TOKEN = '7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# تنظیمات ادمین و کانال
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "Specialcoach1"

# مسیر فایل‌های داده
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")

# ایجاد فایل‌های اولیه اگر وجود ندارند
def init_data_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    
    if not os.path.exists(PLAYERS_FILE):
        # بازیکنان اولیه (5 بازیکن ضعیف)
        starting_players = [
            {"id": 1, "name": "بازیکن 1", "position": "FW", "overall": 50, "price_coins": 100, "price_gems": 1},
            {"id": 2, "name": "بازیکن 2", "position": "MF", "overall": 45, "price_coins": 90, "price_gems": 1},
            {"id": 3, "name": "بازیکن 3", "position": "DF", "overall": 40, "price_coins": 80, "price_gems": 1},
            {"id": 4, "name": "بازیکن 4", "position": "DF", "overall": 42, "price_coins": 85, "price_gems": 1},
            {"id": 5, "name": "بازیکن 5", "position": "GK", "overall": 38, "price_coins": 70, "price_gems": 1}
        ]
        with open(PLAYERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(starting_players, f, ensure_ascii=False, indent=2)

init_data_files()

# توابع مدیریت داده
def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def load_players():
    with open(PLAYERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# بارگذاری داده‌ها
users = load_users()
players = load_players()

# سیستم بازی شبانه
night_game_participants = set()
night_game_results = {}

# منوها
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚽ ترکیب تیم", "🛒 فروشگاه بازیکن")
    markup.row("🎮 بازی شبانه", "🏆 جدول لیگ")
    markup.row("👛 کیف پول", "🎁 پاداش روزانه")
    return markup

def back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔙 بازگشت به منو")
    return markup

# مدیریت ثبت‌نام
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    
    # بررسی عضویت در کانال
    try:
        chat_member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", message.from_user.id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}"))
            markup.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_sub"))
            bot.send_message(message.chat.id, "برای استفاده از ربات، ابتدا در کانال عضو شوید:", reply_markup=markup)
            return
    except Exception as e:
        bot.send_message(message.chat.id, "خطا در بررسی عضویت. لطفا بعدا تلاش کنید.")
        return
    
    # اگر کاربر ثبت‌نام کرده
    if user_id in users and users[user_id].get('registered'):
        bot.send_message(message.chat.id, f"سلام {users[user_id]['team_name']}! خوش آمدید.", reply_markup=main_menu())
        return
    
    # شروع ثبت‌نام جدید
    users[user_id] = {
        'step': 'get_team_name',
        'registered': False,
        'wallet': {'coins': 100, 'gems': 5},
        'score': 0,
        'wins': 0,
        'losses': 0,
        'draws': 0
    }
    save_users(users)
    bot.send_message(message.chat.id, "لطفا نام تیم خود را وارد کنید:")

@bot.message_handler(func=lambda m: users.get(str(m.from_user.id), {}).get('step') == 'get_team_name')
def get_team_name(message):
    user_id = str(message.from_user.id)
    team_name = message.text.strip()
    
    if len(team_name) < 3:
        bot.send_message(message.chat.id, "نام تیم باید حداقل 3 کاراکتر باشد.")
        return
    
    users[user_id]['team_name'] = team_name
    users[user_id]['step'] = 'get_phone'
    save_users(users)
    
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("ارسال شماره تماس", request_contact=True))
    bot.send_message(message.chat.id, "لطفا شماره تماس خود را ارسال کنید:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    user_id = str(message.from_user.id)
    
    if users.get(user_id, {}).get('step') != 'get_phone':
        return
    
    if not message.contact or message.contact.user_id != message.from_user.id:
        bot.send_message(message.chat.id, "لطفا شماره تماس خود را ارسال کنید.")
        return
    
    users[user_id]['phone'] = message.contact.phone_number
    users[user_id]['registered'] = True
    users[user_id]['step'] = None
    users[user_id]['team_players'] = [1, 2, 3, 4, 5]  # اضافه کردن بازیکنان اولیه
    save_users(users)
    
    bot.send_message(message.chat.id, 
                    f"✅ ثبت‌نام شما با موفقیت انجام شد!\n\n"
                    f"نام تیم: {users[user_id]['team_name']}\n"
                    f"5 بازیکن اولیه به تیم شما اضافه شدند.", 
                    reply_markup=main_menu())

# بخش فروشگاه بازیکن
@bot.message_handler(func=lambda m: m.text == "🛒 فروشگاه بازیکن")
def player_store(message):
    user_id = str(message.from_user.id)
    
    if user_id not in users or not users[user_id].get('registered'):
        bot.send_message(message.chat.id, "لطفا ابتدا ثبت‌نام کنید.")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    text = "🛒 لیست بازیکنان قابل خرید:\n\n"
    
    for player in players:
        owned = "✅ (دارید)" if player['id'] in users[user_id].get('team_players', []) else ""
        text += (f"⚽ {player['name']} ({player['position']})\n"
                f"قدرت: {player['overall']} | قیمت: {player['price_gems']} جم یا {player['price_coins']} سکه {owned}\n\n")
        markup.add(f"خرید {player['name']}")
    
    markup.add("🔙 بازگشت به منو")
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text.startswith("خرید "))
def buy_player(message):
    user_id = str(message.from_user.id)
    
    if user_id not in users or not users[user_id].get('registered'):
        bot.send_message(message.chat.id, "لطفا ابتدا ثبت‌نام کنید.")
        return
    
    player_name = message.text.replace("خرید ", "").strip()
    player = next((p for p in players if p['name'] == player_name), None)
    
    if not player:
        bot.send_message(message.chat.id, "بازیکن مورد نظر یافت نشد.")
        return
    
    if player['id'] in users[user_id].get('team_players', []):
        bot.send_message(message.chat.id, "شما قبلا این بازیکن را خریداری کرده‌اید.")
        return
    
    if len(users[user_id].get('team_players', [])) >= 8:
        bot.send_message(message.chat.id, "حداکثر تعداد بازیکن در تیم 8 نفر است.")
        return
    
    wallet = users[user_id]['wallet']
    
    # بررسی موجودی
    if wallet['gems'] >= player['price_gems']:
        wallet['gems'] -= player['price_gems']
        payment = f"{player['price_gems']} جم"
    elif wallet['coins'] >= player['price_coins']:
        wallet['coins'] -= player['price_coins']
        payment = f"{player['price_coins']} سکه"
    else:
        bot.send_message(message.chat.id, "موجودی کافی ندارید.")
        return
    
    # اضافه کردن بازیکن به تیم
    users[user_id]['team_players'].append(player['id'])
    save_users(users)
    
    bot.send_message(message.chat.id, 
                    f"✅ بازیکن {player['name']} با موفقیت خریداری شد!\n"
                    f"پرداخت شده: {payment}", 
                    reply_markup=back_menu())

# بقیه بخش‌های ربات (کیف پول، بازی شبانه، ترکیب تیم و ...)

if __name__ == '__main__':
    # تنظیم وب‌هوک برای اجرا در Render
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
