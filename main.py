import telebot
from telebot import types
from flask import Flask, request
import threading, json, os, time, datetime, random
from datetime import date

# 🔧 تنظیمات
TOKEN = os.getenv("TOKEN", "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://special-coach.onrender.com/" + TOKEN)
ADMIN_ID = int(os.getenv("ADMIN_ID", "5542927340"))
CHANNEL = os.getenv("CHANNEL", "@Specialcoach1")
TRON = os.getenv("TRON", "TJ4xrwKJzKjk6FgKfuuqvah3Az5Ur22kJb")
USERS_FILE = "data/users.json"
PLAYERS_FILE = "data/players.json"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_states = {}

# 📂 ذخیره و خواندن کاربران
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    return json.load(open(USERS_FILE, "r", encoding="utf-8"))

def save_users(u): 
    json.dump(u, open(USERS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ✅ بررسی عضویت در کانال
def is_member(user_id):
    try:
        st = bot.get_chat_member(CHANNEL, user_id).status
        return st in ["member","creator","administrator"]
    except:
        return False

# 📋 منو اصلی
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 ترکیب و تاکتیک", "🏪 فروشگاه")
    markup.row("🎮 بازی شبانه", "📄 گزارش بازی")
    markup.row("👛 کیف پول", "🎁 پاداش روزانه")
    markup.row("🏆 برترین‌ها")
    return markup

# 🔄 هندلِر استارت و ثبت‌نام
@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid = m.from_user.id
    us = load_users()
    if str(uid) in us:
        bot.reply_to(m, "خوش برگشتی!", reply_markup=main_menu())
    else:
        user_states[str(uid)] = "awaiting_join"
        ask_join(m)

def ask_join(m):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ من عضو شدم", callback_data="chk_join"))
    markup.add(types.InlineKeyboardButton("📢 عضو کانال", url=f"https://t.me/{CHANNEL.strip('@')}"))
    bot.send_message(m.chat.id, "لطفاً ابتدا در کانال عضویت خود را تأیید کن:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data=="chk_join")
def cb_join(c):
    uid = c.from_user.id
    if is_member(uid):
        bot.answer_callback_query(c.id, "✅ عضویت تأیید شد")
        user_states[str(uid)] = "awaiting_team"
        bot.send_message(c.message.chat.id, "🏟️ اسم تیم رو بده:")
    else:
        bot.answer_callback_query(c.id, "❌ هنوز عضو نیستی")

@bot.message_handler(func=lambda m: user_states.get(str(m.from_user.id))=="awaiting_team")
def ask_team(m):
    user_states[str(m.from_user.id)] = m.text.strip()
    bot.send_message(m.chat.id, "📱 حالا شماره‌تو بفرساز:", reply_markup=types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True).add(types.KeyboardButton("📱 ارسال شماره", request_contact=True)))

@bot.message_handler(content_types=["contact"])
def get_contact(m):
    uid = str(m.from_user.id)
    if user_states.get(uid) and isinstance(user_states[uid], str) and user_states[uid]!="awaiting_team":
        us = load_users()
        us[uid] = {"team": user_states[uid], "phone": m.contact.phone_number,
                  "players": [f"player{i}" for i in range(1,6)],
                  "coins":0,"gems":0,"score":0,"tactic":{},"match_history":[], "last_reward":""}
        save_users(us)
        user_states[uid] = ""
        bot.send_message(m.chat.id, "✅ ثبت شد!", reply_markup=main_menu())

# ⚠ وبهوک فلَسک
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode())
    bot.process_new_updates([update])
    return "",200

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",5000)))

# 🔥 نمایش فروشگاه بازیکنان
@bot.message_handler(func=lambda m: m.text == "🏪 فروشگاه")
def player_shop(m):
    uid = str(m.from_user.id)
    users = load_users()
    if uid not in users:
        bot.reply_to(m, "❌ ابتدا ثبت‌نام کن")
        return

    with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
        players = json.load(f)

    for pid, pl in players.items():
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"💰 خرید با {pl['price_coins']} سکه", callback_data=f"buyc_{pid}"))
        markup.add(types.InlineKeyboardButton(f"💎 خرید با {pl['price_gems']} جم", callback_data=f"buyg_{pid}"))
        bot.send_message(m.chat.id,
                         f"👤 {pl['name']} ({pl['position']})\n📊 قدرت: {pl['overall']}",
                         reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy"))
def buy_player(c):
    uid = str(c.from_user.id)
    users = load_users()
    players = json.load(open(PLAYERS_FILE, encoding="utf-8"))
    if uid not in users:
        return

    mode, pid = c.data[:4], c.data[5:]
    if pid not in players:
        bot.answer_callback_query(c.id, "❌ بازیکن نامعتبر")
        return

    if pid in users[uid]["players"]:
        bot.answer_callback_query(c.id, "⚠️ قبلاً خریدی")
        return

    if len(users[uid]["players"]) >= 8:
        bot.answer_callback_query(c.id, "👥 حداکثر ۸ بازیکن")
        return

    pl = players[pid]
    if mode == "buyc" and users[uid]["coins"] >= pl["price_coins"]:
        users[uid]["coins"] -= pl["price_coins"]
    elif mode == "buyg" and users[uid]["gems"] >= pl["price_gems"]:
        users[uid]["gems"] -= pl["price_gems"]
    else:
        bot.answer_callback_query(c.id, "❌ موجودی کافی نیست")
        return

    users[uid]["players"].append(pid)
    save_users(users)
    bot.answer_callback_query(c.id, "✅ خرید موفق")

# ⚽ ترکیب و تاکتیک
@bot.message_handler(func=lambda m: m.text == "📋 ترکیب و تاکتیک")
def lineup_menu(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📌 ترکیب", "🧠 تاکتیک")
    markup.add("🎯 سبک بازی", "📍 تله آفساید")
    markup.add("🔥 پرسینگ", "بازگشت به منو")
    bot.send_message(m.chat.id, "یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📌 ترکیب")
def formation_selector(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("1-2-2", "1-1-3", "1-3-1", "1-4")
    bot.send_message(m.chat.id, "✅ یک چیدمان انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["1-2-2", "1-1-3", "1-3-1", "1-4"])
def set_formation(m):
    uid = str(m.from_user.id)
    users = load_users()
    users[uid]["tactic"]["formation"] = m.text
    save_users(users)
    bot.send_message(m.chat.id, f"📌 ترکیب تیم ذخیره شد: {m.text}")

@bot.message_handler(func=lambda m: m.text == "🧠 تاکتیک")
def tactics(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("هجومی", "دفاعی", "متعادل")
    bot.send_message(m.chat.id, "⚔️ تاکتیک رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["هجومی", "دفاعی", "متعادل"])
def set_tactic(m):
    uid = str(m.from_user.id)
    users = load_users()
    users[uid]["tactic"]["mode"] = m.text
    save_users(users)
    bot.send_message(m.chat.id, f"🧠 تاکتیک تنظیم شد: {m.text}")

@bot.message_handler(func=lambda m: m.text == "🎯 سبک بازی")
def styles(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("پاسکاری", "وینگ", "ضربات بلند")
    bot.send_message(m.chat.id, "🎯 سبک بازی رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["پاسکاری", "وینگ", "ضربات بلند"])
def set_style(m):
    uid = str(m.from_user.id)
    users = load_users()
    users[uid]["tactic"]["style"] = m.text
    save_users(users)
    bot.send_message(m.chat.id, f"🎯 سبک بازی انتخاب شد: {m.text}")

@bot.message_handler(func=lambda m: m.text == "📍 تله آفساید")
def offsides(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✅ بذار", "❌ نذار")
    bot.send_message(m.chat.id, "📍 تله آفساید؟", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["✅ بذار", "❌ نذار"])
def set_offside(m):
    uid = str(m.from_user.id)
    users = load_users()
    users[uid]["tactic"]["offside"] = m.text
    save_users(users)
    bot.send_message(m.chat.id, f"📍 تنظیم شد: {m.text}")

@bot.message_handler(func=lambda m: m.text == "🔥 پرسینگ")
def pressing(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("پرس ۱۰۰ درصد", "پرس ۵۰ درصد", "نمی‌خوام")
    bot.send_message(m.chat.id, "📡 سطح پرسینگ رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["پرس ۱۰۰ درصد", "پرس ۵۰ درصد", "نمی‌خوام"])
def set_press(m):
    uid = str(m.from_user.id)
    users = load_users()
    users[uid]["tactic"]["press"] = m.text
    save_users(users)
    bot.send_message(m.chat.id, f"📡 پرسینگ ذخیره شد: {m.text}")

# 🎮 شرکت در بازی شبانه
nightly_players = []

@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def join_game(m):
    uid = str(m.from_user.id)
    if uid not in nightly_players:
        nightly_players.append(uid)
        bot.send_message(m.chat.id, "✅ در لیست بازی شبانه قرار گرفتی!")
    else:
        bot.send_message(m.chat.id, "⚠️ قبلاً ثبت‌نام کردی")

# اجرای خودکار بازی شبانه
def run_nightly_game():
    while True:
        now = datetime.datetime.now()
        if now.hour == 22 and now.minute == 0:
            if len(nightly_players) >= 2:
                random.shuffle(nightly_players)
                for i in range(0, len(nightly_players)-1, 2):
                    u1, u2 = nightly_players[i], nightly_players[i+1]
                    simulate_match(u1, u2)
            nightly_players.clear()
        time.sleep(60)

# شبیه‌سازی بازی منطقی + گزارش
def simulate_match(uid1, uid2):
    users = load_users()
    u1 = users[uid1]
    u2 = users[uid2]

    score1 = random.randint(0, 5)
    score2 = random.randint(0, 5)

    report = f"🎮 بازی شبانه:\n{u1['team']} {score1} - {score2} {u2['team']}"
    if score1 > score2:
        u1["score"] += 20
        u1["coins"] += 100
        u2["score"] -= 10
        u2["coins"] += 20
    elif score1 < score2:
        u2["score"] += 20
        u2["coins"] += 100
        u1["score"] -= 10
        u1["coins"] += 20
    else:
        u1["score"] += 5
        u2["score"] += 5
        u1["coins"] += 40
        u2["coins"] += 40

    u1["match_history"].append(report)
    u2["match_history"].append(report)
    save_users(users)

    bot.send_message(int(uid1), f"📄 گزارش بازی:\n{report}")
    bot.send_message(int(uid2), f"📄 گزارش بازی:\n{report}")

# 👛 کیف پول
@bot.message_handler(func=lambda m: m.text == "👛 کیف پول")
def wallet(m):
    uid = str(m.from_user.id)
    users = load_users()
    u = users.get(uid)
    if not u:
        bot.send_message(m.chat.id, "❌ ابتدا ثبت‌نام کن")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💱 تبدیل سکه به جم", callback_data="convert"))
    markup.add(types.InlineKeyboardButton("📤 ارسال فیش", callback_data="invoice"))
    msg = f"""💰 کیف پول شما:

💎 جم: {u.get('gems',0)}
🪙 سکه: {u.get('coins',0)}
📥 آدرس ترون:
`{TRON}`

🎯 هر ۱۰۰ سکه = ۱ جم
🎯 هر ۴ ترون = ۱۰۰ سکه"""
    bot.send_message(m.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "convert")
def convert(c):
    uid = str(c.from_user.id)
    users = load_users()
    coins = users[uid].get("coins", 0)
    if coins < 100:
        bot.answer_callback_query(c.id, "❌ حداقل ۱۰۰ سکه لازم داری")
        return
    users[uid]["coins"] -= 100
    users[uid]["gems"] += 1
    save_users(users)
    bot.answer_callback_query(c.id, "✅ تبدیل شد: ۱ جم دریافت کردی")
    bot.send_message(c.message.chat.id, "🎉 ۱ جم به کیف پول شما افزوده شد")

@bot.callback_query_handler(func=lambda c: c.data == "invoice")
def ask_invoice(c):
    bot.send_message(c.message.chat.id, "🧾 فیش پرداخت (عکس یا متن) را بفرستید")

@bot.message_handler(content_types=["photo", "text"])
def handle_invoice(m):
    uid = str(m.from_user.id)
    if not is_member(uid): return
    if m.content_type == "photo":
        fid = m.photo[-1].file_id
        bot.send_photo(ADMIN_ID, fid, caption=f"📥 فیش جدید از {uid}", reply_markup=invoice_buttons(uid))
    elif m.text and len(m.text) < 300:
        bot.send_message(ADMIN_ID, f"🧾 فیش متنی از {uid}:\n{m.text}", reply_markup=invoice_buttons(uid))

def invoice_buttons(uid):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تایید", callback_data=f"ok_{uid}"))
    markup.add(types.InlineKeyboardButton("❌ رد", callback_data=f"no_{uid}"))
    return markup

@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_") or c.data.startswith("no_"))
def handle_invoice_response(c):
    uid = c.data[3:]
    if c.data.startswith("ok_"):
        users = load_users()
        users[uid]["coins"] += 100
        save_users(users)
        bot.send_message(int(uid), "✅ فیش تایید شد! ۱۰۰ سکه به کیف شما اضافه شد")
        bot.edit_message_text("تایید شد", c.message.chat.id, c.message.message_id)
    else:
        bot.send_message(int(uid), "❌ فیش شما رد شد. دوباره ارسال کنید")
        bot.edit_message_text("رد شد", c.message.chat.id, c.message.message_id)

# 🎁 پاداش روزانه
@bot.message_handler(func=lambda m: m.text == "🎁 پاداش روزانه")
def daily_reward(m):
    uid = str(m.from_user.id)
    users = load_users()
    if not uid in users:
        bot.send_message(m.chat.id, "❌ ابتدا ثبت‌نام کن")
        return
    today = date.today().isoformat()
    if users[uid].get("last_reward") == today:
        bot.send_message(m.chat.id, "❌ امروز پاداش گرفتی. فردا بیا")
        return
    users[uid]["last_reward"] = today
    users[uid]["gems"] += 2
    save_users(users)
    bot.send_message(m.chat.id, "✅ ۲ جم به عنوان پاداش روزانه دریافت کردی!")

# 🏆 برترین‌ها
@bot.message_handler(func=lambda m: m.text == "🏆 برترین‌ها")
def top_players(m):
    users = load_users()
    win_rates = []
    for uid, data in users.items():
        games = len(data.get("match_history", []))
        score = data.get("score", 0)
        rate = (score / games) if games > 0 else 0
        win_rates.append((uid, data["team"], rate))
    top = sorted(win_rates, key=lambda x: x[2], reverse=True)[:10]
    msg = "🏆 برترین تیم‌ها:\n\n"
    for i, (uid, team, rate) in enumerate(top, 1):
        msg += f"{i}. {team}: {round(rate)} امتیاز\n"
    bot.send_message(m.chat.id, msg)

# ▶ اجرای فلَسک و Webhook
if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    threading.Thread(target=run_nightly_game, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
