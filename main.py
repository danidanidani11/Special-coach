import telebot
from telebot import types
from flask import Flask, request
import threading
import json
import datetime
import random
import time
from datetime import date

# ==== تنظیمات و متغیرها ====
TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "@Specialcoach1"
TRON_ADDRESS = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"
WEBHOOK_URL = "https://special-coach.onrender.com/" + TOKEN

USERS_FILE = "data/users.json"
PLAYERS_FILE = "data/players.json"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ==== توابع کمکی ذخیره/بارگذاری داده ====
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==== چک عضویت در کانال ====
def check_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

# ==== منوی اصلی ====
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 ترکیب و تاکتیک", "🎮 بازی شبانه")
    markup.row("🏪 فروشگاه", "👛 کیف پول")
    markup.row("🎁 پاداش روزانه", "🏆 برترین‌ها")
    return markup

# ==== هندلر /start و ثبت‌نام مرحله‌ای ====

user_states = {}  # ذخیره وضعیت ثبت‌نام کاربر (step: 0=عضویت،1=نام تیم،2=شماره تماس،3=ثبت‌نام کامل)

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    users = load_users()
    user_id_str = str(user_id)

    if user_id_str in users:
        # کاربر قبلا ثبت‌نام کرده، منو اصلی
        bot.send_message(message.chat.id, "خوش آمدی دوباره به ربات مربی‌گری فوتبال!", reply_markup=main_menu())
        user_states[user_id_str] = 3
        return

    # مرحله عضویت اجباری
    user_states[user_id_str] = 0
    ask_membership(message)

def ask_membership(message):
    user_id_str = str(message.from_user.id)
    if check_membership(message.from_user.id):
        user_states[user_id_str] = 1
        bot.send_message(message.chat.id, "✅ عضویت شما در کانال تایید شد.\nلطفا نام تیم خود را وارد کنید:", reply_markup=types.ReplyKeyboardRemove())
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("عضو شدم ✅", callback_data="check_join"))
        markup.add(types.InlineKeyboardButton("عضویت در کانال 📢", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
        bot.send_message(message.chat.id, "برای ادامه ثبت‌نام لطفا ابتدا عضو کانال ما شوید.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    user_id_str = str(call.from_user.id)
    if check_membership(call.from_user.id):
        user_states[user_id_str] = 1
        bot.answer_callback_query(call.id, "عضویت شما تایید شد.")
        bot.send_message(call.message.chat.id, "✅ عضویت تایید شد.\nلطفا نام تیم خود را وارد کنید:", reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.answer_callback_query(call.id, "شما هنوز عضو کانال نیستید!")

@bot.message_handler(func=lambda m: user_states.get(str(m.from_user.id)) == 1)
def ask_team_name(message):
    user_id_str = str(message.from_user.id)
    team_name = message.text.strip()
    if len(team_name) < 3:
        bot.send_message(message.chat.id, "نام تیم باید حداقل ۳ کاراکتر باشد.")
        return
    users = load_users()
    users[user_id_str] = {
        "team_name": team_name,
        "phone": None,
        "players": [],
        "gems": 0,
        "coins": 0,
        "score": 0,
        "tactic": {},
        "match_history": [],
        "last_reward": None
    }
    save_users(users)
    user_states[user_id_str] = 2
    # درخواست شماره تماس با دکمه share contact
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("ارسال شماره تماس", request_contact=True))
    bot.send_message(message.chat.id, "لطفا شماره تماس خود را ارسال کنید (با دکمه زیر):", reply_markup=markup)

@bot.message_handler(content_types=["contact"])
def receive_contact(message):
    user_id_str = str(message.from_user.id)
    if user_states.get(user_id_str) != 2:
        return
    if message.contact is None or message.contact.user_id != message.from_user.id:
        bot.send_message(message.chat.id, "لطفا فقط شماره تماس خود را ارسال کنید.")
        return

    users = load_users()
    if user_id_str not in users:
        bot.send_message(message.chat.id, "ابتدا نام تیم را وارد کنید.")
        return

    users[user_id_str]["phone"] = message.contact.phone_number
    # افزودن ۵ بازیکن اولیه ضعیف به تیم
    for i in range(1, 6):
        users[user_id_str]["players"].append(f"player{i}")

    save_users(users)
    user_states[user_id_str] = 3
    bot.send_message(message.chat.id, "✅ ثبت‌نام کامل شد! به منوی اصلی خوش آمدید.", reply_markup=main_menu())

# در این مرحله اجازه نمی‌دهیم منو اصلی دیده شود تا ثبت‌نام کامل شود.

# سایر هندلرها و منوها در بخش‌های بعدی خواهند آمد.

# ==== وبهوک فلَسک ====
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_update = request.get_json(force=True)
    update = telebot.types.Update.de_json(json_update)
    bot.process_new_updates([update])
    return "", 200

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# ==== اجرای وبهوک ====
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("ربات در حال اجراست...")

    while True:
        time.sleep(10)

# ===== بخش ۲ از ۵ =====
# فروشگاه بازیکنان و ترکیب، تاکتیک، سبک بازی، پرسینگ و تله آفساید

# بارگذاری بازیکنان از فایل
def load_players():
    try:
        with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# نمایش فروشگاه
@bot.message_handler(func=lambda msg: msg.text == "🏪 فروشگاه")
def show_store(message):
    user_id = str(message.from_user.id)
    users = load_users()
    players = load_players()

    if user_id not in users:
        bot.send_message(message.chat.id, "❌ لطفا ابتدا ثبت‌نام کنید.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    for p in players:
        # قیمت با توجه به جم یا سکه
        name = p.get("name", "ناشناخته")
        pos = p.get("position", "")
        price_gems = p.get("price_gems", 0)
        price_coins = p.get("price_coins", 0)
        overall = p.get("overall", 0)

        text = f"{name} ({pos}) - توانایی: {overall}\n"
        if price_gems > 0:
            text += f"قیمت: {price_gems} جم"
        else:
            text += f"قیمت: {price_coins} سکه"

        markup.add(types.InlineKeyboardButton(text=text, callback_data=f"buy_{name}"))

    bot.send_message(message.chat.id, "🏪 فروشگاه بازیکنان:\nبرای خرید روی بازیکن مورد نظر بزنید.", reply_markup=markup)

# خرید بازیکن
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_player(call):
    user_id = str(call.from_user.id)
    player_name = call.data[4:]
    users = load_users()
    players = load_players()

    if user_id not in users:
        bot.answer_callback_query(call.id, "❌ لطفا ابتدا ثبت‌نام کنید.")
        return

    user = users[user_id]
    owned = user.get("players", [])
    if len(owned) >= 8:
        bot.answer_callback_query(call.id, "❌ شما حداکثر ۸ بازیکن می‌توانید داشته باشید.")
        return

    for p in players:
        if p.get("name") == player_name:
            price_gems = p.get("price_gems", 0)
            price_coins = p.get("price_coins", 0)
            break
    else:
        bot.answer_callback_query(call.id, "❌ بازیکن پیدا نشد.")
        return

    # بررسی موجودی و خرید
    if price_gems > 0:
        if user.get("gems", 0) >= price_gems:
            user["gems"] -= price_gems
        else:
            bot.answer_callback_query(call.id, "❌ جم کافی ندارید.")
            return
    else:
        if user.get("coins", 0) >= price_coins:
            user["coins"] -= price_coins
        else:
            bot.answer_callback_query(call.id, "❌ سکه کافی ندارید.")
            return

    # اضافه کردن بازیکن به تیم
    if player_name in owned:
        bot.answer_callback_query(call.id, "❌ شما این بازیکن را قبلاً خریداری کرده‌اید.")
        return

    owned.append(player_name)
    user["players"] = owned
    save_users(users)
    bot.answer_callback_query(call.id, f"✅ بازیکن {player_name} با موفقیت خریداری شد.")

# ترکیب و تاکتیک
@bot.message_handler(func=lambda msg: msg.text == "📋 ترکیب و تاکتیک")
def formation_tactics(message):
    user_id = str(message.from_user.id)
    users = load_users()

    if user_id not in users:
        bot.send_message(message.chat.id, "❌ لطفا ابتدا ثبت‌نام کنید.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("۱-۲-۲", "۱-۱-۳", "۱-۳-۱", "۱-۴")
    markup.row("⚔️ هجومی", "🛡️ دفاعی", "⚖️ متعادل")
    markup.row("🔁 پاسکاری", "🎯 بازی با وینگ")
    markup.row("تله آفساید: بذار", "تله آفساید: نذار")
    markup.row("پرس ۱۰۰ درصد", "پرس ۵۰ درصد", "پرس نمی‌خوام")
    markup.row("بازگشت به منو")

    bot.send_message(message.chat.id, "لطفا چیدمان (فرمیشن) و تاکتیک، سبک بازی، تله آفساید و پرسینگ را به ترتیب انتخاب کنید.\n(مثال: اول روی چیدمان کلیک کنید، سپس تاکتیک و...)", reply_markup=markup)

# ذخیره تاکتیک‌ها و ترکیب با چند هندلر جدا (نمونه ساده)
@bot.message_handler(func=lambda msg: msg.text in ["۱-۲-۲", "۱-۱-۳", "۱-۳-۱", "۱-۴"])
def save_formation(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        bot.send_message(message.chat.id, "❌ لطفا ابتدا ثبت‌نام کنید.")
        return
    users[user_id]["tactic"] = users[user_id].get("tactic", {})
    users[user_id]["tactic"]["formation"] = message.text
    save_users(users)
    bot.send_message(message.chat.id, f"چیدمان ذخیره شد: {message.text}")

@bot.message_handler(func=lambda msg: msg.text in ["⚔️ هجومی", "🛡️ دفاعی", "⚖️ متعادل"])
def save_style(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        return
    users[user_id]["tactic"] = users[user_id].get("tactic", {})
    users[user_id]["tactic"]["style"] = message.text
    save_users(users)
    bot.send_message(message.chat.id, f"تاکتیک ذخیره شد: {message.text}")

@bot.message_handler(func=lambda msg: msg.text in ["🔁 پاسکاری", "🎯 بازی با وینگ"])
def save_playstyle(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        return
    users[user_id]["tactic"] = users[user_id].get("tactic", {})
    users[user_id]["tactic"]["playstyle"] = message.text
    save_users(users)
    bot.send_message(message.chat.id, f"سبک بازی ذخیره شد: {message.text}")

@bot.message_handler(func=lambda msg: msg.text in ["تله آفساید: بذار", "تله آفساید: نذار"])
def save_offside_trap(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        return
    users[user_id]["tactic"] = users[user_id].get("tactic", {})
    val = "فعال" if "بذار" in message.text else "غیرفعال"
    users[user_id]["tactic"]["offside_trap"] = f"📛 {val}"
    save_users(users)
    bot.send_message(message.chat.id, f"تله آفساید تنظیم شد: {val}")

@bot.message_handler(func=lambda msg: msg.text in ["پرس ۱۰۰ درصد", "پرس ۵۰ درصد", "پرس نمی‌خوام"])
def save_pressing(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        return
    users[user_id]["tactic"] = users[user_id].get("tactic", {})
    users[user_id]["tactic"]["pressing"] = message.text
    save_users(users)
    bot.send_message(message.chat.id, f"پرسینگ ذخیره شد: {message.text}")

# شماتیک خودکار ترکیب بر اساس پست بازیکنان
@bot.message_handler(func=lambda msg: msg.text == "نمایش شماتیک")
def show_schematic(message):
    user_id = str(message.from_user.id)
    users = load_users()
    players = load_players()
    if user_id not in users:
        bot.send_message(message.chat.id, "❌ ابتدا ثبت‌نام کنید.")
        return

    user = users[user_id]
    team_players = user.get("players", [])
    # بازیکنان را با پست مرتب کن
    pos_map = {"GK": [], "DF": [], "MF": [], "FW": []}
    player_info = {p["name"]: p for p in players}
    for pl in team_players:
        info = player_info.get(pl)
        if info:
            pos_map.get(info.get("position",""), []).append(info["name"])

    # ساخت متن شماتیک ساده
    text = ""
    # دروازه‌بان
    if pos_map["GK"]:
        text += f"دروازه‌بان:\n  {pos_map['GK'][0]}\n\n"
    # مدافع‌ها
    if pos_map["DF"]:
        text += "مدافعان:\n"
        text += "  " + " - ".join(pos_map["DF"]) + "\n\n"
    # هافبک‌ها
    if pos_map["MF"]:
        text += "هافبک‌ها:\n"
        text += "  " + " - ".join(pos_map["MF"]) + "\n\n"
    # مهاجمان
    if pos_map["FW"]:
        text += "مهاجمان:\n"
        text += "  " + " - ".join(pos_map["FW"]) + "\n\n"

    bot.send_message(message.chat.id, text or "تیمی ندارید.")

# ===== بخش ۳ از ۵ =====
# بازی شبانه دو نفره، اجرای منطقی، گزارش بازی، برترین‌ها

def simulate_match(user1, user2, users_data, players_data):
    # الگوریتم ساده ولی منطقی بر اساس تعداد بازیکن و تاکتیک و امتیاز کل
    # جمع امتیاز تیم‌ها (مثلاً امتیاز کاربر + مجموع overall بازیکنان)
    def team_strength(user):
        strength = user.get("score", 0)
        players_names = user.get("players", [])
        total_overall = 0
        for pname in players_names:
            for p in players_data:
                if p["name"] == pname:
                    total_overall += p.get("overall", 0)
        strength += total_overall
        # تاکتیک‌ها می‌تواند ضریب بدهد (این بخش ساده است)
        tactic = user.get("tactic", {})
        style = tactic.get("style", "")
        if "هجومی" in style:
            strength *= 1.1
        elif "دفاعی" in style:
            strength *= 0.9
        return strength

    strength1 = team_strength(user1)
    strength2 = team_strength(user2)

    # افزودن کمی رندوم
    strength1 *= random.uniform(0.8, 1.2)
    strength2 *= random.uniform(0.8, 1.2)

    # تعیین نتیجه
    if abs(strength1 - strength2) < 10:
        result = "draw"
    elif strength1 > strength2:
        result = "user1"
    else:
        result = "user2"

    return result

# اجرای بازی شبانه هر روز ساعت 21
def run_nightly_game():
    while True:
        now = datetime.datetime.now()
        if now.hour == 21 and now.minute == 0:
            users = load_users()
            players = load_players()

            # لیست شرکت‌کنندگان که حداقل ۸ بازیکن دارند
            active_users = [uid for uid, u in users.items() if len(u.get("players", [])) >= 8]

            # جفت‌های تصادفی برای بازی (اگر تعداد فرد بود آخرین نفر بازی نمی‌کند)
            random.shuffle(active_users)
            pairs = [active_users[i:i+2] for i in range(0, len(active_users)-1, 2)]

            for pair in pairs:
                u1, u2 = pair
                user1 = users[u1]
                user2 = users[u2]

                winner = simulate_match(user1, user2, users, players)
                # بروزرسانی امتیاز و سکه
                if winner == "draw":
                    user1["score"] += 5
                    user1["coins"] = user1.get("coins", 0) + 40
                    user2["score"] += 5
                    user2["coins"] = user2.get("coins", 0) + 40
                    result_text = f"⚽ بازی مساوی شد بین {user1['team_name']} و {user2['team_name']}."
                elif winner == "user1":
                    user1["score"] += 20
                    user1["coins"] = user1.get("coins", 0) + 100
                    user2["score"] -= 10
                    user2["coins"] = max(user2.get("coins", 0) - 20, 0)
                    result_text = f"🏆 تیم {user1['team_name']} برنده بازی مقابل {user2['team_name']} شد!"
                else:
                    user2["score"] += 20
                    user2["coins"] = user2.get("coins", 0) + 100
                    user1["score"] -= 10
                    user1["coins"] = max(user1.get("coins", 0) - 20, 0)
                    result_text = f"🏆 تیم {user2['team_name']} برنده بازی مقابل {user1['team_name']} شد!"

                # ذخیره گزارش بازی
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                report = {
                    "time": now_str,
                    "player1": user1["team_name"],
                    "player2": user2["team_name"],
                    "result": result_text
                }
                user1.setdefault("match_history", []).append(report)
                user2.setdefault("match_history", []).append(report)

                # ارسال پیام گزارش به هر دو بازیکن
                try:
                    bot.send_message(int(u1), f"🎮 بازی شبانه:\n{result_text}")
                    bot.send_message(int(u2), f"🎮 بازی شبانه:\n{result_text}")
                except Exception:
                    pass

            save_users(users)
            print("بازی شبانه اجرا شد.")
            time.sleep(60)
        time.sleep(20)

# هندلر بازی شبانه - ثبت نام در لیست شرکت‌کنندگان
active_game_players = set()

@bot.message_handler(func=lambda msg: msg.text == "🎮 بازی شبانه")
def join_nightly_game(message):
    user_id_str = str(message.from_user.id)
    users = load_users()
    if user_id_str not in users:
        bot.send_message(message.chat.id, "❌ لطفا ابتدا ثبت‌نام کنید.")
        return

    active_game_players.add(user_id_str)
    bot.send_message(message.chat.id, "✅ شما به لیست بازی شبانه اضافه شدید.\nبازی رأس ساعت ۲۱ اجرا می‌شود.\nبرای مشاهده گزارش بازی‌ها، روی '📄 گزارش بازی' کلیک کنید.", reply_markup=main_menu())

# گزارش بازی‌ها
@bot.message_handler(func=lambda msg: msg.text == "📄 گزارش بازی")
def show_match_report(message):
    user_id_str = str(message.from_user.id)
    users = load_users()
    if user_id_str not in users:
        bot.send_message(message.chat.id, "❌ ابتدا ثبت‌نام کنید.")
        return

    history = users[user_id_str].get("match_history", [])
    if not history:
        bot.send_message(message.chat.id, "شما هنوز بازی انجام نداده‌اید.")
        return

    text = "📄 گزارش بازی‌های شما:\n"
    for rep in history[-10:]:
        text += f"{rep['time']}:\n{rep['result']}\n\n"

    bot.send_message(message.chat.id, text)

# برترین‌ها بر اساس درصد برد
@bot.message_handler(func=lambda msg: msg.text == "🏆 برترین‌ها")
def show_top_players(message):
    users = load_users()
    ranking = []
    for uid, u in users.items():
        matches = u.get("match_history", [])
        wins = 0
        total = 0
        for m in matches:
            if f"برنده" in m["result"] and u["team_name"] in m["result"]:
                wins += 1
            total += 1
        percent = (wins / total * 100) if total > 0 else 0
        ranking.append((percent, u.get("score", 0), u["team_name"]))

    ranking.sort(key=lambda x: (-x[0], -x[1]))
    text = "🏆 برترین تیم‌ها:\n"
    for i, (percent, score, team) in enumerate(ranking[:10], 1):
        text += f"{i}- {team}: {percent:.1f}% برد - {score} امتیاز\n"

    bot.send_message(message.chat.id, text)

# ===== بخش ۴ از ۵ =====
# کیف پول، تبدیل سکه به جم، ارسال فیش پرداختی و تأیید توسط ادمین

# نمایش کیف پول
@bot.message_handler(func=lambda msg: msg.text == "👛 کیف پول")
def wallet(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        bot.send_message(message.chat.id, "❌ ابتدا ثبت‌نام کنید.")
        return

    user = users[user_id]
    gems = user.get("gems", 0)
    coins = user.get("coins", 0)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💎 تبدیل ۱۰۰ سکه به ۱ جم", callback_data="convert_coins"))
    markup.add(types.InlineKeyboardButton("📤 ارسال فیش پرداخت", callback_data="send_receipt"))
    bot.send_message(
        message.chat.id,
        f"👛 کیف پول شما:\n💎 جم: {gems}\n🪙 سکه: {coins}\n\n🔄 هر ۱۰۰ سکه = ۱ جم\n💳 آدرس ترون برای پرداخت:\n{TRON_ADDRESS}",
        reply_markup=markup
    )

# تبدیل سکه به جم
@bot.callback_query_handler(func=lambda call: call.data == "convert_coins")
def convert_coins(call):
    user_id = str(call.from_user.id)
    users = load_users()
    user = users.get(user_id)
    if not user:
        bot.answer_callback_query(call.id, "❌ ابتدا ثبت‌نام کنید.")
        return

    if user.get("coins", 0) >= 100:
        user["coins"] -= 100
        user["gems"] += 1
        save_users(users)
        bot.answer_callback_query(call.id, "✅ ۱۰۰ سکه به ۱ جم تبدیل شد.")
        bot.edit_message_text(
            f"✅ تبدیل موفق.\nجم جدید: {user['gems']} | سکه جدید: {user['coins']}",
            chat_id=call.message.chat.id, message_id=call.message.message_id
        )
    else:
        bot.answer_callback_query(call.id, "❌ سکه کافی ندارید.")

# ارسال فیش (تصویر یا متن)
@bot.callback_query_handler(func=lambda call: call.data == "send_receipt")
def request_receipt(call):
    bot.send_message(call.message.chat.id, "🧾 لطفاً فیش پرداخت خود را (به صورت عکس یا متن) ارسال کنید.")
    user_states[str(call.from_user.id)] = "awaiting_receipt"

@bot.message_handler(func=lambda m: user_states.get(str(m.from_user.id)) == "awaiting_receipt", content_types=["text", "photo"])
def handle_receipt(message):
    user_id = str(message.from_user.id)
    user_states[user_id] = 3  # بازگشت به حالت عادی

    caption = f"📥 فیش جدید از کاربر [{message.from_user.first_name}](tg://user?id={user_id})"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}")
    )

    if message.content_type == "photo":
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(ADMIN_ID, caption + f"\n\n📝 متن فیش:\n{message.text}", parse_mode="Markdown", reply_markup=markup)

    bot.send_message(message.chat.id, "✅ فیش شما ارسال شد و در انتظار تایید ادمین است.")

# تایید یا رد فیش توسط ادمین
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin_receipt_response(call):
    user_id = call.data.split("_")[1]
    users = load_users()

    if call.data.startswith("approve_"):
        users[user_id]["coins"] += 100
        save_users(users)
        bot.send_message(int(user_id), "✅ فیش شما تایید شد و ۱۰۰ سکه به کیف پول‌تان اضافه شد.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, f"✅ فیش تایید شد و برای {user_id} ۱۰۰ سکه واریز شد.")
    else:
        bot.send_message(int(user_id), "❌ فیش شما توسط ادمین رد شد. لطفا مجدد تلاش کنید.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, f"❌ فیش کاربر {user_id} رد شد.")

# ===== بخش ۵ از ۵ =====
# پاداش روزانه، بازگشت به منو، عضویت اجباری، ذخیره‌سازی و Flask

# دریافت پاداش روزانه (۲ جم در روز)
@bot.message_handler(func=lambda msg: msg.text == "🎁 پاداش روزانه")
def daily_reward(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        bot.send_message(message.chat.id, "❌ ابتدا ثبت‌نام کنید.")
        return

    last = users[user_id].get("last_reward", "")
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    if last == today:
        bot.send_message(message.chat.id, "❌ شما امروز پاداش گرفته‌اید. فردا دوباره امتحان کنید.")
        return

    users[user_id]["gems"] = users[user_id].get("gems", 0) + 2
    users[user_id]["last_reward"] = today
    save_users(users)
    bot.send_message(message.chat.id, "✅ ۲ جم به عنوان پاداش روزانه دریافت کردید!")

# دکمه بازگشت به منو
@bot.message_handler(func=lambda msg: msg.text == "بازگشت به منو")
def back_to_menu(message):
    bot.send_message(message.chat.id, "بازگشت به منوی اصلی:", reply_markup=main_menu())

# بررسی عضویت اجباری
def is_member(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ["member", "administrator", "creator"]
    except Exception:
        return False

# بررسی عضویت هنگام استارت
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)
    users = load_users()

    if user_id in users:
        bot.send_message(message.chat.id, "👋 خوش آمدید!", reply_markup=main_menu())
        return

    if not is_member(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("عضو شدم ✅", callback_data="check_join"))
        bot.send_message(message.chat.id, "📢 برای استفاده از ربات ابتدا در کانال عضو شوید:", reply_markup=markup)
        return

    msg = bot.send_message(message.chat.id, "🏟️ نام تیم خود را وارد کنید:")
    user_states[user_id] = "awaiting_team"

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_channel(call):
    if is_member(call.from_user.id):
        bot.send_message(call.message.chat.id, "✅ عضویت تایید شد.\n🏟️ حالا نام تیم خود را وارد کنید:")
        user_states[str(call.from_user.id)] = "awaiting_team"
    else:
        bot.send_message(call.message.chat.id, "❌ هنوز عضو نیستید.")

# ثبت‌نام مرحله دوم: دریافت نام تیم
@bot.message_handler(func=lambda m: user_states.get(str(m.from_user.id)) == "awaiting_team")
def get_team_name(message):
    user_id = str(message.from_user.id)
    team_name = message.text.strip()
    user_states[user_id] = "awaiting_contact"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("📱 ارسال شماره", request_contact=True)
    markup.add(btn)
    bot.send_message(message.chat.id, f"✅ تیم شما: {team_name}\nاکنون لطفا شماره موبایل خود را ارسال کنید:", reply_markup=markup)
    # ذخیره موقت
    user_states[f"{user_id}_team"] = team_name

# مرحله سوم: دریافت شماره تماس
@bot.message_handler(content_types=["contact"])
def get_contact(message):
    if not message.contact:
        return

    user_id = str(message.from_user.id)
    team_name = user_states.get(f"{user_id}_team", "ناشناخته")
    phone = message.contact.phone_number

    users = load_users()
    users[user_id] = {
        "team_name": team_name,
        "phone": phone,
        "gems": 0,
        "coins": 0,
        "players": ["player1", "player2", "player3", "player4", "player5"],
        "score": 0,
        "tactic": {},
        "match_history": [],
    }
    save_users(users)

    bot.send_message(message.chat.id, "✅ ثبت‌نام با موفقیت انجام شد!", reply_markup=main_menu())

# منوی اصلی
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 ترکیب و تاکتیک", "🏪 فروشگاه")
    markup.row("🎮 بازی شبانه", "📄 گزارش بازی")
    markup.row("👛 کیف پول", "🎁 پاداش روزانه")
    markup.row("🏆 برترین‌ها", "بازگشت به منو")
    return markup

# ذخیره/بارگذاری
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Flask راه‌اندازی سرور
@app.route("/", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Football Bot Running!"

if __name__ == "__main__":
    # webhook only once
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    threading.Thread(target=run_nightly_game, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
