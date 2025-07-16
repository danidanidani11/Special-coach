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
            # بازیکنان ضعیف (1 جم)
            "p1": {"name": "حسین معطری", "overall": 55, "price_gems": 1, "price_coins": 100, "position": "FW"},
            "p2": {"name": "علی کریمی", "overall": 58, "price_gems": 1, "price_coins": 100, "position": "MF"},
            # ... 23 بازیکن ضعیف دیگر
            
            # بازیکنان متوسط (3-5 جم)
            "p26": {"name": "سردار آزمون", "overall": 75, "price_gems": 3, "price_coins": 300, "position": "FW"},
            "p27": {"name": "علیرضا جهانبخش", "overall": 74, "price_gems": 3, "price_coins": 300, "position": "MF"},
            # ... 15 بازیکن متوسط
            
            # بازیکنان قوی (8-10 جم)
            "p42": {"name": "لیونل مسی", "overall": 93, "price_gems": 10, "price_coins": 1000, "position": "FW"},
            "p43": {"name": "کریستیانو رونالدو", "overall": 92, "price_gems": 10, "price_coins": 1000, "position": "FW"},
            # ... 8 بازیکن قوی
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

# --- ثبت نام سه مرحله‌ای ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    if str(user_id) not in users_db:
        if not check_channel_membership(user_id):
            invite_keyboard = types.InlineKeyboardMarkup()
            invite_keyboard.add(types.InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
            invite_keyboard.add(types.InlineKeyboardButton("عضو شدم", callback_data="check_membership"))
            bot.send_message(user_id, f"⚠️ برای استفاده از ربات باید در کانال {CHANNEL_USERNAME} عضو شوید:", reply_markup=invite_keyboard)
            return
        
        bot.send_message(user_id, "🏟️ لطفا نام تیم خود را وارد کنید:")
        bot.register_next_step_handler(message, process_team_name)
    else:
        main_menu(user_id)

def process_team_name(message):
    user_id = message.from_user.id
    team_name = message.text
    
    users_db[str(user_id)] = {
        "team_name": team_name,
        "phone": None,
        "players": ["p1", "p2", "p3", "p4", "p5"],  # 5 بازیکن اولیه
        "coins": 1000,
        "gems": 10,
        "score": 1000,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "formation": "1-2-2",
        "tactic": "متعادل",
        "style": "پاسکاری",
        "offside": False,
        "pressing": "50%",
        "last_daily_reward": None,
        "night_game": False,
        "transactions": []
    }
    
    save_data()
    
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("اشتراک گذاری شماره 📱", request_contact=True))
    bot.send_message(user_id, "📞 لطفا شماره تماس خود را ارسال کنید یا دکمه زیر را فشار دهید:", reply_markup=markup)
    bot.register_next_step_handler(message, process_phone_number)

def process_phone_number(message):
    user_id = message.from_user.id
    
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text
    
    users_db[str(user_id)]["phone"] = phone
    save_data()
    
    bot.send_message(user_id, "✅ ثبت‌نام شما با موفقیت انجام شد!", reply_markup=types.ReplyKeyboardRemove())
    main_menu(user_id)

# --- منوی اصلی ---
def main_menu(user_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("⚽ ترکیب و تاکتیک", "🛒 فروشگاه بازیکن")
    keyboard.row("🎮 بازی شبانه", "📊 گزارش بازی")
    keyboard.row("👛 کیف پول", "🎁 پاداش روزانه")
    keyboard.row("🏆 برترین‌ها")
    bot.send_message(user_id, "منوی اصلی:", reply_markup=keyboard)

# --- فروشگاه بازیکن ---
@bot.message_handler(func=lambda m: m.text == "🛒 فروشگاه بازیکن")
def player_shop(message):
    user_id = message.from_user.id
    user_data = users_db[str(user_id)]
    
    if len(user_data["players"]) >= 8:
        bot.send_message(user_id, "⚠️ شما حداکثر بازیکن (8 نفر) را دارید!")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    for player_id, player in players_db.items():
        if player_id not in user_data["players"]:
            btn_text = f"{player['name']} ⭐{player['overall']}"
            callback_data = f"buy_{player_id}"
            
            if player["price_gems"] <= user_data["gems"] and player["price_coins"] <= user_data["coins"]:
                keyboard.add(types.InlineKeyboardButton(
                    f"{btn_text} (💎{player['price_gems']} 🪙{player['price_coins']})",
                    callback_data=callback_data
                ))
            else:
                keyboard.add(types.InlineKeyboardButton(
                    f"{btn_text} (ناکافی)",
                    callback_data="no_funds"
                ))
    
    bot.send_message(user_id, "🔍 لیست بازیکنان قابل خرید:", reply_markup=keyboard)

# --- ترکیب و تاکتیک ---
@bot.message_handler(func=lambda m: m.text == "⚽ ترکیب و تاکتیک")
def team_management(message):
    user_id = message.from_user.id
    keyboard = types.InlineKeyboardMarkup()
    
    keyboard.add(types.InlineKeyboardButton("🔀 تغییر ترکیب", callback_data="change_formation"))
    keyboard.add(types.InlineKeyboardButton("🎯 تغییر تاکتیک", callback_data="change_tactic"))
    keyboard.add(types.InlineKeyboardButton("🔄 تغییر سبک بازی", callback_data="change_style"))
    keyboard.add(types.InlineKeyboardButton("🚨 تله آفساید", callback_data="toggle_offside"))
    keyboard.add(types.InlineKeyboardButton("🏃‍♂️ تغییر پرسینگ", callback_data="change_pressing"))
    
    bot.send_message(user_id, "⚽ مدیریت ترکیب و تاکتیک:", reply_markup=keyboard)

# --- بازی شبانه ---
@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def night_game(message):
    user_id = message.from_user.id
    users_db[str(user_id)]["night_game"] = True
    save_data()
    bot.send_message(user_id, "✅ نام شما در لیست بازی‌های امشب ثبت شد. بازی‌ها ساعت 21:00 شروع می‌شوند.")

# --- گزارش بازی ---
@bot.message_handler(func=lambda m: m.text == "📊 گزارش بازی")
def match_report(message):
    user_id = message.from_user.id
    # نمایش آخرین بازی‌های کاربر
    # ...

# --- کیف پول ---
@bot.message_handler(func=lambda m: m.text == "👛 کیف پول")
def wallet(message):
    user_id = message.from_user.id
    user_data = users_db[str(user_id)]
    
    text = f"💰 کیف پول شما:\n\n"
    text += f"🪙 سکه: {user_data['coins']}\n"
    text += f"💎 جم: {user_data['gems']}\n\n"
    text += f"🔹 آدرس ترون: {TRON_ADDRESS}\n"
    text += f"🔸 نرخ تبدیل: هر 100 سکه = 1 جم = 4 ترون\n\n"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💸 تبدیل سکه به جم", callback_data="convert_coins"))
    keyboard.add(types.InlineKeyboardButton("📤 ارسال فیش واریزی", callback_data="send_receipt"))
    
    bot.send_message(user_id, text, reply_markup=keyboard)

# --- پاداش روزانه ---
@bot.message_handler(func=lambda m: m.text == "🎁 پاداش روزانه")
def daily_reward(message):
    user_id = message.from_user.id
    user_data = users_db[str(user_id)]
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user_data["last_daily_reward"] == today:
        bot.send_message(user_id, "⚠️ شما امروز پاداش خود را دریافت کرده‌اید!")
        return
    
    user_data["gems"] += 2
    user_data["last_daily_reward"] = today
    save_data()
    
    bot.send_message(user_id, "🎉 2 جم به عنوان پاداش روزانه به کیف پول شما اضافه شد!")

# --- برترین‌ها ---
@bot.message_handler(func=lambda m: m.text == "🏆 برترین‌ها")
def top_players(message):
    user_id = message.from_user.id
    
    # محاسبه درصد برد برای هر کاربر
    top_list = []
    for uid, data in users_db.items():
        total_games = data["wins"] + data["draws"] + data["losses"]
        if total_games > 0:
            win_rate = (data["wins"] / total_games) * 100
            top_list.append({
                "team": data["team_name"],
                "win_rate": win_rate,
                "score": data["score"]
            })
    
    # مرتب‌سازی بر اساس درصد برد
    top_list.sort(key=lambda x: (-x["win_rate"], -x["score"]))
    
    # نمایش 10 تیم برتر
    text = "🏆 10 تیم برتر:\n\n"
    for i, team in enumerate(top_list[:10], 1):
        text += f"{i}. {team['team']} - {team['win_rate']:.1f}% برد - ⭐{team['score']}\n"
    
    bot.send_message(user_id, text)

# --- مدیریت callback‌ها ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data
    
    if data == "check_membership":
        if check_channel_membership(user_id):
            bot.send_message(user_id, "🏟️ لطفا نام تیم خود را وارد کنید:")
            bot.register_next_step_handler(call.message, process_team_name)
        else:
            bot.answer_callback_query(call.id, "شما هنوز در کانال عضو نشده‌اید!", show_alert=True)
    
    elif data.startswith("buy_"):
        player_id = data[4:]
        buy_player(user_id, player_id)
    
    elif data == "change_formation":
        change_formation(user_id)
    
    # سایر callback‌ها...

# --- Webhook تنظیمات ---
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
