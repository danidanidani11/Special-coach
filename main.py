import os
import json
import random
from datetime import datetime, timedelta
import telebot
from telebot import types
from flask import Flask, request
import threading
import time

# تنظیمات اولیه
TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "@Specialcoach1"
TRON_ADDRESS = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"
WEBHOOK_URL = "https://special-coach.onrender.com"
GAME_TIME = "10:30"  # زمان بازی روزانه

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
        "matches": [],
        "formation": "1-2-2",
        "tactic": "متعادل",
        "style": "پاسکاری",
        "offside": False,
        "pressing": "50%",
        "last_daily_reward": None,
        "in_game": False,
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
    if str(user_id) not in users_db:
        start(bot.send_message(user_id, "لطفا ابتدا ثبت‌نام کنید!"))
        return
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("⚽ ترکیب و تاکتیک", "🛒 فروشگاه بازیکن")
    keyboard.row("🎮 بازی روزانه", "📊 گزارش بازی")
    keyboard.row("👛 کیف پول", "🎁 پاداش روزانه")
    keyboard.row("🏆 برترین‌ها")
    bot.send_message(user_id, "منوی اصلی:", reply_markup=keyboard)

# --- فروشگاه بازیکن ---
@bot.message_handler(func=lambda m: m.text == "🛒 فروشگاه بازیکن" and str(m.from_user.id) in users_db)
def player_shop(message):
    user_id = message.from_user.id
    user_data = users_db[str(user_id)]
    
    if len(user_data["players"]) >= 8:
        bot.send_message(user_id, "⚠️ شما حداکثر بازیکن (8 نفر) را دارید!")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    for player_id, player in players_db.items():
        if player_id not in user_data["players"]:
            btn_text = f"{player['name']} ({player['position']}) ⭐{player['overall']}"
            callback_data = f"buy_{player_id}"
            
            if player["price_gems"] <= user_data["gems"] and player["price_coins"] <= user_data["coins"]:
                keyboard.add(types.InlineKeyboardButton(
                    f"{btn_text} - 💎{player['price_gems']} 🪙{player['price_coins']}",
                    callback_data=callback_data
                ))
            else:
                keyboard.add(types.InlineKeyboardButton(
                    f"{btn_text} - موجودی ناکافی",
                    callback_data="no_funds"
                ))
    
    bot.send_message(user_id, "🔍 لیست بازیکنان قابل خرید:", reply_markup=keyboard)

# --- ترکیب و تاکتیک ---
@bot.message_handler(func=lambda m: m.text == "⚽ ترکیب و تاکتیک" and str(m.from_user.id) in users_db)
def team_management(message):
    user_id = message.from_user.id
    user_data = users_db[str(user_id)]
    
    text = f"⚽ تنظیمات تیم {user_data['team_name']}:\n\n"
    text += f"🔹 ترکیب: {user_data['formation']}\n"
    text += f"🔸 تاکتیک: {user_data['tactic']}\n"
    text += f"🔹 سبک بازی: {user_data['style']}\n"
    text += f"🔸 تله آفساید: {'فعال' if user_data['offside'] else 'غیرفعال'}\n"
    text += f"🔹 پرسینگ: {user_data['pressing']}"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("تغییر ترکیب", callback_data="change_formation"),
        types.InlineKeyboardButton("تغییر تاکتیک", callback_data="change_tactic")
    )
    keyboard.row(
        types.InlineKeyboardButton("تغییر سبک بازی", callback_data="change_style"),
        types.InlineKeyboardButton("تغییر پرسینگ", callback_data="change_pressing")
    )
    keyboard.add(types.InlineKeyboardButton(
        f"تله آفساید: {'✅' if user_data['offside'] else '❌'}", 
        callback_data="toggle_offside"
    ))
    
    bot.send_message(user_id, text, reply_markup=keyboard)

# --- بازی روزانه ---
@bot.message_handler(func=lambda m: m.text == "🎮 بازی روزانه" and str(m.from_user.id) in users_db)
def daily_game(message):
    user_id = message.from_user.id
    users_db[str(user_id)]["in_game"] = True
    save_data()
    
    now = datetime.now().strftime("%H:%M")
    if now >= GAME_TIME:
        bot.send_message(user_id, "⏳ بازی امروز به زودی شروع می‌شود...")
    else:
        bot.send_message(user_id, f"✅ نام شما در لیست بازی‌های امروز ثبت شد. بازی‌ها ساعت {GAME_TIME} شروع می‌شوند.")

# --- گزارش بازی ---
@bot.message_handler(func=lambda m: m.text == "📊 گزارش بازی" and str(m.from_user.id) in users_db)
def match_report(message):
    user_id = message.from_user.id
    user_data = users_db[str(user_id)]
    
    if not user_data["matches"]:
        bot.send_message(user_id, "هنوز هیچ بازی انجام نداده‌اید!")
        return
    
    text = "📊 گزارش بازی‌های شما:\n\n"
    for i, match in enumerate(user_data["matches"][-5:], 1):  # نمایش 5 بازی آخر
        result = "✅ برنده" if match["result"] == "win" else "🔶 مساوی" if match["result"] == "draw" else "❌ بازنده"
        text += f"🎮 بازی {i}:\n"
        text += f"🆚 حریف: {match['opponent']}\n"
        text += f"🏆 نتیجه: {result}\n"
        text += f"📊 نتیجه نهایی: {match['score']}\n"
        text += f"⏰ تاریخ: {match['date']}\n\n"
    
    bot.send_message(user_id, text)

# --- سایر بخش‌ها (کیف پول، پاداش روزانه، برترین‌ها) ---
# ... (کدهای قبلی بدون تغییر)

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
    
    elif data == "change_tactic":
        change_tactic(user_id)
    
    elif data == "change_style":
        change_style(user_id)
    
    elif data == "change_pressing":
        change_pressing(user_id)
    
    elif data == "toggle_offside":
        toggle_offside(user_id)
    
    elif data == "no_funds":
        bot.answer_callback_query(call.id, "موجودی شما برای خرید این بازیکن کافی نیست!", show_alert=True)

# --- توابع کمکی ---
def buy_player(user_id, player_id):
    user_data = users_db[str(user_id)]
    player = players_db[player_id]
    
    if player_id in user_data["players"]:
        bot.answer_callback_query(user_id, "این بازیکن را قبلا خریده‌اید!", show_alert=True)
        return
    
    if len(user_data["players"]) >= 8:
        bot.answer_callback_query(user_id, "حداکثر تعداد بازیکن (8 نفر) را دارید!", show_alert=True)
        return
    
    if user_data["gems"] < player["price_gems"] or user_data["coins"] < player["price_coins"]:
        bot.answer_callback_query(user_id, "موجودی شما کافی نیست!", show_alert=True)
        return
    
    user_data["gems"] -= player["price_gems"]
    user_data["coins"] -= player["price_coins"]
    user_data["players"].append(player_id)
    save_data()
    
    bot.send_message(user_id, f"✅ بازیکن {player['name']} با موفقیت خریداری شد!")
    player_shop(bot.send_message(user_id, "🛒 فروشگاه بازیکن"))

def change_formation(user_id):
    keyboard = types.InlineKeyboardMarkup()
    formations = ["1-2-2", "1-1-3", "1-3-1", "1-4", "2-2-1"]
    
    for formation in formations:
        keyboard.add(types.InlineKeyboardButton(
            formation,
            callback_data=f"set_formation_{formation}"
        ))
    
    bot.send_message(user_id, "🔀 لطفا ترکیب مورد نظر خود را انتخاب کنید:", reply_markup=keyboard)

# ... (توابع مشابه برای تغییر تاکتیک، سبک بازی، پرسینگ)

def toggle_offside(user_id):
    user_data = users_db[str(user_id)]
    user_data["offside"] = not user_data["offside"]
    save_data()
    
    team_management(bot.send_message(user_id, f"تله آفساید {'فعال' if user_data['offside'] else 'غیرفعال'} شد!"))

# --- سیستم بازی روزانه ---
def daily_game_scheduler():
    while True:
        now = datetime.now().strftime("%H:%M")
        if now == GAME_TIME:
            play_daily_matches()
        time.sleep(60)

def play_daily_matches():
    participants = [uid for uid, data in users_db.items() if data.get("in_game", False)]
    random.shuffle(participants)
    
    for i in range(0, len(participants)-1, 2):
        player1 = participants[i]
        player2 = participants[i+1]
        
        # شبیه‌سازی بازی بر اساس تاکتیک‌ها و ترکیب
        result = simulate_match(player1, player2)
        
        # ارسال نتایج به بازیکنان
        send_match_result(player1, player2, result)
        send_match_result(player2, player1, result)
        
        # ریست وضعیت بازی
        users_db[player1]["in_game"] = False
        users_db[player2]["in_game"] = False
    
    save_data()

def simulate_match(player1_id, player2_id):
    # الگوریتم پیشرفته شبیه‌سازی بازی بر اساس تاکتیک‌ها
    p1_data = users_db[player1_id]
    p2_data = users_db[player2_id]
    
    # محاسبه امتیاز بر اساس ترکیب، تاکتیک و بازیکنان
    p1_score = calculate_team_score(p1_data)
    p2_score = calculate_team_score(p2_data)
    
    # کمی رندوم برای هیجان
    p1_score += random.randint(-10, 10)
    p2_score += random.randint(-10, 10)
    
    if p1_score > p2_score:
        return {"winner": player1_id, "loser": player2_id, "draw": False}
    elif p1_score < p2_score:
        return {"winner": player2_id, "loser": player1_id, "draw": False}
    else:
        return {"winner": None, "loser": None, "draw": True}

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
    # شروع زمان‌بندی بازی‌های روزانه
    scheduler_thread = threading.Thread(target=daily_game_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # تنظیم webhook
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + '/' + TOKEN)
    
    # اجرای Flask
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
