import os
import json
import random
from datetime import datetime, timedelta
import telebot
from telebot import types
from flask import Flask, request

# تنظیمات اولیه
TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "@Specialcoach1"
TRON_ADDRESS = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"
WEBHOOK_URL = "https://special-coach.onrender.com"

# ایجاد نمونه ربات و Flask
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# مسیر فایل‌های داده
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")

# ایجاد پوشه داده اگر وجود ندارد
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# بارگذاری یا ایجاد فایل‌های داده
def load_data():
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = {}
    
    try:
        with open(PLAYERS_FILE, 'r') as f:
            players = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        players = {
            "player1": {"name": "بازیکن 1", "overall": 50, "price_gems": 0, "price_coins": 0, "position": "FW"},
            "player2": {"name": "بازیکن 2", "overall": 50, "price_gems": 0, "price_coins": 0, "position": "MF"},
            "player3": {"name": "بازیکن 3", "overall": 50, "price_gems": 0, "price_coins": 0, "position": "DF"},
            "player4": {"name": "بازیکن 4", "overall": 50, "price_gems": 0, "price_coins": 0, "position": "MF"},
            "player5": {"name": "بازیکن 5", "overall": 50, "price_gems": 0, "price_coins": 0, "position": "GK"},
            "messi": {"name": "لیونل مسی", "overall": 93, "price_gems": 5, "price_coins": 500, "position": "FW"},
            "ronaldo": {"name": "کریستیانو رونالدو", "overall": 92, "price_gems": 5, "price_coins": 500, "position": "FW"},
            # ... سایر بازیکنان
        }
    
    return users, players

users_db, players_db = load_data()

# ذخیره داده‌ها
def save_data():
    with open(USERS_FILE, 'w') as f:
        json.dump(users_db, f, indent=4)
    with open(PLAYERS_FILE, 'w') as f:
        json.dump(players_db, f, indent=4)

# بررسی عضویت در کانال
def check_channel_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# منوی اصلی
def main_menu(user_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("⚽ ترکیب و تاکتیک", "🛒 فروشگاه بازیکن")
    keyboard.row("🎮 بازی شبانه", "📄 گزارش بازی")
    keyboard.row("👛 کیف پول", "🎁 پاداش روزانه")
    keyboard.row("🏆 برترین‌ها")
    bot.send_message(user_id, "منوی اصلی:", reply_markup=keyboard)

# دستور شروع
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    if str(user_id) not in users_db:
        if not check_channel_membership(user_id):
            invite_keyboard = types.InlineKeyboardMarkup()
            invite_keyboard.add(types.InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
            invite_keyboard.add(types.InlineKeyboardButton("عضو شدم", callback_data="check_membership"))
            bot.send_message(user_id, f"برای استفاده از ربات باید در کانال {CHANNEL_USERNAME} عضو شوید:", reply_markup=invite_keyboard)
            return
        
        bot.send_message(user_id, "لطفا نام تیم خود را وارد کنید:")
        bot.register_next_step_handler(message, process_team_name)
    else:
        main_menu(user_id)

def process_team_name(message):
    user_id = message.from_user.id
    team_name = message.text
    
    users_db[str(user_id)] = {
        "team_name": team_name,
        "phone": None,
        "players": ["player1", "player2", "player3", "player4", "player5"],
        "coins": 1000,
        "gems": 10,
        "score": 1000,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "last_daily_reward": None,
        "night_game": False,
        "transactions": []
    }
    
    save_data()
    
    bot.send_message(user_id, "لطفا شماره تماس خود را ارسال کنید یا از دکمه اشتراک گذاری شماره استفاده کنید:", 
                     reply_markup=types.ReplyKeyboardMarkup(
                         [[types.KeyboardButton("اشتراک گذاری شماره", request_contact=True)]],
                         resize_keyboard=True
                     ))
    bot.register_next_step_handler(message, process_phone_number)

def process_phone_number(message):
    user_id = message.from_user.id
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text
    
    users_db[str(user_id)]["phone"] = phone
    save_data()
    
    bot.send_message(user_id, "ثبت‌نام شما با موفقیت انجام شد! 5 بازیکن اولیه به تیم شما اضافه شدند.")
    main_menu(user_id)

# مدیریت callback
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == "check_membership":
        if check_channel_membership(user_id):
            bot.send_message(user_id, "لطفا نام تیم خود را وارد کنید:")
            bot.register_next_step_handler(call.message, process_team_name)
        else:
            bot.answer_callback_query(call.id, "شما هنوز در کانال عضو نشده‌اید!", show_alert=True)
    
    # سایر callback ها...

# دستورات منو
@bot.message_handler(func=lambda message: message.text == "🛒 فروشگاه بازیکن")
def player_shop(message):
    user_id = message.from_user.id
    keyboard = types.InlineKeyboardMarkup()
    
    for player_id, player in players_db.items():
        if player_id not in users_db[str(user_id)]["players"]:
            btn_text = f"{player['name']} ({player['position']}) - ⭐{player['overall']} - 🪙{player['price_coins']} - 💎{player['price_gems']}"
            keyboard.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{player_id}"))
    
    bot.send_message(user_id, "لیست بازیکنان قابل خرید:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "⚽ ترکیب و تاکتیک")
def team_formation(message):
    user_id = message.from_user.id
    user_data = users_db[str(user_id)]
    
    # گروه‌بندی بازیکنان بر اساس پست
    positions = {"GK": [], "DF": [], "MF": [], "FW": []}
    for player_id in user_data["players"]:
        player = players_db[player_id]
        positions[player["position"]].append(player["name"])
    
    # ایجاد شماتیک
    formation = f"⚽ ترکیب تیم {user_data['team_name']}:\n\n"
    formation += "          " + "     ".join(positions["FW"]) + "\n"
    formation += "    " + "     ".join(positions["MF"]) + "\n"
    formation += "          " + "     ".join(positions["DF"]) + "\n"
    formation += "               " + "     ".join(positions["GK"])
    
    bot.send_message(user_id, formation)

# سایر دستورات...

# Webhook تنظیمات
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Invalid content type', 403

@app.route('/')
def index():
    return 'Bot is running!'

if __name__ == '__main__':
    # تنظیم webhook
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + '/' + TOKEN)
    
    # اجرای Flask
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
