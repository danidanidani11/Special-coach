import telebot
from telebot import types
from flask import Flask, request
import threading, json, os, time, datetime, random
from datetime import date

TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
WEBHOOK_URL = "https://special-coach.onrender.com/" + TOKEN
ADMIN_ID = 5542927340
CHANNEL = "@Specialcoach1"
TRON = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"
USERS_FILE = "data/users.json"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_states = {}

# ✅ ساخت دیتای کاربران
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    return json.load(open(USERS_FILE, "r", encoding="utf-8"))

def save_users(u):
    json.dump(u, open(USERS_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# 📋 منو اصلی
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 ترکیب و تاکتیک", "🏪 فروشگاه بازیکن")
    markup.row("🎮 بازی شبانه", "📄 گزارش بازی")
    markup.row("👛 کیف پول", "🎁 پاداش روزانه")
    markup.row("🏆 برترین‌ها")
    return markup

# 📲 دکمه بازگشت
def back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بازگشت به منو")
    return markup

# 🧍‍♂️ تعریف ۵۰ بازیکن واقعی
ALL_PLAYERS = {
    f"player{i+1}": {
        "name": name,
        "overall": ovr,
        "position": pos,
        "price_gems": gem,
        "price_coins": coin
    }
    for i, (name, ovr, pos, gem, coin) in enumerate([
        # 🟢 ضعیف‌ها (۱ تا ۲۵)
        ("Ali Karimi", 45, "MF", 1, 50), ("Rahim Mehdi", 48, "DF", 1, 60),
        ("Milad Mansoori", 50, "FW", 1, 80), ("Hamid Safaei", 43, "GK", 1, 40),
        ("Saeid Moradi", 47, "MF", 1, 70), ("Hamed Esmaeili", 49, "DF", 1, 65),
        ("Reza Samiei", 46, "MF", 1, 55), ("Nima Khosravi", 50, "FW", 1, 80),
        ("Amin Tork", 44, "GK", 1, 40), ("Sina Pakzad", 48, "DF", 1, 60),
        ("Mohammad Zarei", 45, "MF", 1, 50), ("Kian Ahmadi", 49, "FW", 1, 75),
        ("Mehdi Jafari", 47, "DF", 1, 65), ("Peyman Ranjbar", 46, "MF", 1, 60),
        ("Yasin Amini", 43, "GK", 1, 35), ("Omid Karami", 45, "DF", 1, 50),
        ("Armin Lotfi", 50, "MF", 1, 80), ("Navid Saeedi", 49, "FW", 1, 70),
        ("Danial Kazemi", 48, "DF", 1, 60), ("Soroush Ghaedi", 46, "MF", 1, 55),
        ("Farshad Bakhtiari", 45, "MF", 1, 50), ("Behzad Ghaffari", 44, "GK", 1, 40),
        ("Shahab Miri", 47, "DF", 1, 65), ("Masoud Jalili", 46, "MF", 1, 55),
        ("Kaveh Bayat", 43, "GK", 1, 30),
        # 🔴 قوی‌ها (۲۶ تا ۵۰)
        ("Messi", 99, "FW", 10, 800), ("Ronaldo", 98, "FW", 9, 750),
        ("Mbappe", 97, "FW", 9, 720), ("De Bruyne", 95, "MF", 8, 650),
        ("Modric", 94, "MF", 7, 600), ("Kimmich", 93, "MF", 7, 580),
        ("Haaland", 96, "FW", 9, 700), ("Vinicius", 93, "FW", 8, 620),
        ("Kane", 92, "FW", 8, 600), ("Neymar", 91, "FW", 7, 580),
        ("Valverde", 89, "MF", 6, 500), ("Musiala", 88, "MF", 6, 480),
        ("Ramos", 92, "DF", 8, 600), ("Van Dijk", 91, "DF", 8, 590),
        ("Hakimi", 90, "DF", 7, 560), ("Alaba", 89, "DF", 6, 540),
        ("Walker", 88, "DF", 6, 500), ("Robertson", 87, "DF", 6, 480),
        ("Ederson", 91, "GK", 7, 550), ("Ter Stegen", 90, "GK", 7, 540),
        ("Oblak", 89, "GK", 6, 500), ("Maignan", 87, "GK", 6, 470),
        ("Lunin", 86, "GK", 5, 450), ("Onana", 88, "GK", 5, 460),
        ("Neuer", 92, "GK", 8, 600),
    ])
}

# 🧾 بررسی عضویت
def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# 🚀 /start
@bot.message_handler(commands=["start"])
def start(m):
    uid = str(m.from_user.id)
    users = load_users()
    if uid in users:
        bot.send_message(m.chat.id, "🔁 خوش برگشتی!", reply_markup=main_menu())
        return

    if not is_member(m.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 عضویت در کانال", url="https://t.me/" + CHANNEL[1:]))
        markup.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_sub"))
        bot.send_message(m.chat.id, "برای ادامه، ابتدا در کانال عضو شو:", reply_markup=markup)
        return

    user_states[uid] = {"step": "team_name"}
    bot.send_message(m.chat.id, "👨‍🏫 نام تیم‌ت رو بنویس:")

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_subscription(c):
    if is_member(c.from_user.id):
        user_states[str(c.from_user.id)] = {"step": "team_name"}
        bot.send_message(c.message.chat.id, "✅ حالا نام تیم‌ت رو بنویس:")
    else:
        bot.answer_callback_query(c.id, "⛔ هنوز عضو نشدی!")

# 📱 دریافت شماره تماس
@bot.message_handler(content_types=["text"])
def get_team_name(m):
    uid = str(m.from_user.id)
    if uid in user_states and user_states[uid]["step"] == "team_name":
        user_states[uid]["team"] = m.text
        user_states[uid]["step"] = "phone"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn = types.KeyboardButton("📱 ارسال شماره", request_contact=True)
        markup.add(btn)
        bot.send_message(m.chat.id, "شماره‌ت رو بفرست:", reply_markup=markup)
        return
    elif m.text == "بازگشت به منو":
        bot.send_message(m.chat.id, "🏠 برگشتی به منو", reply_markup=main_menu())

@bot.message_handler(content_types=["contact"])
def get_contact(m):
    uid = str(m.from_user.id)
    if uid in user_states and user_states[uid]["step"] == "phone":
        users = load_users()
        users[uid] = {
            "team": user_states[uid]["team"],
            "phone": m.contact.phone_number,
            "players": [f"player{i}" for i in range(1, 6)],  # ۵ بازیکن ضعیف
            "tactic": {"formation": "", "mode": "", "style": "", "offside": "", "press": ""},
            "score": 0,
            "coins": 100,
            "gems": 2,
            "match_history": [],
            "last_reward": ""
        }
        save_users(users)
        bot.send_message(m.chat.id, "✅ ثبت‌نام با موفقیت انجام شد!", reply_markup=main_menu())
        user_states.pop(uid)

# 🛍️ فروشگاه بازیکن
@bot.message_handler(func=lambda m: m.text == "🏪 فروشگاه بازیکن")
def player_shop(m):
    uid = str(m.from_user.id)
    users = load_users()
    if uid not in users:
        bot.send_message(m.chat.id, "❌ ابتدا ثبت‌نام کن")
        return

    for pid, pl in ALL_PLAYERS.items():
        if pid in users[uid]["players"]:
            continue  # بازیکن تکراری نخریم
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"💰 با {pl['price_coins']} سکه", callback_data=f"buyc_{pid}"))
        markup.add(types.InlineKeyboardButton(f"💎 با {pl['price_gems']} جم", callback_data=f"buyg_{pid}"))
        bot.send_message(m.chat.id,
                         f"👤 {pl['name']} ({pl['position']})\n📊 قدرت: {pl['overall']}",
                         reply_markup=markup)

    bot.send_message(m.chat.id, "🔙 برای بازگشت از دکمه زیر استفاده کن", reply_markup=back_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy"))
def buy_player(c):
    uid = str(c.from_user.id)
    users = load_users()
    pid = c.data[5:]
    mode = c.data[:4]

    if pid not in ALL_PLAYERS:
        bot.answer_callback_query(c.id, "❌ بازیکن نامعتبر")
        return

    if pid in users[uid]["players"]:
        bot.answer_callback_query(c.id, "⚠️ قبلاً خریدی")
        return

    if len(users[uid]["players"]) >= 8:
        bot.answer_callback_query(c.id, "👥 حداکثر ۸ بازیکن")
        return

    pl = ALL_PLAYERS[pid]
    if mode == "buyc" and users[uid]["coins"] >= pl["price_coins"]:
        users[uid]["coins"] -= pl["price_coins"]
    elif mode == "buyg" and users[uid]["gems"] >= pl["price_gems"]:
        users[uid]["gems"] -= pl["price_gems"]
    else:
        bot.answer_callback_query(c.id, "❌ موجودی کافی نیست")
        return

    users[uid]["players"].append(pid)
    save_users(users)
    bot.answer_callback_query(c.id, "✅ خرید موفق انجام شد")

# ⚽ ترکیب و تاکتیک
@bot.message_handler(func=lambda m: m.text == "📋 ترکیب و تاکتیک")
def tactics_menu(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📌 ترکیب", "🎯 تاکتیک", "⚙️ سبک بازی")
    markup.row("🧱 تله آفساید", "💨 پرسینگ")
    markup.add("📊 شماتیک")
    markup.add("بازگشت به منو")
    bot.send_message(m.chat.id, "📋 یکی از گزینه‌ها رو انتخاب کن:", reply_markup=markup)

# ترکیب
@bot.message_handler(func=lambda m: m.text == "📌 ترکیب")
def formation(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("۱-۲-۲", "۱-۱-۳", "۱-۳-۱", "۱-۴")
    markup.add("بازگشت به منو")
    bot.send_message(m.chat.id, "🔁 یکی از چیدمان‌ها رو انتخاب کن", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["۱-۲-۲", "۱-۱-۳", "۱-۳-۱", "۱-۴"])
def save_formation(m):
    users = load_users()
    uid = str(m.from_user.id)
    users[uid]["tactic"]["formation"] = m.text
    save_users(users)
    bot.send_message(m.chat.id, f"✅ ترکیب ذخیره شد: {m.text}")

# تاکتیک
@bot.message_handler(func=lambda m: m.text == "🎯 تاکتیک")
def tactic_choice(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("هجومی", "دفاعی", "متعادل")
    markup.add("بازگشت به منو")
    bot.send_message(m.chat.id, "🎯 سبک تاکتیک رو انتخاب کن", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["هجومی", "دفاعی", "متعادل"])
def save_tactic(m):
    users = load_users()
    uid = str(m.from_user.id)
    users[uid]["tactic"]["mode"] = m.text
    save_users(users)
    bot.send_message(m.chat.id, f"✅ تاکتیک ذخیره شد: {m.text}")

# سبک بازی
@bot.message_handler(func=lambda m: m.text == "⚙️ سبک بازی")
def style_choice(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("پاسکاری", "بازی با وینگ", "ضدحمله")
    markup.add("بازگشت به منو")
    bot.send_message(m.chat.id, "⚙️ سبک بازی رو انتخاب کن", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["پاسکاری", "بازی با وینگ", "ضدحمله"])
def save_style(m):
    users = load_users()
    uid = str(m.from_user.id)
    users[uid]["tactic"]["style"] = m.text
    save_users(users)
    bot.send_message(m.chat.id, f"✅ سبک بازی ذخیره شد: {m.text}")

# تله افساید
@bot.message_handler(func=lambda m: m.text == "🧱 تله آفساید")
def offside_trap(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بذار", "نذار")
    markup.add("بازگشت به منو")
    bot.send_message(m.chat.id, "🧱 تله آفساید فعال باشه؟", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["بذار", "نذار"])
def save_offside(m):
    users = load_users()
    uid = str(m.from_user.id)
    users[uid]["tactic"]["offside"] = m.text
    save_users(users)
    bot.send_message(m.chat.id, f"✅ وضعیت تله آفساید: {m.text}")

# پرسینگ
@bot.message_handler(func=lambda m: m.text == "💨 پرسینگ")
def press(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("پرس ۱۰۰ درصد", "پرس ۵۰ درصد", "نمی‌خوام")
    markup.add("بازگشت به منو")
    bot.send_message(m.chat.id, "💨 میزان پرس رو مشخص کن", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["پرس ۱۰۰ درصد", "پرس ۵۰ درصد", "نمی‌خوام"])
def save_press(m):
    users = load_users()
    uid = str(m.from_user.id)
    users[uid]["tactic"]["press"] = m.text
    save_users(users)
    bot.send_message(m.chat.id, f"✅ پرسینگ ثبت شد: {m.text}")

# 📊 شماتیک ترکیب
@bot.message_handler(func=lambda m: m.text == "📊 شماتیک")
def show_schematic(m):
    uid = str(m.from_user.id)
    users = load_users()
    if uid not in users:
        return bot.send_message(m.chat.id, "❌ ابتدا ثبت‌نام کن")

    players = users[uid]["players"]
    lines = {"GK": [], "DF": [], "MF": [], "FW": []}
    for pid in players:
        if pid in ALL_PLAYERS:
            pl = ALL_PLAYERS[pid]
            lines[pl["position"]].append(pl["name"])

    text = f"⚽ چیدمان تیم {users[uid]['team']}:\n\n"
    if lines["FW"]: text += "🔼 حمله: " + "   ".join(lines["FW"]) + "\n"
    if lines["MF"]: text += "🏃‍♂️ هافبک: " + "   ".join(lines["MF"]) + "\n"
    if lines["DF"]: text += "🛡 دفاع: " + "   ".join(lines["DF"]) + "\n"
    if lines["GK"]: text += "🧤 دروازه‌بان: " + "   ".join(lines["GK"]) + "\n"

    bot.send_message(m.chat.id, text or "❌ ترکیب خالیه", reply_markup=back_menu())

# 🎮 بازی شبانه ثبت‌نام
participants = set()

@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def join_game(m):
    uid = str(m.from_user.id)
    if uid not in load_users():
        return bot.send_message(m.chat.id, "❌ ابتدا ثبت‌نام کن")
    participants.add(uid)
    bot.send_message(m.chat.id, "✅ ثبت‌نام شدی. ساعت ۲۲ نتیجه رو دریافت می‌کنی!", reply_markup=back_menu())

# 📄 گزارش بازی
@bot.message_handler(func=lambda m: m.text == "📄 گزارش بازی")
def match_report(m):
    uid = str(m.from_user.id)
    users = load_users()
    hist = users[uid].get("match_history", [])
    if not hist:
        return bot.send_message(m.chat.id, "❌ هنوز هیچ بازی‌ای انجام ندادی", reply_markup=back_menu())
    report = "\n\n".join(hist[-3:])
    bot.send_message(m.chat.id, f"📄 آخرین بازی‌ها:\n\n{report}", reply_markup=back_menu())

# ⏰ اجرای شبانه
def run_nightly_game():
    while True:
        now = datetime.datetime.now()
        if now.hour == 22 and now.minute == 0:
            do_matchmaking()
            time.sleep(60)
        time.sleep(1)

def do_matchmaking():
    global participants
    users = load_users()
    ps = list(participants)
    random.shuffle(ps)
    while len(ps) >= 2:
        u1, u2 = ps.pop(), ps.pop()
        t1, t2 = users[u1]["tactic"], users[u2]["tactic"]
        s1, s2 = score_team(t1), score_team(t2)
        result = simulate(u1, u2, s1, s2)
        users[u1]["match_history"].append(result[0])
        users[u2]["match_history"].append(result[1])
    save_users(users)
    participants.clear()

def score_team(t):
    score = 0
    score += {"۱-۲-۲": 3, "۱-۱-۳": 4, "۱-۳-۱": 2, "۱-۴": 5}.get(t["formation"], 0)
    score += {"هجومی": 4, "متعادل": 3, "دفاعی": 2}.get(t["mode"], 0)
    score += {"پاسکاری": 3, "ضدحمله": 4, "بازی با وینگ": 3}.get(t["style"], 0)
    score += 1 if t["offside"] == "بذار" else 0
    score += {"پرس ۱۰۰ درصد": 3, "پرس ۵۰ درصد": 2}.get(t["press"], 0)
    return score

def simulate(u1, u2, s1, s2):
    users = load_users()
    diff = s1 - s2
    if diff > 1:
        users[u1]["score"] += 20
        users[u2]["score"] -= 10
        users[u1]["coins"] += 100
        users[u2]["coins"] += 20
        return [f"🎉 بردی مقابل {users[u2]['team']}", f"❌ باختی به {users[u1]['team']}"]
    elif diff < -1:
        users[u2]["score"] += 20
        users[u1]["score"] -= 10
        users[u2]["coins"] += 100
        users[u1]["coins"] += 20
        return [f"❌ باختی به {users[u2]['team']}", f"🎉 بردی مقابل {users[u1]['team']}"]
    else:
        users[u1]["score"] += 5
        users[u2]["score"] += 5
        users[u1]["coins"] += 40
        users[u2]["coins"] += 40
        return [f"⚖️ مساوی با {users[u2]['team']}", f"⚖️ مساوی با {users[u1]['team']}"]

# ▶ اجرای Flask و Webhook
if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    threading.Thread(target=run_nightly_game, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
