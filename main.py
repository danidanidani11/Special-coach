import telebot
from telebot import types
from flask import Flask, request
import json
import os
import random
from datetime import datetime

TOKEN = '7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc'
URL = 'https://special-coach.onrender.com'
CHANNEL_USERNAME = "@Specialcoach1"
ADMIN_ID = 5542927340

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

USERS_FILE = 'data/users.json'
PLAYERS_FILE = 'data/players.json'

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def is_member(chat_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, chat_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def send_force_join(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("عضو شدم ✅", callback_data='joined')
    btn2 = types.InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
    markup.add(btn2)
    markup.add(btn1)
    bot.send_message(chat_id, "برای استفاده از ربات ابتدا در کانال زیر عضو شو:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    users = load_users()

    if user_id in users:
        bot.send_message(message.chat.id, "شما قبلاً ثبت‌نام کرده‌اید.")
        show_main_menu(message.chat.id)
    else:
        if not is_member(message.chat.id):
            send_force_join(message.chat.id)
        else:
            users[user_id] = {}
            save_users(users)
            bot.send_message(message.chat.id, "نام تیم شما چیست؟")
            bot.register_next_step_handler(message, ask_contact)

def ask_contact(message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id]['team_name'] = message.text
    save_users(users)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("📱 ارسال شماره", request_contact=True)
    markup.add(btn)
    bot.send_message(message.chat.id, "شماره تماس خود را ارسال کنید:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if message.contact:
        user_id = str(message.from_user.id)
        users = load_users()
        users[user_id]['phone'] = message.contact.phone_number
        users[user_id]['coins'] = 0
        users[user_id]['gems'] = 0
        users[user_id]['players'] = ['player1', 'player2', 'player3', 'player4', 'player5']
        users[user_id]['tactic'] = {}
        users[user_id]['score'] = 0
        users[user_id]['match_history'] = []
        users[user_id]['registered_at'] = str(datetime.now())
        save_users(users)
        bot.send_message(message.chat.id, "ثبت‌نام با موفقیت انجام شد ✅", reply_markup=types.ReplyKeyboardRemove())
        show_main_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == 'joined')
def check_joined(call):
    if is_member(call.from_user.id):
        bot.send_message(call.from_user.id, "عضویت تایید شد ✅ حالا نام تیم را وارد کن:")
        user_id = str(call.from_user.id)
        users = load_users()
        users[user_id] = {}
        save_users(users)
        bot.register_next_step_handler(call.message, ask_contact)
    else:
        bot.answer_callback_query(call.id, "هنوز عضو نیستی ❌")

# ====== نمایش منو ======
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 فروشگاه بازیکن", "📋 ترکیب و تاکتیک")
    markup.row("🎮 بازی شبانه", "📄 گزارش بازی")
    markup.row("👛 کیف پول", "🎁 پاداش روزانه")
    markup.row("🏆 برترین‌ها")
    bot.send_message(chat_id, "به منوی اصلی خوش آمدی! یکی از گزینه‌ها رو انتخاب کن:", reply_markup=markup)

# ====== فروشگاه بازیکن ======
@bot.message_handler(func=lambda msg: msg.text == "🛒 فروشگاه بازیکن")
def show_shop(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        return

    with open(PLAYERS_FILE, 'r') as f:
        all_players = json.load(f)

    markup = types.InlineKeyboardMarkup()
    for p in all_players:
        name = p['name']
        price_gems = p['price_gems']
        price_coins = p['price_coins']
        btn = types.InlineKeyboardButton(
            f"{name} | 💎{price_gems} | 🪙{price_coins}",
            callback_data=f"buy_{name}"
        )
        markup.add(btn)

    bot.send_message(message.chat.id, "🏟️ بازیکنان در دسترس:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_player(call):
    player_name = call.data.split("_")[1]
    user_id = str(call.from_user.id)
    users = load_users()

    if user_id not in users:
        return

    with open(PLAYERS_FILE, 'r') as f:
        all_players = json.load(f)

    player = next((p for p in all_players if p['name'] == player_name), None)
    if not player:
        bot.answer_callback_query(call.id, "بازیکن پیدا نشد.")
        return

    if player_name in users[user_id]['players']:
        bot.answer_callback_query(call.id, "قبلاً این بازیکن را خریدی.")
        return

    if len(users[user_id]['players']) >= 8:
        bot.answer_callback_query(call.id, "حداکثر ۸ بازیکن می‌تونی داشته باشی.")
        return

    coins = users[user_id]['coins']
    gems = users[user_id]['gems']
    price_gems = player['price_gems']
    price_coins = player['price_coins']

    if gems >= price_gems:
        users[user_id]['gems'] -= price_gems
        users[user_id]['players'].append(player_name)
        save_users(users)
        bot.answer_callback_query(call.id, "خرید با جم انجام شد ✅")
    elif coins >= price_coins:
        users[user_id]['coins'] -= price_coins
        users[user_id]['players'].append(player_name)
        save_users(users)
        bot.answer_callback_query(call.id, "خرید با سکه انجام شد ✅")
    else:
        bot.answer_callback_query(call.id, "جم یا سکه کافی نداری ❌")

# ====== ترکیب و تاکتیک ======
@bot.message_handler(func=lambda msg: msg.text == "📋 ترکیب و تاکتیک")
def show_tactic_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📌 ترکیب", "🎯 تاکتیک", "🎮 سبک بازی")
    markup.row("🚧 تله آفساید", "🌀 پرسینگ")
    markup.row("🔙 بازگشت به منو")
    bot.send_message(message.chat.id, "یک بخش رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "📌 ترکیب")
def show_players(message):
    user_id = str(message.from_user.id)
    users = load_users()
    players = users[user_id].get('players', [])
    bot.send_message(message.chat.id, f"⚽ بازیکنان فعلی تیم:\n" + "\n".join(players))

@bot.message_handler(func=lambda msg: msg.text == "🎯 تاکتیک")
def set_tactic(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚔️ هجومی", "🛡 دفاعی", "⚖️ متعادل")
    bot.send_message(message.chat.id, "نوع تاکتیک رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["⚔️ هجومی", "🛡 دفاعی", "⚖️ متعادل"])
def save_tactic_type(message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id]['tactic']['style'] = message.text
    save_users(users)
    bot.send_message(message.chat.id, "تاکتیک ذخیره شد ✅")

@bot.message_handler(func=lambda msg: msg.text == "🎮 سبک بازی")
def set_playstyle(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🔁 پاسکاری", "🏃 بازی وینگر")
    bot.send_message(message.chat.id, "سبک بازی رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["🔁 پاسکاری", "🏃 بازی وینگر"])
def save_playstyle(message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id]['tactic']['playstyle'] = message.text
    save_users(users)
    bot.send_message(message.chat.id, "سبک بازی ذخیره شد ✅")

@bot.message_handler(func=lambda msg: msg.text == "🚧 تله آفساید")
def set_offside(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⛔️ بذار", "✅ نذار")
    bot.send_message(message.chat.id, "تله آفساید رو فعال می‌کنی؟", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["⛔️ بذار", "✅ نذار"])
def save_offside(message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id]['tactic']['offside'] = message.text
    save_users(users)
    bot.send_message(message.chat.id, "تله آفساید ثبت شد ✅")

@bot.message_handler(func=lambda msg: msg.text == "🌀 پرسینگ")
def set_pressing(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💯 پرس کامل", "➗ پرس ۵۰٪", "❌ بدون پرس")
    bot.send_message(message.chat.id, "میزان پرس رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["💯 پرس کامل", "➗ پرس ۵۰٪", "❌ بدون پرس"])
def save_pressing(message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id]['tactic']['pressing'] = message.text
    save_users(users)
    bot.send_message(message.chat.id, "پرس ذخیره شد ✅")

@bot.message_handler(func=lambda msg: msg.text == "🔙 بازگشت به منو")
def back_to_menu(message):
    show_main_menu(message.chat.id)

from threading import Timer
import schedule
import time

# ====== لیست شرکت‌کنندگان بازی شبانه ======
night_players = []

@bot.message_handler(func=lambda msg: msg.text == "🎮 بازی شبانه")
def register_for_match(message):
    user_id = str(message.from_user.id)
    if user_id not in night_players:
        night_players.append(user_id)
        bot.send_message(message.chat.id, "✅ در لیست بازی شبانه قرار گرفتی. ساعت ۲۲ بازی انجام میشه.")
    else:
        bot.send_message(message.chat.id, "⏳ شما قبلاً در لیست بازی امشب ثبت شدی.")

# ====== اجرای بازی شبانه (۲ نفره) ======
def simulate_match():
    global night_players
    users = load_users()
    random.shuffle(night_players)

    while len(night_players) >= 2:
        p1 = night_players.pop()
        p2 = night_players.pop()

        u1 = users[p1]
        u2 = users[p2]

        t1 = u1.get('tactic', {})
        t2 = u2.get('tactic', {})

        score1 = 0
        score2 = 0

        # بررسی تاکتیک و تاثیر
        if t1.get("style") == "⚔️ هجومی":
            score1 += 3
        if t2.get("style") == "⚔️ هجومی":
            score2 += 3

        if t1.get("playstyle") == "🔁 پاسکاری":
            score1 += 2
        if t2.get("playstyle") == "🔁 پاسکاری":
            score2 += 2

        if t1.get("offside") == "⛔️ بذار":
            score1 += 1
        if t2.get("offside") == "⛔️ بذار":
            score2 += 1

        if t1.get("pressing") == "💯 پرس کامل":
            score1 += 2
        elif t1.get("pressing") == "➗ پرس ۵۰٪":
            score1 += 1

        if t2.get("pressing") == "💯 پرس کامل":
            score2 += 2
        elif t2.get("pressing") == "➗ پرس ۵۰٪":
            score2 += 1

        # کمی شانس (برای جذابیت)
        score1 += random.randint(0, 3)
        score2 += random.randint(0, 3)

        result = ""
        if score1 > score2:
            result = f"برد با نتیجه {score1}-{score2}"
            u1["score"] += 20
            u1["coins"] += 100
            u2["score"] -= 10
            u2["coins"] += 20
        elif score2 > score1:
            result = f"باخت با نتیجه {score1}-{score2}"
            u2["score"] += 20
            u2["coins"] += 100
            u1["score"] -= 10
            u1["coins"] += 20
        else:
            result = f"مساوی {score1}-{score2}"
            u1["score"] += 5
            u2["score"] += 5
            u1["coins"] += 40
            u2["coins"] += 40

        u1['match_history'].append({'vs': p2, 'result': result})
        u2['match_history'].append({'vs': p1, 'result': result})

        bot.send_message(int(p1), f"📄 گزارش بازی:\n{result}")
        bot.send_message(int(p2), f"📄 گزارش بازی:\n{result}")

    save_users(users)
    night_players = []

# ====== گزارش بازی ======
@bot.message_handler(func=lambda msg: msg.text == "📄 گزارش بازی")
def match_report(message):
    user_id = str(message.from_user.id)
    users = load_users()
    history = users[user_id].get('match_history', [])
    if not history:
        bot.send_message(message.chat.id, "هنوز هیچ بازی‌ای انجام ندادی.")
    else:
        rep = "\n".join([f"در برابر {h['vs']} - {h['result']}" for h in history[-5:]])
        bot.send_message(message.chat.id, f"🧾 آخرین بازی‌ها:\n{rep}")

# ====== بخش برترین‌ها ======
@bot.message_handler(func=lambda msg: msg.text == "🏆 برترین‌ها")
def top_players(message):
    users = load_users()
    ranking = []
    for uid, data in users.items():
        total = len(data.get("match_history", []))
        wins = sum(1 for m in data.get("match_history", []) if "برد" in m['result'])
        percent = round((wins / total) * 100, 1) if total else 0
        ranking.append((data.get("team_name", "بی‌نام"), percent))
    ranking.sort(key=lambda x: x[1], reverse=True)
    top10 = ranking[:10]
    text = "\n".join([f"{i+1}- {name}: {score}% برد" for i, (name, score) in enumerate(top10)])
    bot.send_message(message.chat.id, f"🏆 تیم‌های برتر:\n{text}")

from datetime import date

# ====== کیف پول ======
@bot.message_handler(func=lambda msg: msg.text == "👛 کیف پول")
def show_wallet(message):
    user_id = str(message.from_user.id)
    users = load_users()
    data = users[user_id]
    coins = data.get("coins", 0)
    gems = data.get("gems", 0)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🔄 تبدیل سکه به جم", "💸 ارسال فیش پرداخت")
    markup.row("🔙 بازگشت به منو")

    bot.send_message(
        message.chat.id,
        f"📦 موجودی شما:\nسکه: {coins} 🪙\nجم: {gems} 💎\n\n💳 آدرس ترون:\nTJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb\n(هر ۱۰۰ سکه = ۱ جم = ۴ ترون)",
        reply_markup=markup
    )

# ====== تبدیل سکه به جم ======
@bot.message_handler(func=lambda msg: msg.text == "🔄 تبدیل سکه به جم")
def convert_coins(message):
    user_id = str(message.from_user.id)
    users = load_users()
    coins = users[user_id].get("coins", 0)

    if coins >= 100:
        users[user_id]["coins"] -= 100
        users[user_id]["gems"] += 1
        save_users(users)
        bot.send_message(message.chat.id, "✅ ۱ جم به شما اضافه شد و ۱۰۰ سکه کم شد.")
    else:
        bot.send_message(message.chat.id, "❌ سکه کافی نداری.")

# ====== ارسال فیش ======
@bot.message_handler(func=lambda msg: msg.text == "💸 ارسال فیش پرداخت")
def ask_receipt(message):
    bot.send_message(message.chat.id, "🧾 لطفاً عکس یا متن فیش پرداخت خود را ارسال کنید.")
    bot.register_next_step_handler(message, forward_receipt_to_admin)

def forward_receipt_to_admin(message):
    user_id = str(message.from_user.id)
    caption = f"🧾 فیش پرداخت از {user_id}\nبرای تایید، روی یکی از دکمه‌ها کلیک کن:"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{user_id}"))
    markup.add(types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}"))

    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
        bot.send_photo(ADMIN_ID, file_id, caption=caption, reply_markup=markup)
    else:
        bot.send_message(ADMIN_ID, f"{caption}\n\n{message.text}", reply_markup=markup)

    bot.send_message(message.chat.id, "✅ فیش شما ارسال شد. منتظر تایید ادمین باشید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def handle_receipt_action(call):
    target_id = call.data.split("_")[1]
    users = load_users()

    if call.data.startswith("approve_"):
        users[target_id]["coins"] += 100
        save_users(users)
        bot.send_message(int(target_id), "✅ فیش شما تایید شد. ۱۰۰ سکه اضافه شد.")
        bot.edit_message_text("✅ فیش تایید شد.", call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(int(target_id), "❌ فیش شما رد شد.")
        bot.edit_message_text("❌ فیش رد شد.", call.message.chat.id, call.message.message_id)

# ====== پاداش روزانه ======
@bot.message_handler(func=lambda msg: msg.text == "🎁 پاداش روزانه")
def daily_reward(message):
    user_id = str(message.from_user.id)
    users = load_users()
    today = str(date.today())

    if users[user_id].get("last_reward") == today:
        bot.send_message(message.chat.id, "❌ امروز پاداش را گرفته‌ای.")
    else:
        users[user_id]["last_reward"] = today
        users[user_id]["gems"] += 2
        save_users(users)
        bot.send_message(message.chat.id, "🎉 دو جم رایگان به شما تعلق گرفت!")

# ====== اجرای اتوماتیک بازی شبانه در ساعت ۲۲ ======
def schedule_nightly_game():
    schedule.every().day.at("22:00").do(simulate_match)
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)
    import threading
    threading.Thread(target=run_scheduler).start()

# ====== راه‌اندازی Flask Webhook ======
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running..."

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL}/{TOKEN}")
    schedule_nightly_game()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
