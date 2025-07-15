import telebot
from telebot import types
import json
import os
import random
from datetime import datetime

TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
ADMIN_ID = 5542927340
CHANNEL_USERNAME = "@Specialcoach1"
TRON_ADDRESS = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"

bot = telebot.TeleBot(TOKEN)

users_file = 'data/users.json'
players_file = 'data/players.json'

# ---------------- ذخیره و بارگذاری ---------------- #

def load_users():
    if not os.path.exists(users_file):
        return {}
    with open(users_file, 'r') as f:
        return json.load(f)

def save_users(data):
    with open(users_file, 'w') as f:
        json.dump(data, f)

def load_players():
    with open(players_file, 'r') as f:
        return json.load(f)

users = load_users()
players = load_players()

# ---------------- استارت و عضویت ---------------- #

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = str(msg.from_user.id)
    if user_id not in users:
        users[user_id] = {"step": "check_join", "team": "", "contact": "", "coins": 0, "gems": 0, "players": [], "lineup": [], "tactic": {}, "score": 0, "wins": 0, "games": 0}
        save_users(users)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
    markup.add(types.InlineKeyboardButton("عضو شدم ✅", callback_data="check_joined"))
    bot.send_message(msg.chat.id, "برای ادامه لطفاً عضو کانال شوید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_joined")
def check_joined(call):
    user_id = str(call.from_user.id)
    chat_member = bot.get_chat_member(CHANNEL_USERNAME, call.from_user.id)
    if chat_member.status in ['member', 'administrator', 'creator']:
        users[user_id]["step"] = "ask_team"
        save_users(users)
        bot.send_message(call.message.chat.id, "نام تیم خود را وارد کنید:")
    else:
        bot.send_message(call.message.chat.id, "لطفاً ابتدا عضو کانال شوید.")

@bot.message_handler(func=lambda m: str(m.from_user.id) in users and users[str(m.from_user.id)]["step"] == "ask_team")
def get_team_name(msg):
    user_id = str(msg.from_user.id)
    users[user_id]["team"] = msg.text
    users[user_id]["step"] = "ask_contact"
    save_users(users)

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("📞 ارسال شماره", request_contact=True))
    bot.send_message(msg.chat.id, "شماره تماس خود را بفرستید:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_contact(msg):
    user_id = str(msg.from_user.id)
    if users[user_id]["step"] == "ask_contact":
        users[user_id]["contact"] = msg.contact.phone_number
        users[user_id]["step"] = "done"
        save_users(users)
        bot.send_message(msg.chat.id, "ثبت‌نام با موفقیت انجام شد ✅", reply_markup=main_menu())
    else:
        bot.send_message(msg.chat.id, "شماره تماس نیاز نیست.")

# ---------------- منوی اصلی ---------------- #

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛒 فروشگاه بازیکنان", "📋 ترکیب و تاکتیک")
    markup.add("🏆 برترین‌ها", "🎮 بازی شبانه")
    markup.add("💰 کیف پول")
    return markup

@bot.message_handler(func=lambda m: m.text == "🛒 فروشگاه بازیکنان")
def player_shop(msg):
    user_id = str(msg.from_user.id)
    text = "بازیکنان موجود برای خرید:\n"
    markup = types.InlineKeyboardMarkup()
    for p in players:
        if p["id"] not in users[user_id]["players"]:
            text += f"{p['id']}- {p['name']} | توان: {p['skill']} | 💎{p['price_gems']} | 🪙{p['price_coins']}\n"
            markup.add(types.InlineKeyboardButton(f"خرید {p['name']}", callback_data=f"buy_{p['id']}"))
    bot.send_message(msg.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_player(call):
    user_id = str(call.from_user.id)
    player_id = int(call.data.split("_")[1])
    player = next((p for p in players if p["id"] == player_id), None)
    if not player:
        return

    if player_id in users[user_id]["players"]:
        bot.answer_callback_query(call.id, "این بازیکن را قبلاً خریدید.")
        return

    if users[user_id]["gems"] >= player["price_gems"]:
        users[user_id]["gems"] -= player["price_gems"]
        users[user_id]["players"].append(player_id)
        save_users(users)
        bot.answer_callback_query(call.id, f"{player['name']} خریداری شد!")
    else:
        bot.answer_callback_query(call.id, "جم کافی ندارید.")

# ---------------- تاکتیک و ترکیب ---------------- #

@bot.message_handler(func=lambda m: m.text == "📋 ترکیب و تاکتیک")
def tactics_menu(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🧩 چیدمان", "🎯 تاکتیک", "🎲 سبک بازی")
    markup.add("🚧 تله آفساید", "🔥 پرسینگ")
    markup.add("🔙 بازگشت به منو")
    bot.send_message(msg.chat.id, "یکی از بخش‌های تاکتیک رو انتخاب کن:", reply_markup=markup)

# ادامه کد شامل سیستم بازی شبانه، ثبت بازی‌ها، رتبه‌بندی، کیف پول و ارسال فیش در پیام بعدی قرار می‌گیره...

# ---------------- تنظیم تاکتیک‌ها ---------------- #

@bot.message_handler(func=lambda m: m.text == "🧩 چیدمان")
def formation(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("1-2-2", "1-1-3", "1-3-1", "1-4")
    users[str(msg.from_user.id)]["tactic"]["formation"] = ""
    bot.send_message(msg.chat.id, "چیدمان مورد نظر رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["1-2-2", "1-1-3", "1-3-1", "1-4"])
def set_formation(msg):
    uid = str(msg.from_user.id)
    users[uid]["tactic"]["formation"] = msg.text
    save_users(users)
    bot.send_message(msg.chat.id, f"چیدمان ذخیره شد: {msg.text}")

@bot.message_handler(func=lambda m: m.text == "🎯 تاکتیک")
def tactics_choice(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("هجومی", "دفاعی", "متعادل")
    bot.send_message(msg.chat.id, "تاکتیک رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["هجومی", "دفاعی", "متعادل"])
def save_tactic(msg):
    uid = str(msg.from_user.id)
    users[uid]["tactic"]["style"] = msg.text
    save_users(users)
    bot.send_message(msg.chat.id, f"تاکتیک ذخیره شد: {msg.text}")

@bot.message_handler(func=lambda m: m.text == "🎲 سبک بازی")
def play_style(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("پاسکاری", "بازی با وینگ")
    bot.send_message(msg.chat.id, "سبک بازی رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["پاسکاری", "بازی با وینگ"])
def save_playstyle(msg):
    uid = str(msg.from_user.id)
    users[uid]["tactic"]["play_style"] = msg.text
    save_users(users)
    bot.send_message(msg.chat.id, f"سبک ذخیره شد: {msg.text}")

@bot.message_handler(func=lambda m: m.text == "🚧 تله آفساید")
def set_offside(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بذار", "نذار")
    bot.send_message(msg.chat.id, "تله آفساید رو فعال کنی؟", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["بذار", "نذار"])
def save_offside(msg):
    uid = str(msg.from_user.id)
    users[uid]["tactic"]["offside"] = msg.text
    save_users(users)
    bot.send_message(msg.chat.id, f"تله آفساید تنظیم شد: {msg.text}")

@bot.message_handler(func=lambda m: m.text == "🔥 پرسینگ")
def press_choice(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("پرس 100%", "پرس 50%", "نمی‌خوام")
    bot.send_message(msg.chat.id, "درصد پرسینگ:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["پرس 100%", "پرس 50%", "نمی‌خوام"])
def save_press(msg):
    uid = str(msg.from_user.id)
    users[uid]["tactic"]["press"] = msg.text
    save_users(users)
    bot.send_message(msg.chat.id, f"پرسینگ تنظیم شد: {msg.text}")

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت به منو")
def back_main(msg):
    bot.send_message(msg.chat.id, "بازگشت به منو:", reply_markup=main_menu())

# ---------------- بازی شبانه ---------------- #

@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def show_game(msg):
    now = datetime.now()
    if now.hour == 21:
        bot.send_message(msg.chat.id, "🎮 بازی شما شروع شد!")
        # اینجا باید متناسب با جدول‌ها و سیستم دو نفره اجرا بشه
        bot.send_message(msg.chat.id, "🔍 گزارش بازی: تیم شما با ترکیب و تاکتیک خودتون به میدان رفت...")
        # امتیازدهی ساده
        result = random.choice(["win", "draw", "lose"])
        uid = str(msg.from_user.id)
        users[uid]["games"] += 1
        if result == "win":
            users[uid]["score"] += 20
            users[uid]["wins"] += 1
            bot.send_message(msg.chat.id, "🎉 بردی! +20 امتیاز")
        elif result == "draw":
            users[uid]["score"] += 5
            bot.send_message(msg.chat.id, "⚖️ مساوی! +5 امتیاز")
        else:
            users[uid]["score"] -= 10
            bot.send_message(msg.chat.id, "❌ باختی! -10 امتیاز")
        save_users(users)
    else:
        bot.send_message(msg.chat.id, "🕘 بازی شبانه فقط ساعت ۹ شب شروع می‌شود.")

# ---------------- برترین‌ها ---------------- #

@bot.message_handler(func=lambda m: m.text == "🏆 برترین‌ها")
def show_leaders(msg):
    ranking = sorted(users.items(), key=lambda x: (x[1]["wins"] / x[1]["games"] if x[1]["games"] else 0, x[1]["score"]), reverse=True)
    text = "🏆 برترین مربیان:\n"
    for i, (uid, data) in enumerate(ranking[:10], 1):
        percent = round((data["wins"] / data["games"])*100) if data["games"] > 0 else 0
        text += f"{i}- {data['team']}: {percent}% برد - {data['score']} امتیاز\n"
    bot.send_message(msg.chat.id, text)

# ---------------- کیف پول ---------------- #

@bot.message_handler(func=lambda m: m.text == "💰 کیف پول")
def wallet(msg):
    uid = str(msg.from_user.id)
    u = users[uid]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("تبدیل ۱۰۰ سکه به ۱ جم", callback_data="coin2gem"))
    markup.add(types.InlineKeyboardButton("ارسال فیش خرید 💸", callback_data="send_receipt"))
    text = f"💎 جم: {u['gems']}\n🪙 سکه: {u['coins']}\n📥 آدرس واریز ترون:\n`{TRON_ADDRESS}`"
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "coin2gem")
def convert_coin(c):
    uid = str(c.from_user.id)
    if users[uid]["coins"] >= 100:
        users[uid]["coins"] -= 100
        users[uid]["gems"] += 1
        save_users(users)
        bot.answer_callback_query(c.id, "✅ ۱ جم اضافه شد")
    else:
        bot.answer_callback_query(c.id, "❌ سکه کافی نداری")

@bot.callback_query_handler(func=lambda c: c.data == "send_receipt")
def ask_receipt(c):
    bot.send_message(c.message.chat.id, "🧾 لطفاً فیش واریزی (عکس یا متن) را ارسال کنید.")

@bot.message_handler(content_types=['photo', 'text'])
def handle_receipt(msg):
    if str(msg.from_user.id) not in users:
        return
    if msg.photo or "trx" in msg.text.lower():
        bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{msg.from_user.id}"),
            types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{msg.from_user.id}")
        )
        bot.send_message(ADMIN_ID, f"فیش جدید از {msg.from_user.first_name}:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_") or c.data.startswith("reject_"))
def admin_decision(c):
    target = c.data.split("_")[1]
    if c.data.startswith("approve_"):
        users[target]["coins"] += 100
        save_users(users)
        bot.send_message(target, "✅ فیش تأیید شد. 100 سکه اضافه شد.")
        bot.answer_callback_query(c.id, "فیش تأیید شد.")
    else:
        bot.send_message(target, "❌ فیش شما رد شد.")
        bot.answer_callback_query(c.id, "فیش رد شد.")

# ---------------- اجرا ---------------- #

bot.remove_webhook()
bot.infinity_polling()
