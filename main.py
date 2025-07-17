import telebot
from telebot import types
from flask import Flask, request
import os, json

TOKEN = "YOUR_TOKEN"
WEBHOOK_URL = "https://YOUR_URL/" + TOKEN
ADMIN_ID = 5542927340
CHANNEL = "@YourChannel"

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
    markup.row("👛 کیف پول", "برترین ها🏆", "پاداش روزانه🎁")
    return markup

# منوی بازگشت
def back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بازگشت به منو")
    return markup

# متغیر برای وضعیت کاربر در ثبت‌نام
user_states = {}

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
        "players": [],
        "score": 0,
        "coins": 100,
        "gems": 2,
        "match_history": [],
        "last_reward_date": None  # برای پاداش روزانه
    }

    save_users(users)
    user_states.pop(uid)

    bot.send_message(message.chat.id, "🎉 ثبت‌نام کامل شد. به منوی اصلی خوش اومدی!", reply_markup=main_menu())

# برترین ها
@bot.message_handler(func=lambda m: m.text == "برترین ها🏆")
def show_leaders(m):
    users = load_users()
    sorted_users = sorted(users.items(), key=lambda x: x[1]["score"], reverse=True)
    leaderboard = "🏆 برترین‌ها:\n"
    
    for idx, (uid, user) in enumerate(sorted_users[:10], start=1):
        leaderboard += f"{idx}. {user['team']} - امتیاز: {user['score']}\n"

    bot.send_message(m.chat.id, leaderboard, reply_markup=back_menu())

# پاداش روزانه
@bot.message_handler(func=lambda m: m.text == "پاداش روزانه🎁")
def daily_reward(m):
    uid = str(m.from_user.id)
    users = load_users()
    
    if uid not in users:
        return bot.send_message(m.chat.id, "❌ ابتدا ثبت‌نام کن")

    now = datetime.datetime.now()
    last_reward_date = users[uid]["last_reward_date"]

    if last_reward_date and last_reward_date.date() == now.date():
        return bot.send_message(m.chat.id, "❗ شما امروز قبلاً پاداش دریافت کرده‌اید.")

    users[uid]["coins"] += 50  # مقدار پاداش
    users[uid]["gems"] += 1  # مقدار پاداش
    users[uid]["last_reward_date"] = now

    save_users(users)
    bot.send_message(m.chat.id, "🎁 پاداش روزانه شما با موفقیت دریافت شد! سکه: +50، جم: +1", reply_markup=back_menu())

# اجرای برنامه
if __name__ == "__main__":
    app.run(port=8443)
