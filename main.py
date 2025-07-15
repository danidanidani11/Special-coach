import telebot
from telebot import types
import json
import os
import random
from datetime import datetime, timedelta

TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "Specialcoach1"
TRON_ADDRESS = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"

bot = telebot.TeleBot(TOKEN)
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")
ENTRANTS_FILE = os.path.join(DATA_DIR, "entrants.json")

# ---------------- Load/save users ---------------- #
def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file) as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

users = load_json(USERS_FILE)
entrants = load_json(ENTRANTS_FILE)
players = json.load(open(PLAYERS_FILE))

def save_users(u): save_json(USERS_FILE, u)
def save_entrants(e): save_json(ENTRANTS_FILE, e)

# ---------------- منو اصلی ---------------- #
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛒 فروشگاه بازیکنان", "📋 ترکیب و تاکتیک")
    markup.add("🎮 بازی شبانه", "🏆 برترین‌ها")
    markup.add("🎁 پاداش روزانه", "💰 کیف پول")
    return markup

# ---------------- /start ---------------- #
@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.from_user.id)
    # بررسی عضویت در کانال
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", msg.from_user.id)
        if member.status in ['left', 'kicked']:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}"))
            bot.send_message(msg.chat.id, "🛑 برای استفاده از ربات، ابتدا در کانال عضو شوید.", reply_markup=markup)
            return
    except:
        bot.send_message(msg.chat.id, "⚠️ کانال یافت نشد یا نام کاربری اشتباه است.")
        return

    # اگر قبلاً ثبت‌نام کرده
    if uid in users:
        bot.send_message(msg.chat.id, "👋 خوش برگشتی مربی!", reply_markup=main_menu())
        return

    # ثبت‌نام جدید
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("📱 ارسال شماره من", request_contact=True)
    markup.add(btn)
    bot.send_message(msg.chat.id, "📱 لطفاً شماره خود را ارسال کنید:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_contact(msg):
    uid = str(msg.from_user.id)
    if uid not in users:
        users[uid] = {
            "phone": msg.contact.phone_number,
            "step": "ask_team"
        }
        save_users(users)
        bot.send_message(msg.chat.id, "📛 نام تیم شما چیست؟")

@bot.message_handler(func=lambda m: True)
def get_team_name(msg):
    uid = str(msg.from_user.id)
    if uid in users and users[uid].get("step") == "ask_team":
        users[uid].update({
            "team": msg.text,
            "step": None,
            "players": [],
            "coins": 100,
            "gems": 2,
            "score": 0,
            "wins": 0,
            "games": 0,
            "tactic": {},
            "last_daily": "",
        })
        save_users(users)
        bot.send_message(msg.chat.id, f"✅ تیم {msg.text} ثبت شد!", reply_markup=main_menu())

# ---------------- فروشگاه بازیکنان ---------------- #

def get_player_price_text(p):
    return f"{p['price_gems']} جم و {p['price_coins']} سکه"

@bot.message_handler(func=lambda m: m.text == "🛒 فروشگاه بازیکنان")
def store(msg):
    uid = str(msg.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for p in players:
        markup.add(f"{p['name']} - {p['skill']} (قیمت: {get_player_price_text(p)})")
    markup.add("🔙 بازگشت به منو")
    bot.send_message(msg.chat.id, "🎯 بازیکن مورد نظر را انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text and m.text.startswith(p['name']) for p in players))
def buy_player(msg):
    uid = str(msg.from_user.id)
    for p in players:
        if msg.text.startswith(p['name']):
            user = users[uid]
            if p["id"] in [pl["id"] for pl in user["players"]]:
                bot.send_message(msg.chat.id, "❌ شما این بازیکن را قبلا خریداری کرده‌اید.")
                return
            # قیمت جم و سکه
            if user["gems"] >= p["price_gems"] and user["coins"] >= p["price_coins"]:
                if len(user["players"]) >= 8:
                    bot.send_message(msg.chat.id, "⚠️ حداکثر ۸ بازیکن می‌توانید داشته باشید.")
                    return
                user["gems"] -= p["price_gems"]
                user["coins"] -= p["price_coins"]
                user["players"].append(p)
                save_users(users)
                bot.send_message(msg.chat.id, f"🎉 بازیکن {p['name']} با موفقیت خریداری شد.")
            else:
                bot.send_message(msg.chat.id, "❌ جم یا سکه کافی ندارید.")
            return

# ---------------- ترکیب و تاکتیک ---------------- #

@bot.message_handler(func=lambda m: m.text == "📋 ترکیب و تاکتیک")
def formation_menu(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("چیدمان", "تاکتیک", "سبک بازی", "تله آفساید", "پرسینگ", "شماتیک")
    markup.add("🔙 بازگشت به منو")
    bot.send_message(msg.chat.id, "📋 بخش ترکیب و تاکتیک:", reply_markup=markup)

# چیدمان
@bot.message_handler(func=lambda m: m.text == "چیدمان")
def set_formation(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("1-2-2", "1-1-3", "1-3-1", "1-4")
    markup.add("🔙 بازگشت به منو")
    bot.send_message(msg.chat.id, "لطفا چیدمان را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["1-2-2", "1-1-3", "1-3-1", "1-4"])
def save_formation(msg):
    uid = str(msg.from_user.id)
    users[uid]["tactic"]["formation"] = msg.text
    save_users(users)
    bot.send_message(msg.chat.id, f"چیدمان {msg.text} ذخیره شد.", reply_markup=main_menu())

# تاکتیک
@bot.message_handler(func=lambda m: m.text == "تاکتیک")
def tactic_menu(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("هجومی", "دفاعی", "متعادل", "🔙 بازگشت به منو")
    bot.send_message(msg.chat.id, "تاکتیک خود را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["هجومی", "دفاعی", "متعادل"])
def save_tactic(msg):
    uid = str(msg.from_user.id)
    users[uid]["tactic"]["style"] = msg.text
    save_users(users)
    bot.send_message(msg.chat.id, f"تاکتیک {msg.text} ذخیره شد.", reply_markup=main_menu())

# سبک بازی
@bot.message_handler(func=lambda m: m.text == "سبک بازی")
def style_menu(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("پاسکاری", "بازی با وینگ", "🔙 بازگشت به منو")
    bot.send_message(msg.chat.id, "سبک بازی خود را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["پاسکاری", "بازی با وینگ"])
def save_style(msg):
    uid = str(msg.from_user.id)
    users[uid]["tactic"]["play_style"] = msg.text
    save_users(users)
    bot.send_message(msg.chat.id, f"سبک بازی {msg.text} ذخیره شد.", reply_markup=main_menu())

# تله آفساید
@bot.message_handler(func=lambda m: m.text == "تله آفساید")
def offside_menu(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بذار", "نذار", "🔙 بازگشت به منو")
    bot.send_message(msg.chat.id, "تله آفساید را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["بذار", "نذار"])
def save_offside(msg):
    uid = str(msg.from_user.id)
    users[uid]["tactic"]["offside"] = msg.text
    save_users(users)
    bot.send_message(msg.chat.id, f"تله آفساید {msg.text} ذخیره شد.", reply_markup=main_menu())

# پرسینگ
@bot.message_handler(func=lambda m: m.text == "پرسینگ")
def press_menu(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("پرس 100%", "پرس 50%", "نمی‌خوام", "🔙 بازگشت به منو")
    bot.send_message(msg.chat.id, "میزان پرسینگ را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["پرس 100%", "پرس 50%", "نمی‌خوام"])
def save_press(msg):
    uid = str(msg.from_user.id)
    users[uid]["tactic"]["press"] = msg.text
    save_users(users)
    bot.send_message(msg.chat.id, f"پرسینگ {msg.text} ذخیره شد.", reply_markup=main_menu())

# ---------------- شماتیک ---------------- #

def schematic_text(user_players, formation):
    # طبقه‌بندی بازیکنان بر اساس پست
    gk = [p for p in user_players if p['position'] == "GK"]
    df = [p for p in user_players if p['position'] == "DF"]
    mf = [p for p in user_players if p['position'] == "MF"]
    fw = [p for p in user_players if p['position'] == "FW"]

    # جایگذاری ساده بر اساس تعداد و چیدمان
    # فقط ۸ بازیکن در ترکیب داریم
    # چیدمان مثلاً 1-3-1 یعنی 1 مهاجم، 3 هافبک، 1 مدافع (این مثال ساده)

    # خط پایین دروازه‌بان
    gk_name = gk[0]['name'] if gk else "دروازه‌بان خالی"

    # آماده سازی خطوط متن
    lines = []

    # مهاجم‌ها (خط بالا)
    fwnames = [p['name'] for p in fw[:2]]
    line_fw = "    ".join(fwnames) if fwnames else "مهاجم خالی"
    lines.append(line_fw)

    # هافبک‌ها (خط وسط)
    mfnames = [p['name'] for p in mf[:2]]
    line_mf = "    ".join(mfnames) if mfnames else "هافبک خالی"
    lines.append(line_mf)

    # مدافع‌ها (خط پایین)
    dfnames = [p['name'] for p in df[:2]]
    line_df = "    ".join(dfnames) if dfnames else "مدافع خالی"
    lines.append(line_df)

    # دروازه‌بان پایین‌تر
    lines.append(f"        {gk_name}")

    return "\n".join(lines)

@bot.message_handler(func=lambda m: m.text == "شماتیک")
def show_schematic(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user:
        bot.send_message(msg.chat.id, "شما ثبت نام نکرده‌اید.")
        return
    if not user.get("players"):
        bot.send_message(msg.chat.id, "لیست بازیکنی ندارید.")
        return

    formation = user["tactic"].get("formation", "1-2-2")
    text = schematic_text(user["players"], formation)
    bot.send_message(msg.chat.id, f"📊 شماتیک ترکیب:\n\n{text}", reply_markup=main_menu())

import threading
from time import sleep

# ---------------- پاداش روزانه ---------------- #

@bot.message_handler(func=lambda m: m.text == "🎁 پاداش روزانه")
def daily_bonus(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user:
        bot.send_message(msg.chat.id, "ابتدا ثبت‌نام کنید.")
        return
    today_str = datetime.now().strftime("%Y-%m-%d")
    if user.get("last_daily") == today_str:
        bot.send_message(msg.chat.id, "✅ امروز پاداش روزانه را دریافت کرده‌اید.")
        return
    user["gems"] += 2
    user["last_daily"] = today_str
    save_users(users)
    bot.send_message(msg.chat.id, "🎉 پاداش روزانه شما: ۲ جم اضافه شد.", reply_markup=main_menu())

# ---------------- کیف پول ---------------- #

@bot.message_handler(func=lambda m: m.text == "💰 کیف پول")
def wallet_menu(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user:
        bot.send_message(msg.chat.id, "ابتدا ثبت‌نام کنید.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("تبدیل سکه به جم", "ارسال فیش خرید", "🔙 بازگشت به منو")
    bot.send_message(msg.chat.id,
                     f"💰 موجودی شما:\nجم: {user['gems']}\nسکه: {user['coins']}",
                     reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "تبدیل سکه به جم")
def convert_coins_to_gems(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if user["coins"] < 100:
        bot.send_message(msg.chat.id, "⚠️ حداقل ۱۰۰ سکه نیاز است تا تبدیل شود.")
        return
    gems_added = user["coins"] // 100 * 1
    coins_used = gems_added * 100
    user["coins"] -= coins_used
    user["gems"] += gems_added
    save_users(users)
    bot.send_message(msg.chat.id,
                     f"✅ {coins_used} سکه به {gems_added} جم تبدیل شد.",
                     reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "ارسال فیش خرید")
def send_receipt(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    markup = types.ForceReply(selective=False)
    bot.send_message(msg.chat.id,
                     f"لطفا فیش پرداخت خود را (متن یا عکس) ارسال کنید. آدرس ترون برای واریز:\n{TRON_ADDRESS}",
                     reply_markup=markup)
    user["step"] = "waiting_receipt"
    save_users(users)

@bot.message_handler(content_types=['text', 'photo'])
def receive_receipt(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user or user.get("step") != "waiting_receipt":
        return

    # فوروارد فیش به ادمین
    if msg.content_type == 'photo':
        file_id = msg.photo[-1].file_id
        bot.send_photo(ADMIN_ID, file_id,
                       caption=f"فیش پرداخت از {user['team']} (ID: {uid})")
    else:
        bot.send_message(ADMIN_ID, f"فیش پرداخت از {user['team']} (ID: {uid}):\n\n{msg.text}")

    # دکمه تایید و رد برای ادمین
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{uid}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{uid}")
    )
    bot.send_message(ADMIN_ID, "لطفا وضعیت فیش را مشخص کنید:", reply_markup=markup)

    user["step"] = None
    save_users(users)
    bot.send_message(msg.chat.id, "فیش شما دریافت شد. پس از بررسی به شما اطلاع داده می‌شود.")

# ---------------- پاسخ به تایید/رد فیش توسط ادمین ---------------- #

@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_") or c.data.startswith("reject_"))
def handle_receipt_approval(call):
    data = call.data
    uid = data.split("_")[1]
    user = users.get(uid)
    if not user:
        bot.answer_callback_query(call.id, "کاربر یافت نشد.")
        return

    if data.startswith("approve_"):
        user["coins"] += 100  # 100 سکه اضافه می‌کنیم به کاربر
        save_users(users)
        bot.edit_message_text("✅ فیش تایید شد و ۱۰۰ سکه به کاربر اضافه شد.",
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        bot.send_message(int(uid), "✅ فیش شما تایید شد و ۱۰۰ سکه به کیف پولتان اضافه گردید.", reply_markup=main_menu())
    else:
        bot.edit_message_text("❌ فیش رد شد.",
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        bot.send_message(int(uid), "❌ فیش شما رد شد. لطفا دوباره تلاش کنید.", reply_markup=main_menu())

# ---------------- بازی شبانه ---------------- #

def pair_players_randomly():
    # جفت‌سازی رندوم بازیکنان حاضر در لیست entrants
    uids = list(entrants.keys())
    random.shuffle(uids)
    pairs = []
    while len(uids) >= 2:
        p1 = uids.pop()
        p2 = uids.pop()
        pairs.append((p1, p2))
    # اگر تعداد فرد بود، آخرین نفر بدون بازی می‌ماند و به بازی بعدی می‌رود
    if uids:
        last = uids.pop()
        bot.send_message(int(last), "⚠️ شما در این دور بازی نخواهید داشت و به دور بعدی منتقل می‌شوید.")
    return pairs

def simulate_match(p1, p2):
    user1 = users[p1]
    user2 = users[p2]

    # محاسبه قدرت تیم بر اساس ترکیب و تاکتیک و بازیکنان
    power1 = sum(pl["skill"] for pl in user1["players"])
    power2 = sum(pl["skill"] for pl in user2["players"])

    # تأثیر تاکتیک (مثلا هجومی 10%، دفاعی -10% و متعادل 0)
    tactics_impact = {
        "هجومی": 1.1,
        "دفاعی": 0.9,
        "متعادل": 1.0
    }
    t1_factor = tactics_impact.get(user1["tactic"].get("style", "متعادل"), 1.0)
    t2_factor = tactics_impact.get(user2["tactic"].get("style", "متعادل"), 1.0)

    score1 = power1 * t1_factor * random.uniform(0.8, 1.2)
    score2 = power2 * t2_factor * random.uniform(0.8, 1.2)

    # تعیین نتیجه
    if abs(score1 - score2) < 10:
        result = "draw"
    elif score1 > score2:
        result = "p1_win"
    else:
        result = "p2_win"

    return result, round(score1), round(score2)

def update_user_after_match(uid, result, coins_reward, score_reward):
    user = users[uid]
    user["coins"] += coins_reward
    user["score"] += score_reward
    user["games"] += 1
    if result == "win":
        user["wins"] += 1
    elif result == "lose":
        user["wins"] += 0
    save_users(users)

def send_match_report(p1, p2, result, score1, score2):
    user1 = users[p1]
    user2 = users[p2]

    # متن گزارش
    if result == "draw":
        res_text = "⚖️ بازی مساوی شد."
        update_user_after_match(p1, "draw", 40, 5)
        update_user_after_match(p2, "draw", 40, 5)
    elif result == "p1_win":
        res_text = f"🏆 تیم {user1['team']} پیروز شد!"
        update_user_after_match(p1, "win", 100, 20)
        update_user_after_match(p2, "lose", 20, -10)
    else:
        res_text = f"🏆 تیم {user2['team']} پیروز شد!"
        update_user_after_match(p2, "win", 100, 20)
        update_user_after_match(p1, "lose", 20, -10)

    report = (f"📊 گزارش بازی شبانه:\n"
              f"{user1['team']} ({score1}) - ({score2}) {user2['team']}\n"
              f"{res_text}\n\n"
              f"🎁 جوایز:\n"
              f"🏅 امتیاز و 💰 سکه به‌روزرسانی شدند.")

    bot.send_message(int(p1), report, reply_markup=main_menu())
    bot.send_message(int(p2), report, reply_markup=main_menu())

# اضافه کردن کاربر به لیست شرکت‌کنندگان بازی شبانه

@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def join_night_game(msg):
    uid = str(msg.from_user.id)
    if uid in entrants:
        bot.send_message(msg.chat.id, "✅ شما قبلاً در بازی شبانه شرکت کرده‌اید. لطفا تا شروع بازی صبر کنید.", reply_markup=main_menu())
        return
    entrants[uid] = True
    save_entrants(entrants)
    bot.send_message(msg.chat.id, "✅ شما به لیست شرکت‌کنندگان بازی شبانه اضافه شدید.\nبازیتان رأس ساعت ۹ شب شروع می‌شود!", reply_markup=main_menu())

# تابع اجرا کننده بازی رأس ساعت ۹ شب
def game_scheduler():
    while True:
        now = datetime.now()
        # تا رسیدن به ساعت 21:00 صبر کن
        target = now.replace(hour=21, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        sleep(wait_seconds)

        # شروع بازی
        bot.send_message(ADMIN_ID, "⏰ بازی شبانه آغاز شد.")
        pairs = pair_players_randomly()

        for p1, p2 in pairs:
            result, s1, s2 = simulate_match(p1, p2)
            send_match_report(p1, p2, result, s1, s2)

        # پاک کردن لیست شرکت‌کنندگان بعد بازی
        entrants.clear()
        save_entrants(entrants)

# اجرای ترد زمان‌بندی در پس‌زمینه
threading.Thread(target=game_scheduler, daemon=True).start()

# ---------------- برترین‌ها ---------------- #

@bot.message_handler(func=lambda m: m.text == "🏆 برترین‌ها")
def show_leaderboard(msg):
    # میانگین برد و امتیاز مرتب شود
    leaderboard = []
    for uid, u in users.items():
        games = u.get("games", 0)
        wins = u.get("wins", 0)
        if games == 0:
            win_rate = 0
        else:
            win_rate = wins / games
        score = u.get("score", 0)
        leaderboard.append((uid, u["team"], win_rate, score))

    leaderboard.sort(key=lambda x: (x[2], x[3]), reverse=True)

    text = "🏆 برترین مربیان:\n\n"
    for i, (uid, team, win_rate, score) in enumerate(leaderboard[:10], 1):
        text += f"{i}- {team}: {win_rate*100:.1f}% برد - {score} امتیاز\n"

    bot.send_message(msg.chat.id, text, reply_markup=main_menu())

# ---------------- دکمه بازگشت عمومی ---------------- #
@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت به منو")
def back_to_menu(msg):
    bot.send_message(msg.chat.id, "بازگشت به منو اصلی.", reply_markup=main_menu())

# ---------------- اجرای ربات ---------------- #
print("Bot is running...")
bot.remove_webhook()
bot.infinity_polling()
