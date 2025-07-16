import telebot
import json
import os
from flask import Flask, request
import time
from datetime import datetime, timedelta
import random
import threading
import logging

# تنظیم لاگ برای عیب‌یابی
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تنظیمات اولیه
TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
ADMIN_ID = 5542927340
CHANNEL_ID = "@Specialcoach1"
TRON_ADDRESS = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"
WEBHOOK_URL = "https://special-coach.onrender.com"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# مسیرهای دایرکتوری
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")

# اطمینان از وجود دایرکتوری data
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    logger.info("پوشه data ایجاد شد")

# بارگذاری یا ایجاد فایل‌های JSON
def load_json(file_path, default_data):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)
            return default_data
    except Exception as e:
        logger.error(f"خطا در بارگذاری فایل {file_path}: {e}")
        return default_data

users = load_json(USERS_FILE, {})
players = load_json(PLAYERS_FILE, {})

# ذخیره داده‌ها
def save_users():
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
        logger.info("داده‌های کاربران ذخیره شد")
    except Exception as e:
        logger.error(f"خطا در ذخیره فایل users.json: {e}")

# تابع بررسی عضویت در کانال
def check_channel_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"خطا در بررسی عضویت کاربر {user_id}: {e}")
        return False

# منوی اصلی
def main_menu():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🎮 بازی شبانه", "🧍‍♂️ فروشگاه بازیکن")
    keyboard.add("⚽ ترکیب و تاکتیک", "👛 کیف پول")
    keyboard.add("🏆 برترین‌ها", "🎁 پاداش روزانه")
    return keyboard

# مراحل ثبت‌نام
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} دستور /start را اجرا کرد")
    if user_id in users:
        bot.send_message(message.chat.id, "شما قبلاً ثبت‌نام کرده‌اید!", reply_markup=main_menu())
        return

    users[user_id] = {"step": "check_membership"}
    save_users()
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("عضو شدم", callback_data="check_membership"))
    keyboard.add(telebot.types.InlineKeyboardButton("لینک کانال", url=f"https://t.me/{CHANNEL_ID[1:]}"))
    bot.send_message(message.chat.id, "لطفاً ابتدا در کانال @Specialcoach1 عضو شوید.", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = str(call.from_user.id)
    logger.info(f"کاربر {user_id} دکمه {call.data} را کلیک کرد")
    try:
        if call.data == "check_membership":
            if check_channel_membership(user_id):
                users[user_id]["step"] = "team_name"
                save_users()
                bot.send_message(call.message.chat.id, "نام تیم خود را وارد کنید:")
            else:
                bot.answer_callback_query(call.id, "شما هنوز در کانال عضو نشده‌اید!")
        elif call.data == "share_contact":
            bot.answer_callback_query(call.id)
        elif call.data.startswith("buy_player_"):
            player_id = call.data.split("_")[2]
            buy_player(call.message, user_id, player_id)
        elif call.data.startswith("tactic_"):
            tactic = call.data.split("_")[1]
            users[user_id]["tactic"] = tactic
            save_users()
            bot.send_message(call.message.chat.id, f"تاکتیک {tactic} انتخاب شد.")
            show_tactics_menu(call.message)
        elif call.data.startswith("style_"):
            style = call.data.split("_")[1]
            users[user_id]["style"] = style
            save_users()
            bot.send_message(call.message.chat.id, f"سبک بازی {style} انتخاب شد.")
            show_tactics_menu(call.message)
        elif call.data.startswith("offside_"):
            offside = call.data.split("_")[1]
            users[user_id]["offside_trap"] = offside
            save_users()
            bot.send_message(call.message.chat.id, f"تله آفساید: {offside}")
            show_tactics_menu(call.message)
        elif call.data.startswith("pressing_"):
            pressing = call.data.split("_")[1]
            users[user_id]["pressing"] = pressing
            save_users()
            bot.send_message(call.message.chat.id, f"پرسینگ: {pressing}")
            show_tactics_menu(call.message)
        elif call.data.startswith("confirm_payment_") or call.data.startswith("reject_payment_"):
            handle_payment_confirmation(call.message, user_id, call.data)
        elif call.data.startswith("formation_"):
            formation = call.data.split("_")[1]
            users[user_id]["formation"] = formation
            save_users()
            bot.send_message(call.message.chat.id, f"ترکیب {formation} انتخاب شد.")
            show_team_formation(call.message)
        elif call.data == "change_formation":
            change_formation(call)
        elif call.data in ["tactic_menu", "style_menu", "offside_menu", "pressing_menu"]:
            if call.data == "tactic_menu":
                tactic_menu(call)
            elif call.data == "style_menu":
                style_menu(call)
            elif call.data == "offside_menu":
                offside_menu(call)
            elif call.data == "pressing_menu":
                pressing_menu(call)
    except Exception as e:
        logger.error(f"خطا در پردازش callback {call.data} برای کاربر {user_id}: {e}")
        bot.send_message(call.message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} پیام متنی ارسال کرد: {message.text}")
    try:
        if user_id not in users:
            bot.send_message(message.chat.id, "لطفاً با /start ثبت‌نام کنید.")
            return

        step = users[user_id].get("step")
        if step == "team_name":
            users[user_id]["team_name"] = message.text
            users[user_id]["step"] = "share_contact"
            save_users()
            keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(telebot.types.KeyboardButton("ارسال شماره", request_contact=True))
            bot.send_message(message.chat.id, "لطفاً شماره تماس خود را ارسال کنید:", reply_markup=keyboard)
        elif step == "wallet_text":
            users[user_id]["pending_payment"] = {"amount": message.text}
            save_users()
            bot.send_message(message.chat.id, "فیش متنی دریافت شد و برای ادمین ارسال شد.")
            bot.send_message(ADMIN_ID, f"فیش متنی از {user_id}:\n{message.text}", reply_markup=admin_payment_keyboard(user_id))
    except Exception as e:
        logger.error(f"خطا در پردازش پیام متنی کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} شماره تماس ارسال کرد")
    try:
        if user_id not in users or users[user_id].get("step") != "share_contact":
            return

        users[user_id]["phone"] = message.contact.phone_number
        users[user_id]["step"] = "completed"
        users[user_id]["coins"] = 0
        users[user_id]["gems"] = 0
        users[user_id]["players"] = ["player1", "player2", "player3", "player4", "player5"]
        users[user_id]["score"] = 0
        users[user_id]["matches"] = 0
        users[user_id]["wins"] = 0
        users[user_id]["formation"] = "1-2-2"
        users[user_id]["tactic"] = "متعادل"
        users[user_id]["style"] = "پاسکاری"
        users[user_id]["offside_trap"] = "نذار"
        users[user_id]["pressing"] = "پرسینگ ۵۰ درصد"
        users[user_id]["daily_reward"] = None
        save_users()
        bot.send_message(message.chat.id, "ثبت‌نام شما با موفقیت انجام شد!", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"خطا در پردازش شماره تماس کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} تصویر فیش ارسال کرد")
    try:
        if user_id not in users:
            return

        if users[user_id].get("step") == "wallet_photo":
            file_info = bot.get_file(message.photo[-1].file_id)
            file_path = file_info.file_path
            users[user_id]["pending_payment"] = {"photo": file_path}
            save_users()
            bot.send_message(message.chat.id, "فیش تصویری دریافت شد و برای ادمین ارسال شد.")
            bot.send_photo(ADMIN_ID, file_path, caption=f"فیش تصویری از {user_id}", reply_markup=admin_payment_keyboard(user_id))
    except Exception as e:
        logger.error(f"خطا در پردازش تصویر فیش کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

# فروشگاه بازیکن
@bot.message_handler(func=lambda message: message.text == "🧍‍♂️ فروشگاه بازیکن")
def show_players(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} فروشگاه بازیکن را باز کرد")
    try:
        if user_id not in users:
            bot.send_message(message.chat.id, "لطفاً ابتدا ثبت‌نام کنید.")
            return

        keyboard = telebot.types.InlineKeyboardMarkup()
        for player_id, player in players.items():
            if player_id not in users[user_id]["players"]:
                price = f"{player['price_coins']} سکه یا {player['price_gems']} جم"
                keyboard.add(telebot.types.InlineKeyboardButton(f"{player['name']} ({player['position']}) - {price}", callback_data=f"buy_player_{player_id}"))
        bot.send_message(message.chat.id, "بازیکنان موجود:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطا در نمایش فروشگاه برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

def buy_player(message, user_id, player_id):
    try:
        if len(users[user_id]["players"]) >= 8:
            bot.send_message(message.chat.id, "شما نمی‌توانید بیش از ۸ بازیکن داشته باشید!")
            return
        if player_id in users[user_id]["players"]:
            bot.send_message(message.chat.id, "این بازیکن قبلاً خریداری شده است!")
            return

        player = players[player_id]
        if users[user_id]["coins"] >= player["price_coins"]:
            users[user_id]["coins"] -= player["price_coins"]
            users[user_id]["players"].append(player_id)
            save_users()
            bot.send_message(message.chat.id, f"بازیکن {player['name']} با موفقیت خریداری شد!")
        elif users[user_id]["gems"] >= player["price_gems"]:
            users[user_id]["gems"] -= player["price_gems"]
            users[user_id]["players"].append(player_id)
            save_users()
            bot.send_message(message.chat.id, f"بازیکن {player['name']} با موفقیت خریداری شد!")
        else:
            bot.send_message(message.chat.id, "موجودی کافی نیست!")
    except Exception as e:
        logger.error(f"خطا در خرید بازیکن {player_id} برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

# ترکیب و تاکتیک
@bot.message_handler(func=lambda message: message.text == "⚽ ترکیب و تاکتیک")
def show_tactics_menu(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} منوی ترکیب و تاکتیک را باز کرد")
    try:
        if user_id not in users:
            bot.send_message(message.chat.id, "لطفاً ابتدا ثبت‌نام کنید.")
            return

        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton("تغییر ترکیب", callback_data="change_formation"))
        keyboard.add(telebot.types.InlineKeyboardButton("تاکتیک", callback_data="tactic_menu"))
        keyboard.add(telebot.types.InlineKeyboardButton("سبک بازی", callback_data="style_menu"))
        keyboard.add(telebot.types.InlineKeyboardButton("تله آفساید", callback_data="offside_menu"))
        keyboard.add(telebot.types.InlineKeyboardButton("پرسینگ", callback_data="pressing_menu"))
        bot.send_message(message.chat.id, "بخش ترکیب و تاکتیک:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطا در نمایش منوی ترکیب و تاکتیک برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

def change_formation(call):
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        formations = ["1-2-2", "1-1-3", "1-3-1", "1-4"]
        for formation in formations:
            keyboard.add(telebot.types.InlineKeyboardButton(formation, callback_data=f"formation_{formation}"))
        bot.send_message(call.message.chat.id, "ترکیب موردنظر را انتخاب کنید:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطا در نمایش منوی ترکیب برای کاربر {call.from_user.id}: {e}")
        bot.send_message(call.message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

def show_team_formation(message):
    user_id = str(message.from_user.id)
    try:
        formation = users[user_id]["formation"]
        team_players = users[user_id]["players"]
        positions = {"GK": [], "DF": [], "MF": [], "FW": []}
        for player_id in team_players:
            position = players[player_id]["position"]
            positions[position].append(players[player_id]["name"])

        formation_map = {
            "1-2-2": {"GK": 1, "DF": 2, "MF": 2, "FW": 0},
            "1-1-3": {"GK": 1, "DF": 1, "MF": 3, "FW": 0},
            "1-3-1": {"GK": 1, "DF": 3, "MF": 1, "FW": 0},
            "1-4": {"GK": 1, "DF": 4, "MF": 0, "FW": 0}
        }
        required = formation_map[formation]
        team = []
        for pos, count in required.items():
            available = positions[pos][:count]
            team.extend(available)
            if len(available) < count:
                team.extend(["-"] * (count - len(available)))
        bot.send_message(message.chat.id, f"ترکیب تیم ({formation}):\n" + "\n".join(team))
    except Exception as e:
        logger.error(f"خطا در نمایش ترکیب تیم برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

def tactic_menu(call):
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        tactics = ["هجومی", "دفاعی", "متعادل"]
        for tactic in tactics:
            keyboard.add(telebot.types.InlineKeyboardButton(tactic, callback_data=f"tactic_{tactic}"))
        bot.send_message(call.message.chat.id, "تاکتیک موردنظر را انتخاب کنید:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطا در نمایش منوی تاکتیک برای کاربر {call.from_user.id}: {e}")
        bot.send_message(call.message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

def style_menu(call):
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        styles = ["پاسکاری", "بازی با وینگ", "ضدحمله"]
        for style in styles:
            keyboard.add(telebot.types.InlineKeyboardButton(style, callback_data=f"style_{style}"))
        bot.send_message(call.message.chat.id, "سبک بازی را انتخاب کنید:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطا در نمایش منوی سبک بازی برای کاربر {call.from_user.id}: {e}")
        bot.send_message(call.message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

def offside_menu(call):
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton("بذار", callback_data="offside_بذار"))
        keyboard.add(telebot.types.InlineKeyboardButton("نذار", callback_data="offside_نذار"))
        bot.send_message(call.message.chat.id, "تله آفساید:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطا در نمایش منوی تله آفساید برای کاربر {call.from_user.id}: {e}")
        bot.send_message(call.message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

def pressing_menu(call):
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        pressings = ["پرس ۱۰۰ درصد", "پرسینگ ۵۰ درصد", "پرسینگ نمیخوام"]
        for pressing in pressings:
            keyboard.add(telebot.types.InlineKeyboardButton(pressing, callback_data=f"pressing_{pressing}"))
        bot.send_message(call.message.chat.id, "پرسینگ:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطا در نمایش منوی پرسینگ برای کاربر {call.from_user.id}: {e}")
        bot.send_message(call.message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

# بازی شبانه
@bot.message_handler(func=lambda message: message.text == "🎮 بازی شبانه")
def join_night_game(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} در بازی شبانه ثبت‌نام کرد")
    try:
        if user_id not in users:
            bot.send_message(message.chat.id, "لطفاً ابتدا ثبت‌نام کنید.")
            return
        users[user_id]["night_game"] = True
        save_users()
        bot.send_message(message.chat.id, "شما در بازی شبانه ساعت ۲۱:۰۰ ثبت‌نام کردید!")
    except Exception as e:
        logger.error(f"خطا در ثبت‌نام بازی شبانه برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

def simulate_match(player1_id, player2_id):
    try:
        p1_players = users[player1_id]["players"]
        p2_players = users[player2_id]["players"]
        p1_score = sum(players[p]["overall"] for p in p1_players)
        p2_score = sum(players[p]["overall"] for p in p2_players)

        tactic_multipliers = {"هجومی": 1.2, "دفاعی": 0.8, "متعادل": 1.0}
        style_multipliers = {"پاسکاری": 1.1, "بازی با وینگ": 1.15, "ضدحمله": 1.2}
        pressing_multipliers = {"پرس ۱۰۰ درصد": 1.2, "پرسینگ ۵۰ درصد": 1.0, "پرسینگ نمیخوام": 0.9}
        offside_multipliers = {"بذار": 1.1, "نذار": 1.0}

        p1_tactic = tactic_multipliers.get(users[player1_id]["tactic"], 1.0)
        p2_tactic = tactic_multipliers.get(users[player2_id]["tactic"], 1.0)
        p1_style = style_multipliers.get(users[player1_id]["style"], 1.0)
        p2_style = style_multipliers.get(users[player2_id]["style"], 1.0)
        p1_pressing = pressing_multipliers.get(users[player1_id]["pressing"], 1.0)
        p2_pressing = pressing_multipliers.get(users[player2_id]["pressing"], 1.0)
        p1_offside = offside_multipliers.get(users[player1_id]["offside_trap"], 1.0)
        p2_offside = offside_multipliers.get(users[player2_id]["offside_trap"], 1.0)

        p1_total = p1_score * p1_tactic * p1_style * p1_pressing * p1_offside
        p2_total = p2_score * p2_tactic * p2_style * p2_pressing * p2_offside

        random_factor = random.uniform(0.9, 1.1)
        p1_total *= random_factor
        p2_total *= random_factor

        if p1_total > p2_total:
            users[player1_id]["score"] += 20
            users[player1_id]["wins"] += 1
            users[player1_id]["coins"] += 100
            users[player2_id]["score"] -= 10
            users[player2_id]["coins"] += 20
            result = f"{users[player1_id]['team_name']} برد!"
        elif p2_total > p1_total:
            users[player2_id]["score"] += 20
            users[player2_id]["wins"] += 1
            users[player2_id]["coins"] += 100
            users[player1_id]["score"] -= 10
            users[player1_id]["coins"] += 20
            result = f"{users[player2_id]['team_name']} برد!"
        else:
            users[player1_id]["score"] += 5
            users[player1_id]["coins"] += 40
            users[player2_id]["score"] += 5
            users[player2_id]["coins"] += 40
            result = "مساوی!"

        users[player1_id]["matches"] += 1
        users[player2_id]["matches"] += 1
        report = f"بازی شروع شد!\n{users[player1_id]['team_name']} vs {users[player2_id]['team_name']}\nنتیجه: {result}"
        users[player1_id]["last_match"] = report
        users[player2_id]["last_match"] = report
        save_users()
        return report
    except Exception as e:
        logger.error(f"خطا در شبیه‌سازی بازی بین {player1_id} و {player2_id}: {e}")
        return "خطایی در شبیه‌سازی بازی رخ داد."

@bot.message_handler(func=lambda message: message.text == "📄 گزارش بازی")
def show_match_report(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} درخواست گزارش بازی کرد")
    try:
        if user_id not in users or not users[user_id].get("last_match"):
            bot.send_message(message.chat.id, "هنوز بازی‌ای انجام نشده است!")
            return
        bot.send_message(message.chat.id, users[user_id]["last_match"])
    except Exception as e:
        logger.error(f"خطا در نمایش گزارش بازی برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

# کیف پول
@bot.message_handler(func=lambda message: message.text == "👛 کیف پول")
def show_wallet(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} منوی کیف پول را باز کرد")
    try:
        if user_id not in users:
            bot.send_message(message.chat.id, "لطفاً ابتدا ثبت‌نام کنید.")
            return

        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("ارسال فیش متنی", "ارسال فیش تصویری")
        keyboard.add("تبدیل سکه به جم", "بازگشت")
        bot.send_message(message.chat.id, f"موجودی:\nسکه: {users[user_id]['coins']}\nجم: {users[user_id]['gems']}\n\nآدرس ترون: {TRON_ADDRESS}\nهر ۴ ترون = ۱۰۰ سکه", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطا در نمایش کیف پول برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

@bot.message_handler(func=lambda message: message.text == "ارسال فیش متنی")
def request_text_payment(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} درخواست ارسال فیش متنی کرد")
    try:
        users[user_id]["step"] = "wallet_text"
        save_users()
        bot.send_message(message.chat.id, "لطفاً فیش متنی را ارسال کنید:")
    except Exception as e:
        logger.error(f"خطا در درخواست فیش متنی برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

@bot.message_handler(func=lambda message: message.text == "ارسال فیش تصویری")
def request_photo_payment(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} درخواست ارسال فیش تصویری کرد")
    try:
        users[user_id]["step"] = "wallet_photo"
        save_users()
        bot.send_message(message.chat.id, "لطفاً تصویر فیش را ارسال کنید:")
    except Exception as e:
        logger.error(f"خطا در درخواست فیش تصویری برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

@bot.message_handler(func=lambda message: message.text == "تبدیل سکه به جم")
def convert_coins_to_gems(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} درخواست تبدیل سکه به جم کرد")
    try:
        if users[user_id]["coins"] >= 100:
            users[user_id]["coins"] -= 100
            users[user_id]["gems"] += 1
            save_users()
            bot.send_message(message.chat.id, "۱۰۰ سکه به ۱ جم تبدیل شد!")
        else:
            bot.send_message(message.chat.id, "سکه کافی ندارید!")
    except Exception as e:
        logger.error(f"خطا در تبدیل سکه به جم برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

def admin_payment_keyboard(user_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("تأیید ✅", callback_data=f"confirm_payment_{user_id}"))
    keyboard.add(telebot.types.InlineKeyboardButton("رد ❌", callback_data=f"reject_payment_{user_id}"))
    return keyboard

def handle_payment_confirmation(message, user_id, action):
    try:
        target_user_id = action.split("_")[-1]
        if user_id != str(ADMIN_ID):
            return
        if action.startswith("confirm_payment"):
            users[target_user_id]["coins"] += 100
            save_users()
            bot.send_message(target_user_id, "۱۰۰ سکه به شما اضافه شد!")
            bot.send_message(message.chat.id, "پرداخت تأیید شد.")
        else:
            bot.send_message(target_user_id, "فیش ارسالی رد شد.")
            bot.send_message(message.chat.id, "پرداخت رد شد.")
    except Exception as e:
        logger.error(f"خطا در پردازش تأیید/رد فیش برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

@bot.message_handler(func=lambda message: message.text == "بازگشت")
def back_to_menu(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} به منوی اصلی بازگشت")
    try:
        users[user_id]["step"] = "completed"
        save_users()
        bot.send_message(message.chat.id, "منوی اصلی:", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"خطا در بازگشت به منوی اصلی برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

# برترین‌ها
@bot.message_handler(func=lambda message: message.text == "🏆 برترین‌ها")
def show_leaderboard(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} منوی برترین‌ها را باز کرد")
    try:
        leaderboard = []
        for user_id, data in users.items():
            if data.get("matches", 0) > 0:
                win_rate = (data["wins"] / data["matches"]) * 100
                leaderboard.append((data["team_name"], win_rate, data["score"]))
        leaderboard.sort(key=lambda x: (x[1], x[2]), reverse=True)
        text = "🏆 برترین‌ها:\n"
        for i, (team, win_rate, score) in enumerate(leaderboard[:10], 1):
            text += f"{i}. {team}: {win_rate:.1f}% برد، {score} امتیاز\n"
        bot.send_message(message.chat.id, text or "هنوز تیمی ثبت نشده است!")
    except Exception as e:
        logger.error(f"خطا در نمایش برترین‌ها برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

# پاداش روزانه
@bot.message_handler(func=lambda message: message.text == "🎁 پاداش روزانه")
def daily_reward(message):
    user_id = str(message.from_user.id)
    logger.info(f"کاربر {user_id} درخواست پاداش روزانه کرد")
    try:
        if user_id not in users:
            bot.send_message(message.chat.id, "لطفاً ابتدا ثبت‌نام کنید.")
            return

        last_reward = users[user_id].get("daily_reward")
        now = datetime.now()
        if last_reward and (now - datetime.fromisoformat(last_reward)).days < 1:
            bot.send_message(message.chat.id, "شما امروز پاداش خود را دریافت کرده‌اید!")
            return

        users[user_id]["gems"] += 2
        users[user_id]["daily_reward"] = now.isoformat()
        save_users()
        bot.send_message(message.chat.id, "۲ جم به شما اضافه شد!")
    except Exception as e:
        logger.error(f"خطا در اعطای پاداش روزانه برای کاربر {user_id}: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

# زمان‌بندی بازی شبانه
def night_game_scheduler():
    while True:
        try:
            now = datetime.now()
            target_time = now.replace(hour=21, minute=0, second=0, microsecond=0)
            if now > target_time:
                target_time += timedelta(days=1)
            time.sleep((target_time - now).total_seconds())
            logger.info("اجرای بازی شبانه شروع شد")
            participants = [user_id for user_id, data in users.items() if data.get("night_game")]
            random.shuffle(participants)
            for i in range(0, len(participants), 2):
                if i + 1 < len(participants):
                    report = simulate_match(participants[i], participants[i + 1])
                    bot.send_message(participants[i], report)
                    bot.send_message(participants[i + 1], report)
            save_users()
            logger.info("بازی شبانه با موفقیت اجرا شد")
        except Exception as e:
            logger.error(f"خطا در اجرای بازی شبانه: {e}")

# تنظیم وب‌هوک
@app.route('/', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            logger.info("وب‌هوک با موفقیت پردازش شد")
            return 'OK', 200
        logger.warning("نوع محتوای نامعتبر در وب‌هوک")
        return 'Invalid content type', 400
    except Exception as e:
        logger.error(f"خطا در پردازش وب‌هوک: {e}")
        return 'Error', 500

if __name__ == "__main__":
    try:
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"وب‌هوک با موفقیت روی {WEBHOOK_URL} تنظیم شد")
        threading.Thread(target=night_game_scheduler, daemon=True).start()
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    except Exception as e:
        logger.error(f"خطا در راه‌اندازی سرور: {e}")
