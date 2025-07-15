import telebot, json, os, time, threading, random
from telebot import types
from flask import Flask, request

# ---------- تنظیمات ----------
TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
ADMIN_ID = 5542927340
CHANNEL_ID = "@Specialcoach1"
TRON_ADDRESS = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"

# ---------- ساخت پوشه و فایل‌ها ----------
if not os.path.exists("data"):
    os.makedirs("data")

for name, default in {
    "users.json": {},
    "players.json": {},
    "night_game.json": {"players": [], "matches": {}}
}.items():
    path = f"data/{name}"
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)

# ---------- بارگذاری داده‌ها ----------
with open("data/users.json", "r") as f:
    users = json.load(f)

with open("data/players.json", "r") as f:
    players = json.load(f)

with open("data/night_game.json", "r") as f:
    night_game = json.load(f)

def save_users():
    with open("data/users.json", "w") as f:
        json.dump(users, f)

def save_night_game():
    with open("data/night_game.json", "w") as f:
        json.dump(night_game, f)

# ---------- منوی اصلی ----------
def main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🏪 فروشگاه بازیکن", "🧠 ترکیب و تاکتیک")
    m.add("🎮 بازی شبانه", "🏆 برترین‌ها")
    m.add("🎁 پاداش روزانه", "👛 کیف پول")
    return m

# ---------- استارت ----------
@bot.message_handler(commands=["start"])
def handle_start(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)

    if user and user.get("registered"):
        bot.send_message(msg.chat.id, "👋 خوش برگشتی!", reply_markup=main_menu())
        return

    users[uid] = {"step": "ask_team", "registered": False}
    save_users()
    bot.send_message(msg.chat.id, "🏷 لطفاً نام تیم خود را وارد کنید:")

# ---------- پاسخ نام تیم ----------
@bot.message_handler(func=lambda m: users.get(str(m.from_user.id), {}).get("step") == "ask_team")
def ask_contact(msg):
    uid = str(msg.from_user.id)
    users[uid]["team_name"] = msg.text
    users[uid]["step"] = "ask_contact"
    save_users()

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📱 ارسال شماره", request_contact=True))
    bot.send_message(msg.chat.id, "📞 لطفاً شماره خود را ارسال کنید:", reply_markup=kb)

# ---------- پاسخ شماره تماس ----------
@bot.message_handler(content_types=["contact"])
def check_membership(msg):
    uid = str(msg.from_user.id)
    if not users.get(uid) or users[uid]["step"] != "ask_contact":
        return

    users[uid]["phone"] = msg.contact.phone_number
    users[uid]["step"] = "check_join"
    save_users()

    btn = types.InlineKeyboardMarkup()
    btn.add(types.InlineKeyboardButton("✅ عضویت زدم", url=f"https://t.me/{CHANNEL_ID[1:]}"))
    bot.send_message(msg.chat.id, f"📢 لطفاً در کانال {CHANNEL_ID} عضو شو و بعد دکمه زیر رو بزن.", reply_markup=btn)

# ---------- بررسی عضویت ----------
@bot.callback_query_handler(func=lambda c: c.data == "joined")
def finish_register(call):
    uid = str(call.from_user.id)
    user = users.get(uid)
    if not user or user.get("registered"):
        return

    try:
        member = bot.get_chat_member(CHANNEL_ID, call.from_user.id)
        if member.status in ["member", "creator", "administrator"]:
            user["registered"] = True
            user.update({"coins": 0, "gems": 0, "players": [], "points": 0, "last_reward": 0})
            save_users()
            bot.send_message(call.message.chat.id, "🎉 ثبت‌نام با موفقیت انجام شد!", reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ هنوز عضو نشدی!")
    except:
        bot.answer_callback_query(call.id, "❌ خطا در بررسی عضویت")

# ---------- فروشگاه بازیکن ----------
@bot.message_handler(func=lambda m: m.text == "🏪 فروشگاه بازیکن")
def show_store(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user or not user.get("registered"):
        bot.send_message(msg.chat.id, "⚠️ لطفا ابتدا ثبت‌نام کنید.", reply_markup=main_menu())
        return

    text = "🧍‍♂️ لیست بازیکنان موجود برای خرید:\n\n"
    buttons = []
    for pid, p in players.items():
        if pid not in user["players"]:
            text += f"{p['name']} - پست: {p['position']} - اورال: {p['overall']} - 💎 {p['gems']} - 🪙 {p['coins']}\n"
            buttons.append(types.InlineKeyboardButton(f"خرید {p['name']}", callback_data=f"buy_{pid}"))

    if not buttons:
        bot.send_message(msg.chat.id, "🎉 همه بازیکنان را خریدی!", reply_markup=main_menu())
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(*buttons)
    bot.send_message(msg.chat.id, text, reply_markup=markup)

# ---------- هندلر خرید بازیکن ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy_player(call):
    uid = str(call.from_user.id)
    pid = call.data.split("_")[1]
    user = users.get(uid)
    player = players.get(pid)

    if not user or not user.get("registered"):
        bot.answer_callback_query(call.id, "❌ ابتدا ثبت‌نام کنید.")
        return

    if not player:
        bot.answer_callback_query(call.id, "❌ بازیکن یافت نشد.")
        return

    if pid in user["players"]:
        bot.answer_callback_query(call.id, "❌ شما این بازیکن را قبلا خریدید.")
        return

    # بررسی موجودی سکه و جم
    if user["gems"] >= player["gems"]:
        user["gems"] -= player["gems"]
    elif user["coins"] >= player["coins"]:
        user["coins"] -= player["coins"]
    else:
        bot.answer_callback_query(call.id, "❌ سکه یا جم کافی نیست!")
        return

    user["players"].append(pid)
    save_users()
    bot.answer_callback_query(call.id, f"🎉 بازیکن {player['name']} خریداری شد!")
    bot.send_message(call.message.chat.id, f"🎉 بازیکن {player['name']} با موفقیت خریداری شد.", reply_markup=main_menu())

# ---------- منوی ترکیب و تاکتیک ----------
@bot.message_handler(func=lambda m: m.text == "🧠 ترکیب و تاکتیک")
def tactic_menu(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 شماتیک", "🧱 تعیین ترکیب")
    markup.add("🎯 تاکتیک", "🎲 سبک بازی")
    markup.add("🪤 تله افساید", "🔥 پرسینگ")
    markup.add("🔙 بازگشت به منو")
    bot.send_message(msg.chat.id, "🔧 لطفا یک گزینه انتخاب کن:", reply_markup=markup)

# ---------- شماتیک ----------
@bot.message_handler(func=lambda m: m.text == "📊 شماتیک")
def show_schematic(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)

    if not user or not user.get("registered"):
        bot.send_message(msg.chat.id, "⚠️ لطفا ابتدا ثبت‌نام کنید.", reply_markup=main_menu())
        return

    # فقط 8 بازیکن از بازیکنان خریداری شده را در ترکیب نشان بده (حداکثر 8 بازیکن)
    team_players = user.get("players", [])[:8]
    if not team_players:
        bot.send_message(msg.chat.id, "🛑 هنوز هیچ بازیکنی نخریدی.", reply_markup=main_menu())
        return

    # جایگذاری بازیکنان بر اساس پست در شماتیک ساده (مثال)
    # ترتیب برای نمایش: دروازه‌بان، مدافع‌ها، هافبک‌ها، مهاجم‌ها

    GK = []
    DEF = []
    MID = []
    FWD = []

    for pid in team_players:
        p = players.get(pid)
        if not p:
            continue
        pos = p.get("position", "").lower()
        if "دروازه" in pos or "goalkeeper" in pos:
            GK.append(p["name"])
        elif "مدافع" in pos or "defender" in pos:
            DEF.append(p["name"])
        elif "هافبک" in pos or "midfielder" in pos:
            MID.append(p["name"])
        elif "مهاجم" in pos or "forward" in pos or "striker" in pos:
            FWD.append(p["name"])
        else:
            MID.append(p["name"])  # اگر پست مشخص نیست، هاپک فرض کن

    schematic_text = ""

    # یک شماتیک خیلی ساده متنی می‌سازیم:

    # مهاجم‌ها بالا
    schematic_text += "  ".join(FWD) + "\n\n"

    # هافبک‌ها
    schematic_text += "  ".join(MID) + "\n\n"

    # مدافع‌ها
    schematic_text += "  ".join(DEF) + "\n\n"

    # دروازه‌بان
    schematic_text += "  ".join(GK) + "\n"

    bot.send_message(msg.chat.id, f"📊 ترکیب تیم شما:\n\n{schematic_text}", reply_markup=main_menu())

# ---------- بازگشت به منو ----------
@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت به منو")
def back_to_menu(msg):
    bot.send_message(msg.chat.id, "👋 به منوی اصلی برگشتی.", reply_markup=main_menu())

import datetime

# ---------- پاداش روزانه ----------
@bot.message_handler(func=lambda m: m.text == "🎁 پاداش روزانه")
def daily_reward(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user or not user.get("registered"):
        bot.send_message(msg.chat.id, "⚠️ ابتدا ثبت‌نام کنید.", reply_markup=main_menu())
        return

    now = int(time.time())
    last = user.get("last_reward", 0)

    # فاصله حداقل 24 ساعت
    if now - last >= 86400:
        user["gems"] = user.get("gems", 0) + 2
        user["last_reward"] = now
        save_users()
        bot.send_message(msg.chat.id, "🎉 امروز ۲ جم دریافت کردی!", reply_markup=main_menu())
    else:
        bot.send_message(msg.chat.id, "⏳ پاداش روزانه را قبلاً گرفتی، فردا بیا!", reply_markup=main_menu())

# ---------- بازی شبانه - ثبت نام ----------
@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def join_night_game(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user or not user.get("registered"):
        bot.send_message(msg.chat.id, "⚠️ ابتدا ثبت‌نام کنید.", reply_markup=main_menu())
        return

    if uid in night_game["players"]:
        bot.send_message(msg.chat.id, "✅ شما قبلا در بازی شبانه ثبت نام کردی، منتظر حریف باش.", reply_markup=main_menu())
        return

    night_game["players"].append(uid)
    save_night_game()
    bot.send_message(msg.chat.id, "✅ تو به لیست بازی شبانه اضافه شدی! ساعت ۹ شب بازی شروع می‌شود.", reply_markup=main_menu())

# ---------- اجرای بازی شبانه (وظیفه در بک‌گراند با threading) ----------
def night_game_runner():
    while True:
        now = datetime.datetime.now()
        # ساعت 21:00
        if now.hour == 21 and now.minute == 0:
            players_list = night_game.get("players", [])
            random.shuffle(players_list)
            matches = {}

            # جفت‌سازی بازیکنان
            for i in range(0, len(players_list)-1, 2):
                p1 = players_list[i]
                p2 = players_list[i+1]
                matches[f"{p1}_{p2}"] = {"p1": p1, "p2": p2, "result": None}

            night_game["matches"] = matches
            night_game["players"] = []
            save_night_game()

            # بازی و گزارش
            for key, match in matches.items():
                # بازی ساده با استفاده از امتیاز بازیکنان و تاکتیک (ایده ساده)
                u1 = users.get(match["p1"])
                u2 = users.get(match["p2"])
                if not u1 or not u2:
                    continue

                # امتیاز کل تیم (ساده سازی)
                score1 = len(u1.get("players", [])) + u1.get("points", 0)
                score2 = len(u2.get("players", [])) + u2.get("points", 0)

                # نتیجه بازی
                if score1 > score2:
                    winner = match["p1"]
                    loser = match["p2"]
                    match["result"] = "win"
                elif score2 > score1:
                    winner = match["p2"]
                    loser = match["p1"]
                    match["result"] = "lose"
                else:
                    winner = None
                    match["result"] = "draw"

                # اعمال امتیاز و سکه
                if winner:
                    users[winner]["points"] = users[winner].get("points", 0) + 20
                    users[winner]["coins"] = users[winner].get("coins", 0) + 100

                    users[loser]["points"] = users[loser].get("points", 0) - 10
                    users[loser]["coins"] = users[loser].get("coins", 0) + 20
                else:  # مساوی
                    users[match["p1"]]["points"] = users[match["p1"]].get("points", 0) + 5
                    users[match["p2"]]["points"] = users[match["p2"]].get("points", 0) + 5
                    users[match["p1"]]["coins"] = users[match["p1"]].get("coins", 0) + 40
                    users[match["p2"]]["coins"] = users[match["p2"]].get("coins", 0) + 40

            save_users()
            save_night_game()

            # ارسال پیام به بازیکنان
            for key, match in matches.items():
                p1 = match["p1"]
                p2 = match["p2"]
                result = match["result"]

                msg1 = "🔔 بازی شما شروع و پایان یافت!\n"
                msg2 = "🔔 بازی شما شروع و پایان یافت!\n"

                if result == "win":
                    msg1 += "🎉 شما برنده شدید! +20 امتیاز و 100 سکه"
                    msg2 += "😞 شما باختید! -10 امتیاز و 20 سکه"
                elif result == "lose":
                    msg1 += "😞 شما باختید! -10 امتیاز و 20 سکه"
                    msg2 += "🎉 شما برنده شدید! +20 امتیاز و 100 سکه"
                else:
                    msg1 += "🤝 بازی مساوی شد! +5 امتیاز و 40 سکه"
                    msg2 += "🤝 بازی مساوی شد! +5 امتیاز و 40 سکه"

                try:
                    bot.send_message(int(p1), msg1, reply_markup=main_menu())
                    bot.send_message(int(p2), msg2, reply_markup=main_menu())
                except:
                    pass

        time.sleep(60)

# ---------- شروع ترد بازی شبانه ----------
threading.Thread(target=night_game_runner, daemon=True).start()

# ---------- برترین‌ها ----------
@bot.message_handler(func=lambda m: m.text == "🏆 برترین‌ها")
def show_top_players(msg):
    sorted_users = sorted(users.items(), key=lambda x: (x[1].get("points", 0)), reverse=True)
    text = "🏆 برترین‌ها بر اساس امتیاز:\n\n"
    for i, (uid, user) in enumerate(sorted_users[:10], 1):
        wins = user.get("wins", 0)
        points = user.get("points", 0)
        text += f"{i}. {user.get('team_name','کاربر')} - {points} امتیاز\n"
    bot.send_message(msg.chat.id, text, reply_markup=main_menu())

# ---------- کیف پول ----------
@bot.message_handler(func=lambda m: m.text == "👛 کیف پول")
def wallet(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user or not user.get("registered"):
        bot.send_message(msg.chat.id, "⚠️ ابتدا ثبت‌نام کنید.", reply_markup=main_menu())
        return
    coins = user.get("coins", 0)
    gems = user.get("gems", 0)
    text = f"👛 کیف پول شما:\n\n🪙 سکه: {coins}\n💎 جم: {gems}\n\nآدرس ترون:\n`{TRON_ADDRESS}`"
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

# ---------- تبدیل سکه به جم ----------
@bot.message_handler(func=lambda m: m.text == "تبدیل سکه به جم")
def convert_coins_to_gems(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user or not user.get("registered"):
        bot.send_message(msg.chat.id, "⚠️ ابتدا ثبت‌نام کنید.", reply_markup=main_menu())
        return

    coins = user.get("coins", 0)
    if coins < 100:
        bot.send_message(msg.chat.id, "⚠️ حداقل 100 سکه نیاز است.", reply_markup=main_menu())
        return

    user["coins"] -= 100
    user["gems"] = user.get("gems", 0) + 1
    save_users()
    bot.send_message(msg.chat.id, "🎉 تبدیل موفق! 100 سکه به 1 جم تبدیل شد.", reply_markup=main_menu())

# ---------- ارسال فیش ----------
@bot.message_handler(func=lambda m: m.text == "ارسال فیش")
def send_receipt(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user or not user.get("registered"):
        bot.send_message(msg.chat.id, "⚠️ ابتدا ثبت‌نام کنید.", reply_markup=main_menu())
        return

    bot.send_message(msg.chat.id, "📤 لطفا فیش پرداختی خود را (عکس یا متن) ارسال کنید:")
    users[uid]["step"] = "waiting_receipt"
    save_users()

@bot.message_handler(content_types=["photo", "text"])
def receive_receipt(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)

    if not user or user.get("step") != "waiting_receipt":
        return

    # ارسال فیش به ادمین با دکمه‌های تایید و رد
    if msg.content_type == "photo":
        file_id = msg.photo[-1].file_id
        bot.send_photo(ADMIN_ID, file_id, caption=f"💰 فیش از {user.get('team_name')} (id: {uid})")
    else:
        bot.send_message(ADMIN_ID, f"💰 فیش از {user.get('team_name')} (id: {uid}):\n{msg.text}")

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{uid}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{uid}")
    )
    bot.send_message(ADMIN_ID, "عملیات مورد نظر را انتخاب کنید:", reply_markup=markup)

    user["step"] = None
    save_users()
    bot.send_message(msg.chat.id, "⏳ فیش شما برای بررسی ارسال شد.", reply_markup=main_menu())

# ---------- تایید یا رد فیش توسط ادمین ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_") or c.data.startswith("reject_"))
def handle_receipt_confirm(call):
    data = call.data
    if data.startswith("confirm_"):
        uid = data.split("_")[1]
        user = users.get(uid)
        if user:
            user["coins"] = user.get("coins", 0) + 100  # ۱۰۰ سکه اضافه کن
            save_users()
            bot.edit_message_text("✅ فیش تایید شد و ۱۰۰ سکه به کاربر اضافه شد.", call.message.chat.id, call.message.message_id)
            bot.send_message(int(uid), "🎉 فیش شما تایید شد و ۱۰۰ سکه به حساب شما اضافه شد.", reply_markup=main_menu())
    elif data.startswith("reject_"):
        uid = data.split("_")[1]
        bot.edit_message_text("❌ فیش رد شد.", call.message.chat.id, call.message.message_id)
        bot.send_message(int(uid), "❌ فیش شما رد شد.", reply_markup=main_menu())

# ---------- وبهوک ----------
@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    json_update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([json_update])
    return {"ok": True}

# ---------- شروع ربات ----------
if __name__ == "__main__":
    # فلکسی یا پولینگ رو فقط یکی فعال باشه؛ اینجا فرض بر وبهوک هست
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
