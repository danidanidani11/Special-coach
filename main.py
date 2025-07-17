import telebot
from telebot import types
from flask import Flask, request
import os, time, json, threading, random, datetime

TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
WEBHOOK_URL = "https://special-coach.onrender.com/" + TOKEN
ADMIN_ID = 5542927340
CHANNEL = "@Specialcoach1"
TRON_ADDRESS = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
DATA_FOLDER = "data"
USERS_FILE = os.path.join(DATA_FOLDER, "users.json")

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# ۵۰ بازیکن واقعی (۲۵ ضعیف، ۲۵ قوی)
ALL_PLAYERS = {
    "player1": {"name": "بازیکن ضعیف 1", "overall": 40, "position": "DF", "price_coins": 20, "price_gems": 1},
    "player2": {"name": "بازیکن ضعیف 2", "overall": 42, "position": "DF", "price_coins": 25, "price_gems": 1},
    "player3": {"name": "بازیکن ضعیف 3", "overall": 43, "position": "MF", "price_coins": 25, "price_gems": 1},
    "player25": {"name": "بازیکن ضعیف 25", "overall": 50, "position": "GK", "price_coins": 30, "price_gems": 1},

    "player26": {"name": "Messi", "overall": 93, "position": "FW", "price_coins": 500, "price_gems": 10},
    "player27": {"name": "Ronaldo", "overall": 91, "position": "FW", "price_coins": 480, "price_gems": 10},
    "player28": {"name": "Modric", "overall": 90, "position": "MF", "price_coins": 450, "price_gems": 9},
    "player50": {"name": "Ter Stegen", "overall": 88, "position": "GK", "price_coins": 400, "price_gems": 8}
}

# توابع کمکی برای دیتابیس
def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

# چک عضویت در کانال
def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# منو اصلی
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 ترکیب و تاکتیک", "🏪 فروشگاه بازیکن")
    markup.row("🎮 بازی شبانه", "📄 گزارش بازی")
    markup.row("👛 کیف پول", "🏆 برترین‌ها")
    markup.row("🎁 پاداش روزانه")
    return markup

# منوی بازگشت
def back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بازگشت به منو")
    return markup

# متغیر برای وضعیت کاربر در ثبت‌نام
user_states = {}
participants = set()
daily_rewards = {}  # برای پیگیری پاداش روزانه

# /start — بررسی عضویت و شروع ثبت‌نام
@bot.message_handler(commands=["start"])
def start_command(message):
    uid = str(message.from_user.id)
    users = load_users()

    if uid in users:
        bot.send_message(message.chat.id, "👋 خوش اومدی مجدد!", reply_markup=main_menu())
        return

    if not is_member(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL.strip('@')}"))
        markup.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_join"))
        bot.send_message(message.chat.id, "برای ادامه باید در کانال عضو بشی:", reply_markup=markup)
        return

    user_states[uid] = "awaiting_team"
    bot.send_message(message.chat.id, "🏟️ نام تیم خود را وارد کن:")

# بررسی عضویت پس از زدن دکمه "عضو شدم"
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if is_member(call.from_user.id):
        uid = str(call.from_user.id)
        user_states[uid] = "awaiting_team"
        bot.send_message(call.message.chat.id, "✅ عضویت تایید شد!\n\n🏟️ حالا نام تیم خودتو وارد کن:")
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو کانال نشدی!")

# دریافت نام تیم
@bot.message_handler(func=lambda message: user_states.get(str(message.from_user.id)) == "awaiting_team")
def get_team_name(message):
    uid = str(message.from_user.id)
    team_name = message.text.strip()

    if len(team_name) < 3:
        bot.send_message(message.chat.id, "❗ نام تیم باید حداقل ۳ کاراکتر باشد.")
        return

    user_states[uid] = {"step": "awaiting_phone", "team": team_name}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("📱 ارسال شماره تماس", request_contact=True)
    markup.add(btn)

    bot.send_message(message.chat.id, "لطفاً شماره موبایل خود را ارسال کن:", reply_markup=markup)

# دریافت شماره تماس و ثبت نهایی کاربر
@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    uid = str(message.from_user.id)
    if not user_states.get(uid) or user_states[uid].get("step") != "awaiting_phone":
        return

    contact = message.contact.phone_number
    team_name = user_states[uid]["team"]

    users = load_users()
    users[uid] = {
        "team": team_name,
        "phone": contact,
        "players": [f"player{i}" for i in range(1, 6)],
        "tactic": {
            "formation": "",
            "mode": "",
            "style": "",
            "offside": "",
            "press": ""
        },
        "score": 0,
        "coins": 100,
        "gems": 2,
        "match_history": [],
        "last_daily_reward": None
    }

    save_users(users)
    user_states.pop(uid)

    bot.send_message(message.chat.id, "🎉 ثبت‌نام کامل شد. به منوی اصلی خوش اومدی!", reply_markup=main_menu())

# 🏆 برترین‌ها
@bot.message_handler(func=lambda m: m.text == "🏆 برترین‌ها")
def show_top_players(m):
    users = load_users()
    if not users:
        return bot.send_message(m.chat.id, "❌ هنوز کاربری ثبت‌نام نکرده است.")
    
    # مرتب‌سازی کاربران بر اساس امتیاز
    sorted_users = sorted(users.items(), key=lambda x: x[1]["score"], reverse=True)
    
    text = "🏆 جدول برترین‌ها:\n\n"
    for i, (uid, user) in enumerate(sorted_users[:10], 1):
        wins = sum(1 for h in user["match_history"] if "برنده شد" in h)
        losses = sum(1 for h in user["match_history"] if "باخت" in h)
        draws = sum(1 for h in user["match_history"] if "مساوی" in h)
        
        text += f"{i}. {user['team']} - امتیاز: {user['score']}\n"
        text += f"   🏆 برد: {wins} | 🏳️ باخت: {losses} | 🤝 تساوی: {draws}\n\n"
    
    bot.send_message(m.chat.id, text, reply_markup=back_menu())

# 🎁 پاداش روزانه
@bot.message_handler(func=lambda m: m.text == "🎁 پاداش روزانه")
def daily_reward_handler(m):
    uid = str(m.from_user.id)
    users = load_users()
    
    if uid not in users:
        return bot.send_message(m.chat.id, "❌ ابتدا ثبت‌نام کنید.")
    
    now = datetime.datetime.now()
    last_reward = users[uid].get("last_daily_reward")
    
    if last_reward:
        last_date = datetime.datetime.strptime(last_reward, "%Y-%m-%d").date()
        if now.date() == last_date:
            return bot.send_message(m.chat.id, "❌ امروز قبلاً پاداش دریافت کرده‌اید. فردا دوباره امتحان کنید.", reply_markup=back_menu())
    
    users[uid]["coins"] += 50
    users[uid]["last_daily_reward"] = now.strftime("%Y-%m-%d")
    save_users(users)
    
    bot.send_message(m.chat.id, "🎉 پاداش روزانه شما دریافت شد! 50 سکه به حساب شما اضافه شد.", reply_markup=back_menu())

# 🏪 فروشگاه بازیکن
@bot.message_handler(func=lambda m: m.text == "🏪 فروشگاه بازیکن")
def show_store(m):
    uid = str(m.from_user.id)
    users = load_users()
    if uid not in users:
        return bot.send_message(m.chat.id, "❌ ابتدا ثبت‌نام کن")

    text = "🏪 لیست بازیکنان قابل خرید:\n\n"
    markup = types.InlineKeyboardMarkup()
    for pid, pl in ALL_PLAYERS.items():
        if pid in users[uid]["players"]:
            continue  # قبلاً خریده

        price = f"{pl['price_gems']} جم / {pl['price_coins']} سکه"
        btn = types.InlineKeyboardButton(f"{pl['name']} ({pl['position']}) | {price}", callback_data=f"buy_{pid}")
        markup.add(btn)

    if len(markup.keyboard) == 0:
        return bot.send_message(m.chat.id, "✅ همه بازیکنان رو خریدی!", reply_markup=back_menu())

    bot.send_message(m.chat.id, text, reply_markup=markup)

# خرید بازیکن
@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def handle_buy(c):
    uid = str(c.from_user.id)
    users = load_users()
    pid = c.data.replace("buy_", "")

    if pid not in ALL_PLAYERS:
        return bot.answer_callback_query(c.id, "❌ بازیکن پیدا نشد.")

    if pid in users[uid]["players"]:
        return bot.answer_callback_query(c.id, "❗ قبلاً خریدی")

    if len(users[uid]["players"]) >= 8:
        return bot.answer_callback_query(c.id, "❗ حداکثر ۸ بازیکن مجاز است.")

    player = ALL_PLAYERS[pid]
    if users[uid]["gems"] >= player["price_gems"]:
        users[uid]["gems"] -= player["price_gems"]
    elif users[uid]["coins"] >= player["price_coins"]:
        users[uid]["coins"] -= player["price_coins"]
    else:
        return bot.answer_callback_query(c.id, "❌ سکه یا جم کافی نداری!")

    users[uid]["players"].append(pid)
    save_users(users)

    bot.answer_callback_query(c.id, "✅ خرید با موفقیت انجام شد!")
    bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    bot.send_message(c.message.chat.id, f"🎉 بازیکن {player['name']} با موفقیت به تیمت اضافه شد.", reply_markup=back_menu())

# 📋 ترکیب و تاکتیک
@bot.message_handler(func=lambda m: m.text == "📋 ترکیب و تاکتیک")
def tactic_menu(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📌 انتخاب ترکیب", "⚔️ سبک بازی")
    markup.row("🧠 تاکتیک", "🪤 تله آفساید", "🔥 پرسینگ")
    markup.row("📊 شماتیک")
    markup.row("بازگشت به منو")
    bot.send_message(m.chat.id, "⚙️ یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=markup)

# انتخاب ترکیب
@bot.message_handler(func=lambda m: m.text == "📌 انتخاب ترکیب")
def formation_handler(m):
    uid = str(m.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    formations = ["۱-۲-۲", "۱-۱-۳", "۱-۳-۱", "۱-۴"]
    for f in formations:
        markup.add(f)
    markup.add("بازگشت به منو")
    user_states[uid] = "formation"
    bot.send_message(m.chat.id, "🎯 ترکیب مورد نظر را انتخاب کن:", reply_markup=markup)

# انتخاب تاکتیک
@bot.message_handler(func=lambda m: m.text == "🧠 تاکتیک")
def mode_handler(m):
    uid = str(m.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    modes = ["هجومی", "دفاعی", "متعادل"]
    for m_ in modes:
        markup.add(m_)
    markup.add("بازگشت به منو")
    user_states[uid] = "mode"
    bot.send_message(m.chat.id, "🎯 تاکتیک مورد نظر را انتخاب کن:", reply_markup=markup)

# سبک بازی
@bot.message_handler(func=lambda m: m.text == "⚔️ سبک بازی")
def style_handler(m):
    uid = str(m.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    styles = ["پاسکاری", "بازی با وینگ", "ضدحمله"]
    for s in styles:
        markup.add(s)
    markup.add("بازگشت به منو")
    user_states[uid] = "style"
    bot.send_message(m.chat.id, "🎮 سبک بازی مورد نظر را انتخاب کن:", reply_markup=markup)

# تله آفساید
@bot.message_handler(func=lambda m: m.text == "🪤 تله آفساید")
def offside_handler(m):
    uid = str(m.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بذار", "نذار", "بازگشت به منو")
    user_states[uid] = "offside"
    bot.send_message(m.chat.id, "🪤 تله آفساید رو فعال می‌کنی؟", reply_markup=markup)

# پرسینگ
@bot.message_handler(func=lambda m: m.text == "🔥 پرسینگ")
def pressing_handler(m):
    uid = str(m.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("پرس ۱۰۰ درصد", "پرس ۵۰ درصد", "پرس نمی‌خوام")
    markup.add("بازگشت به منو")
    user_states[uid] = "press"
    bot.send_message(m.chat.id, "🔥 شدت پرسینگ را مشخص کن:", reply_markup=markup)

# ذخیره تنظیمات تاکتیکی
@bot.message_handler(func=lambda m: user_states.get(str(m.from_user.id)) in ["formation", "mode", "style", "offside", "press"])
def save_tactic(m):
    uid = str(m.from_user.id)
    field = user_states[uid]
    users = load_users()
    users[uid]["tactic"][field] = m.text
    save_users(users)
    bot.send_message(m.chat.id, f"✅ {field} ذخیره شد.", reply_markup=back_menu())
    user_states.pop(uid)

# 📊 شماتیک تیم
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
            p = ALL_PLAYERS[pid]
            lines[p["position"]].append(p["name"])

    text = f"📊 شماتیک تیم {users[uid]['team']}:\n\n"
    if lines["FW"]: text += "⚽ مهاجم: " + "  ".join(lines["FW"]) + "\n"
    if lines["MF"]: text += "🏃 هافبک: " + "  ".join(lines["MF"]) + "\n"
    if lines["DF"]: text += "🛡 مدافع: " + "  ".join(lines["DF"]) + "\n"
    if lines["GK"]: text += "🧤 دروازه‌بان: " + "  ".join(lines["GK"]) + "\n"

    bot.send_message(m.chat.id, text or "❌ ترکیب خالیه!", reply_markup=back_menu())

# 🎮 بازی شبانه: ثبت‌نام در لیست بازی
@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def join_night_game(m):
    uid = str(m.from_user.id)
    participants.add(uid)
    bot.send_message(m.chat.id, "🕘 شما در بازی شبانه امشب ثبت‌نام شدید.", reply_markup=back_menu())

# 📄 گزارش بازی
@bot.message_handler(func=lambda m: m.text == "📄 گزارش بازی")
def match_report(m):
    uid = str(m.from_user.id)
    users = load_users()
    history = users[uid].get("match_history", [])
    if not history:
        return bot.send_message(m.chat.id, "❌ هنوز هیچ بازی ثبت نشده.")
    
    report = "📄 گزارش آخرین بازی:\n\n" + history[-1]
    bot.send_message(m.chat.id, report, reply_markup=back_menu())

# شبیه‌سازی بازی شبانه
def simulate_match(user1, user2, users):
    team1 = users[user1]
    team2 = users[user2]

    score1 = team1["score"]
    score2 = team2["score"]

    # امتیاز بر اساس تاکتیک و ترکیب
    p1 = len(team1["players"]) * 5 + sum([ALL_PLAYERS[pid]["overall"] for pid in team1["players"] if pid in ALL_PLAYERS])
    p2 = len(team2["players"]) * 5 + sum([ALL_PLAYERS[pid]["overall"] for pid in team2["players"] if pid in ALL_PLAYERS])

    # تأثیر تاکتیک‌ها
    for k in ["formation", "mode", "style", "offside", "press"]:
        if team1["tactic"].get(k) == "هجومی": p1 += 10
        if team2["tactic"].get(k) == "هجومی": p2 += 10

    r1 = random.randint(0, 5)
    r2 = random.randint(0, 5)

    final1 = p1 + r1
    final2 = p2 + r2

    if final1 > final2:
        team1["score"] += 20
        team1["coins"] += 100
        team2["score"] -= 10
        team2["coins"] += 20
        result = f"🏆 {team1['team']} برنده شد!\nنتیجه: {final1} - {final2}"
    elif final1 < final2:
        team2["score"] += 20
        team2["coins"] += 100
        team1["score"] -= 10
        team1["coins"] += 20
        result = f"🏆 {team2['team']} برنده شد!\nنتیجه: {final1} - {final2}"
    else:
        team1["score"] += 5
        team2["score"] += 5
        team1["coins"] += 40
        team2["coins"] += 40
        result = f"🤝 بازی مساوی شد!\nنتیجه: {final1} - {final2}"

    users[user1]["match_history"].append(result)
    users[user2]["match_history"].append(result)

# اجرای خودکار بازی‌ها رأس ساعت ۲۲:۰۰
def run_nightly_game():
    while True:
        now = datetime.datetime.now()
        if now.hour == 8 and now.minute == 30:  # برای ۱۲ ظهر ایران
            users = load_users()
            plist = list(participants)
            random.shuffle(plist)
            for i in range(0, len(plist)-1, 2):
                simulate_match(plist[i], plist[i+1], users)
                try:
                    bot.send_message(plist[i], "🕘 بازیت شروع شد!\nبرای مشاهده نتیجه برو به 📄 گزارش بازی")
                    bot.send_message(plist[i+1], "🕘 بازیت شروع شد!\nبرای مشاهده نتیجه برو به 📄 گزارش بازی")
                except: continue
            participants.clear()
            save_users(users)
        time.sleep(60)

# 👛 کیف پول
@bot.message_handler(func=lambda m: m.text == "👛 کیف پول")
def wallet(m):
    uid = str(m.from_user.id)
    users = load_users()
    user = users[uid]
    text = f"""
💰 کیف پول شما:

🪙 سکه‌ها: {user['coins']}
💎 جم‌ها: {user['gems']}

📥 تبدیل سکه به جم: هر 100 سکه = 1 جم
🧾 ارسال فیش پرداخت (متن یا عکس)

TRX Address:
{TRON_ADDRESS}
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔄 تبدیل سکه به جم", "📤 ارسال فیش")
    markup.add("بازگشت به منو")
    bot.send_message(m.chat.id, text, reply_markup=markup)

# تبدیل سکه به جم
@bot.message_handler(func=lambda m: m.text == "🔄 تبدیل سکه به جم")
def convert_coins(m):
    uid = str(m.from_user.id)
    users = load_users()
    if users[uid]["coins"] >= 100:
        users[uid]["coins"] -= 100
        users[uid]["gems"] += 1
        save_users(users)
        bot.send_message(m.chat.id, "✅ تبدیل انجام شد!", reply_markup=back_menu())
    else:
        bot.send_message(m.chat.id, "❌ سکه کافی نداری!", reply_markup=back_menu())

# ارسال فیش
@bot.message_handler(func=lambda m: m.text == "📤 ارسال فیش")
def ask_receipt(m):
    bot.send_message(m.chat.id, "🧾 فیش پرداخت را ارسال کن (عکس یا متن):", reply_markup=back_menu())

# هندلر دریافت فیش (متن یا عکس) - فقط اگر در حالت دریافت فیش باشیم
@bot.message_handler(content_types=["text"], func=lambda m: m.reply_to_message and m.reply_to_message.text == "🧾 فیش پرداخت را ارسال کن (عکس یا متن):")
def handle_text_receipt(m):
    bot.send_message(ADMIN_ID, f"📤 فیش متنی جدید از {m.from_user.first_name}:\n{m.text}")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{m.from_user.id}"))
    markup.add(types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{m.from_user.id}"))
    bot.send_message(ADMIN_ID, f"🎯 فیش جدید برای بررسی:", reply_markup=markup)
    bot.send_message(m.chat.id, "✅ فیش شما دریافت شد و در حال بررسی است.", reply_markup=back_menu())

@bot.message_handler(content_types=["photo"], func=lambda m: m.reply_to_message and m.reply_to_message.text == "🧾 فیش پرداخت را ارسال کن (عکس یا متن):")
def handle_photo_receipt(m):
    bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{m.from_user.id}"))
    markup.add(types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{m.from_user.id}"))
    bot.send_message(ADMIN_ID, f"🎯 فیش جدید برای بررسی:", reply_markup=markup)
    bot.send_message(m.chat.id, "✅ فیش شما دریافت شد و در حال بررسی است.", reply_markup=back_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_") or c.data.startswith("reject_"))
def handle_receipt_admin(c):
    uid = c.data.split("_")[1]
    users = load_users()

    if c.data.startswith("confirm_"):
        users[uid]["coins"] += 100
        save_users(users)
        bot.send_message(int(uid), "✅ فیش تایید شد! 100 سکه به حسابت اضافه شد.")
        bot.edit_message_text("✔️ تایید شد", c.message.chat.id, c.message.message_id)
    else:
        bot.send_message(int(uid), "❌ فیش رد شد.")
        bot.edit_message_text("❌ رد شد", c.message.chat.id, c.message.message_id)

# هندلر بازگشت به منو
@bot.message_handler(func=lambda m: m.text == "بازگشت به منو")
def back_to_main(m):
    bot.send_message(m.chat.id, "منوی اصلی:", reply_markup=main_menu())

# اجرای فل ask با webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است"

def start_bot():
    threading.Thread(target=run_nightly_game).start()
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    print("ربات در حال اجراست...")
    start_bot()
