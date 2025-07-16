import telebot
from telebot import types
from flask import Flask, request
import json
import os
import random
import time
import threading
import datetime
from datetime import date

bot.set_webhook(url=WEBHOOK_URL)

TOKEN = '7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc'
URL = 'https://special-coach.onrender.com'
CHANNEL_USERNAME = "@Specialcoach1"
ADMIN_ID = 5542927340
TRON_ADDRESS = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

USERS_FILE = 'data/users.json'
PLAYERS_FILE = 'data/players.json'
night_players = []

# ---------- Helper functions ----------
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
    markup.add(types.InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
    markup.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="joined"))
    bot.send_message(chat_id, "اول در کانال زیر عضو شو بعد ادامه بده:", reply_markup=markup)

# ---------- Start & Register ----------
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

@bot.callback_query_handler(func=lambda call: call.data == "joined")
def joined(call):
    if is_member(call.from_user.id):
        bot.send_message(call.message.chat.id, "نام تیم خود را وارد کنید:")
        user_id = str(call.from_user.id)
        users = load_users()
        users[user_id] = {}
        save_users(users)
        bot.register_next_step_handler(call.message, ask_contact)
    else:
        bot.answer_callback_query(call.id, "عضویت هنوز تایید نشده ❌")

def ask_contact(message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id]['team_name'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 ارسال شماره", request_contact=True))
    bot.send_message(message.chat.id, "لطفاً شماره‌ت رو ارسال کن:", reply_markup=markup)
    save_users(users)

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
        users[user_id]['last_reward'] = ""
        save_users(users)
        bot.send_message(message.chat.id, "ثبت‌نام تکمیل شد ✅", reply_markup=types.ReplyKeyboardRemove())
        show_main_menu(message.chat.id)

def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 فروشگاه بازیکن", "📋 ترکیب و تاکتیک")
    markup.row("🎮 بازی شبانه", "📄 گزارش بازی")
    markup.row("👛 کیف پول", "🎁 پاداش روزانه")
    markup.row("🏆 برترین‌ها")
    bot.send_message(chat_id, "منوی اصلی:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_player(call):
    user_id = str(call.from_user.id)
    player_name = call.data.split("_")[1]

    users = load_users()
    user = users[user_id]

    if player_name in user["players"]:
        bot.answer_callback_query(call.id, "شما این بازیکن را دارید.")
        return

    if len(user["players"]) >= 8:
        bot.answer_callback_query(call.id, "حداکثر ۸ بازیکن می‌تونی داشته باشی.")
        return

    with open(PLAYERS_FILE, "r") as f:
        all_players = json.load(f)

    player = next((p for p in all_players if p["name"] == player_name), None)
    if not player:
        bot.answer_callback_query(call.id, "بازیکن پیدا نشد.")
        return

    if user["gems"] >= player["price_gems"]:
        user["gems"] -= player["price_gems"]
        user["players"].append(player_name)
        save_users(users)
        bot.send_message(call.message.chat.id, f"✅ {player_name} با موفقیت خریداری شد.")
    elif user["coins"] >= player["price_coins"]:
        user["coins"] -= player["price_coins"]
        user["players"].append(player_name)
        save_users(users)
        bot.send_message(call.message.chat.id, f"✅ {player_name} با موفقیت با سکه خریداری شد.")
    else:
        bot.send_message(call.message.chat.id, "❌ جم یا سکه کافی نداری.")

# ---------- ترکیب و تاکتیک ----------
@bot.message_handler(func=lambda msg: msg.text == "📋 ترکیب و تاکتیک")
def show_tactic_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📌 تعیین ترکیب", "⚔️ سبک بازی")
    markup.row("🧠 تاکتیک", "🚫 تله آفساید")
    markup.row("🔥 پرسینگ", "📊 شماتیک")
    markup.row("🔙 بازگشت به منو")
    bot.send_message(message.chat.id, "یکی از گزینه‌های تاکتیکی را انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "📌 تعیین ترکیب")
def set_formation(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("۱-۲-۲", "۱-۱-۳")
    markup.row("۱-۳-۱", "۱-۴")
    markup.row("🔙 بازگشت به منو")
    bot.send_message(message.chat.id, "ترکیب مورد نظر را انتخاب کن:", reply_markup=markup)
    bot.register_next_step_handler(message, save_formation)

def save_formation(message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id]["tactic"]["formation"] = message.text
    save_users(users)
    bot.send_message(message.chat.id, f"✅ ترکیب {message.text} ذخیره شد.")

@bot.message_handler(func=lambda msg: msg.text == "🧠 تاکتیک")
def set_style(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚔️ هجومی", "🛡️ دفاعی", "⚖️ متعادل")
    markup.row("🔙 بازگشت به منو")
    bot.send_message(message.chat.id, "سبک کلی بازی را انتخاب کن:", reply_markup=markup)
    bot.register_next_step_handler(message, save_style)

def save_style(message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id]["tactic"]["style"] = message.text
    save_users(users)
    bot.send_message(message.chat.id, f"✅ تاکتیک {message.text} ذخیره شد.")

@bot.message_handler(func=lambda msg: msg.text == "⚔️ سبک بازی")
def set_playstyle(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🔁 پاسکاری", "🎯 بازی با وینگ")
    markup.row("🔙 بازگشت به منو")
    bot.send_message(message.chat.id, "سبک بازی را انتخاب کن:", reply_markup=markup)
    bot.register_next_step_handler(message, save_playstyle)

def save_playstyle(message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id]["tactic"]["playstyle"] = message.text
    save_users(users)
    bot.send_message(message.chat.id, f"✅ سبک بازی {message.text} ثبت شد.")

@bot.message_handler(func=lambda msg: msg.text == "🚫 تله آفساید")
def set_offside_trap(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📛 فعال", "❌ غیرفعال")
    markup.row("🔙 بازگشت به منو")
    bot.send_message(message.chat.id, "تله آفساید را انتخاب کن:", reply_markup=markup)
    bot.register_next_step_handler(message, save_offside)

def save_offside(message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id]["tactic"]["offside_trap"] = message.text
    save_users(users)
    bot.send_message(message.chat.id, f"✅ تله آفساید {message.text} شد.")

@bot.message_handler(func=lambda msg: msg.text == "🔥 پرسینگ")
def set_pressing(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💯 پرس کامل", "➗ پرس ۵۰٪", "🚫 بدون پرس")
    markup.row("🔙 بازگشت به منو")
    bot.send_message(message.chat.id, "میزان پرس را انتخاب کن:", reply_markup=markup)
    bot.register_next_step_handler(message, save_pressing)

def save_pressing(message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id]["tactic"]["pressing"] = message.text
    save_users(users)
    bot.send_message(message.chat.id, f"✅ پرسینگ {message.text} ذخیره شد.")

@bot.message_handler(func=lambda msg: msg.text == "📊 شماتیک")
def show_formation_schematic(message):
    user_id = str(message.from_user.id)
    users = load_users()
    user = users[user_id]
    players = user.get("players", [])

    with open(PLAYERS_FILE, "r") as f:
        all_players = json.load(f)

    player_positions = {p["name"]: p["position"] for p in all_players}
    gk = [p for p in players if player_positions.get(p) == "GK"]
    df = [p for p in players if player_positions.get(p) == "DF"]
    mf = [p for p in players if player_positions.get(p) == "MF"]
    fw = [p for p in players if player_positions.get(p) == "FW"]

    lines = []
    if fw: lines.append(" ".join(fw))
    if mf: lines.append(" ".join(mf))
    if df: lines.append(" ".join(df))
    if gk: lines.append(" ".join(gk))

    formation = "\n".join(lines)
    bot.send_message(message.chat.id, f"📊 ترکیب بازیکنان:\n{formation}")

# ---------- ثبت نام بازی شبانه ----------
night_players = []

@bot.message_handler(func=lambda msg: msg.text == "🎮 بازی شبانه")
def join_night_game(message):
    user_id = str(message.from_user.id)
    if user_id not in night_players:
        night_players.append(user_id)
        bot.send_message(message.chat.id, "✅ شما در لیست بازی شبانه ثبت شدی. رأس ساعت ۲۲ بازی شروع می‌شود.")
    else:
        bot.send_message(message.chat.id, "❌ قبلاً در لیست بازی شبانه ثبت نام کردی.")

# ---------- الگوریتم شبیه‌سازی بازی ----------
def simulate_match():
    global night_players
    users = load_users()
    random.shuffle(night_players)
    pairs = []

    while len(night_players) >= 2:
        p1 = night_players.pop()
        p2 = night_players.pop()
        pairs.append((p1, p2))

    for p1, p2 in pairs:
        user1 = users[p1]
        user2 = users[p2]

        # نمره تاکتیک و سبک بازی برای هر تیم (مثال ساده‌شده)
        def calc_score(u):
            score = 0
            tactic = u.get("tactic", {})
            style = tactic.get("style", "")
            playstyle = tactic.get("playstyle", "")
            pressing = tactic.get("pressing", "")
            formation = tactic.get("formation", "")
            offside = tactic.get("offside_trap", "")

            if style == "⚔️ هجومی": score += 5
            elif style == "🛡️ دفاعی": score += 3
            elif style == "⚖️ متعادل": score += 4

            if playstyle == "🔁 پاسکاری": score += 3
            elif playstyle == "🎯 بازی با وینگ": score += 4

            if pressing == "💯 پرس کامل": score += 3
            elif pressing == "➗ پرس ۵۰٪": score += 1

            if offside == "📛 فعال": score += 1

            # نمره ترکیب بر اساس تعداد بازیکن و formation
            formation_map = {"۱-۲-۲":4, "۱-۱-۳":4, "۱-۳-۱":3, "۱-۴":2}
            score += formation_map.get(formation, 3)

            # امتیاز قبلی تیم تاثیر دارد
            score += u.get("score", 0) / 10

            # رندوم هیجان
            score += random.uniform(-2, 2)

            return score

        score1 = calc_score(user1)
        score2 = calc_score(user2)

        # نتیجه
        if score1 > score2:
            res1, res2 = "برد", "باخت"
            user1["score"] += 20
            user1["coins"] += 100
            user2["score"] -= 10
            user2["coins"] += 20
        elif score2 > score1:
            res1, res2 = "باخت", "برد"
            user2["score"] += 20
            user2["coins"] += 100
            user1["score"] -= 10
            user1["coins"] += 20
        else:
            res1 = res2 = "مساوی"
            user1["score"] += 5
            user2["score"] += 5
            user1["coins"] += 40
            user2["coins"] += 40

        # ذخیره نتیجه بازی در تاریخ روز
        today = str(date.today())
        mh1 = user1.get("match_history", [])
        mh2 = user2.get("match_history", [])

        mh1.append({"date": today, "vs": p2, "result": res1})
        mh2.append({"date": today, "vs": p1, "result": res2})

        user1["match_history"] = mh1[-10:]  # ذخیره ۱۰ بازی آخر
        user2["match_history"] = mh2[-10:]

        # ارسال گزارش به هر دو بازیکن
        bot.send_message(int(p1), f"🎮 بازی شبانه:\nشما {res1} کردید.\nامتیاز شما: {user1['score']}\nسکه: {user1['coins']}")
        bot.send_message(int(p2), f"🎮 بازی شبانه:\nشما {res2} کردید.\nامتیاز شما: {user2['score']}\nسکه: {user2['coins']}")

    save_users(users)

# ---------- اجرای خودکار بازی شبانه با Threading ----------
def run_nightly_game():
    while True:
        now = datetime.datetime.now()
        if now.hour == 22 and now.minute == 0:
            if len(night_players) >= 2:
                bot.send_message(ADMIN_ID, "بازی شبانه شروع شد!")
                simulate_match()
            else:
                bot.send_message(ADMIN_ID, "شرکت‌کننده کافی برای بازی شبانه نیست.")
            time.sleep(60)
        time.sleep(20)

# ---------- گزارش بازی ----------
@bot.message_handler(func=lambda msg: msg.text == "📄 گزارش بازی")
def show_match_report(message):
    user_id = str(message.from_user.id)
    users = load_users()
    mh = users.get(user_id, {}).get("match_history", [])
    if not mh:
        bot.send_message(message.chat.id, "شما بازی‌ای انجام نداده‌اید.")
        return

    text = "📋 ۱۰ بازی آخر شما:\n"
    for match in mh[-10:]:
        opponent = match["vs"]
        result = match["result"]
        text += f"با {opponent}: {result}\n"

    bot.send_message(message.chat.id, text)

# ---------- برترین‌ها ----------
@bot.message_handler(func=lambda msg: msg.text == "🏆 برترین‌ها")
def show_leaderboard(message):
    users = load_users()
    ranking = []
    for uid, data in users.items():
        total_games = len(data.get("match_history", []))
        wins = sum(1 for m in data.get("match_history", []) if m["result"] == "برد")
        win_percent = (wins / total_games) * 100 if total_games > 0 else 0
        ranking.append((uid, data.get("team_name", "ناشناخته"), win_percent))

    ranking.sort(key=lambda x: x[2], reverse=True)
    text = "🏆 ۱۰ برتر بر اساس درصد برد:\n"
    for i, (uid, team, percent) in enumerate(ranking[:10], 1):
        text += f"{i}. {team}: {percent:.1f}% برد\n"

    bot.send_message(message.chat.id, text)

# ---------- کیف پول ----------
@bot.message_handler(func=lambda msg: msg.text == "👛 کیف پول")
def show_wallet(message):
    user_id = str(message.from_user.id)
    users = load_users()
    user = users.get(user_id, {})

    text = (f"👛 کیف پول شما:\n"
            f"جم: {user.get('gems', 0)}\n"
            f"سکه: {user.get('coins', 0)}\n\n"
            f"💳 آدرس ترون جهت واریز:\n{TRON_ADDRESS}\n\n"
            "🔄 تبدیل سکه به جم:\n"
            "هر ۱۰۰ سکه = ۱ جم\n"
            "برای تبدیل عدد جم مورد نظر را بنویسید.\n"
            "مثال: تبدیل ۳ جم")

    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda msg: msg.text.startswith("تبدیل "))
def convert_coins_to_gems(message):
    try:
        user_id = str(message.from_user.id)
        users = load_users()
        user = users.get(user_id, {})

        amount = int(message.text.split()[1])
        cost = amount * 100

        if user.get("coins", 0) >= cost:
            user["coins"] -= cost
            user["gems"] = user.get("gems", 0) + amount
            save_users(users)
            bot.send_message(message.chat.id, f"✅ تبدیل {cost} سکه به {amount} جم با موفقیت انجام شد.")
        else:
            bot.send_message(message.chat.id, "❌ سکه کافی ندارید.")
    except:
        bot.send_message(message.chat.id, "فرمت پیام صحیح نیست. مثلا: تبدیل ۳")

# ---------- ارسال فیش پرداخت ----------
@bot.message_handler(content_types=['photo', 'text'])
def receive_payment_proof(message):
    user_id = str(message.from_user.id)
    if message.text and message.text.startswith("فیش"):
        text = message.text
    elif message.photo:
        file_id = message.photo[-1].file_id
        text = f"فیش تصویری از کاربر {user_id}, فایل آی‌دی: {file_id}"
    else:
        return

    # ارسال به ادمین
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{user_id}"))
    markup.add(types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}"))

    if message.photo:
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=text, reply_markup=markup)
    else:
        bot.send_message(ADMIN_ID, text, reply_markup=markup)

    bot.send_message(message.chat.id, "✅ فیش شما به ادمین ارسال شد و در حال بررسی است.")

# ---------- تایید/رد ادمین ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def handle_admin_approval(call):
    data = call.data
    action, user_id = data.split("_", 1)
    users = load_users()

    if user_id not in users:
        bot.answer_callback_query(call.id, "کاربر یافت نشد.")
        return

    if action == "approve":
        users[user_id]["coins"] = users[user_id].get("coins", 0) + 100
        save_users(users)
        bot.send_message(int(user_id), "✅ فیش شما تایید شد و ۱۰۰ سکه به کیف پول شما افزوده شد.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id, "تایید شد.")
    else:
        bot.send_message(int(user_id), "❌ فیش شما رد شد. لطفا دوباره ارسال کنید.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id, "رد شد.")

# ---------- پاداش روزانه ----------
@bot.message_handler(func=lambda msg: msg.text == "🎁 پاداش روزانه")
def daily_reward(message):
    user_id = str(message.from_user.id)
    users = load_users()
    user = users.get(user_id, {})

    today_str = date.today().isoformat()
    if user.get("last_reward") == today_str:
        bot.send_message(message.chat.id, "❌ شما امروز پاداش روزانه را دریافت کرده‌اید.")
        return

    user["gems"] = user.get("gems", 0) + 2
    user["last_reward"] = today_str
    save_users(users)
    bot.send_message(message.chat.id, "🎉 پاداش روزانه شما ۲ جم به حساب شما افزوده شد.")

from flask import Flask, request
import threading

app = Flask(__name__)

# ---------- راه‌اندازی وبهوک ----------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_update = request.get_json(force=True)
    update = telebot.types.Update.de_json(json_update)
    bot.process_new_updates([update])
    return "", 200

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# ---------- اجرای بازی شبانه در پس‌زمینه ----------
threading.Thread(target=run_nightly_game, daemon=True).start()

# ---------- اجرای فلَسک در Thread ----------
threading.Thread(target=run_flask, daemon=True).start()

print("ربات در حال اجراست...")

# ---------- اجرای تلگرام بات ----------
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# ---------- نگهداری برنامه ----------
import time
while True:
    time.sleep(10)

# ---------- ذخیره‌سازی (توابع کمک) ----------
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- متغیرها و فایل‌ها ----------
TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "@Specialcoach1"
TRON_ADDRESS = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"
WEBHOOK_URL = "https://special-coach.onrender.com/" + TOKEN

USERS_FILE = "data/users.json"
PLAYERS_FILE = "data/players.json"

import telebot
import json
import datetime
import random
from datetime import date

bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

bot = telebot.TeleBot(TOKEN)
