import telebot
from flask import Flask, request
import threading, schedule, time, json, random

# === تنظیمات اصلی ===
TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
CHANNEL_USERNAME = "@Specialcoach1"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# === توابع JSON ===
def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def get_user(uid):
    return load_json("users.json").get(str(uid))

def save_user(uid, data):
    users = load_json("users.json")
    users[str(uid)] = data
    save_json("users.json", users)

# === چک عضویت در کانال ===
def is_member(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

# === /start ===
@bot.message_handler(commands=["start"])
def start(m):
    if not is_member(m.chat.id):
        markup = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton("عضویت در کانال 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
        markup.add(btn)
        return bot.send_message(m.chat.id, "🔐 برای استفاده از ربات، ابتدا عضو کانال زیر شو:", reply_markup=markup)

    users = load_json("users.json")
    if str(m.chat.id) in users and "team_name" in users[str(m.chat.id)]:
        return show_menu(m.chat.id)

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = telebot.types.KeyboardButton("📱 ارسال شماره من", request_contact=True)
    markup.add(btn)
    bot.send_message(m.chat.id, "📞 لطفاً شماره‌ت رو بفرست برای احراز هویت:", reply_markup=markup)

# === دریافت شماره تماس ===
@bot.message_handler(content_types=['contact'])
def handle_contact(m):
    if not m.contact or m.contact.user_id != m.from_user.id:
        return bot.send_message(m.chat.id, "❗ لطفاً شماره واقعی خودت رو بفرست.")

    users = load_json("users.json")
    users[str(m.chat.id)] = {
        "phone": m.contact.phone_number,
        "step": "ask_team_name"
    }
    save_json("users.json", users)
    bot.send_message(m.chat.id, "✅ شماره ثبت شد! حالا اسم تیمت رو بنویس:")

# === پردازش پیام‌های متنی ===
@bot.message_handler(func=lambda m: True)
def handle_all_messages(m):
    if not is_member(m.chat.id):
        markup = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton("عضویت در کانال 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
        markup.add(btn)
        return bot.send_message(m.chat.id, "🔐 برای ادامه، اول عضو کانال شو:", reply_markup=markup)

    users = load_json("users.json")
    user = users.get(str(m.chat.id))

    if not user:
        return bot.send_message(m.chat.id, "❗ لطفاً /start رو بزن.")

    if user.get("step") == "ask_team_name":
        team = m.text.strip()
        try:
            all_players = load_json("players.json")
            players = random.sample(all_players, 11) if len(all_players) >= 11 else []
        except:
            players = []

        user.update({
            "team_name": team,
            "coins": 100,
            "gems": 5,
            "players": players,
            "formation": "4-4-2",
            "tactic": "تعادلی",
            "points": 0,
            "step": None
        })
        users[str(m.chat.id)] = user
        save_json("users.json", users)
        bot.send_message(m.chat.id, f"✅ تیم {team} ساخته شد!")
        return show_menu(m.chat.id)

    # دکمه‌های منو
    if m.text == "👤 پروفایل":
        return show_profile(m)
    if m.text == "📋 ترکیب و تاکتیک":
        return bot.send_message(m.chat.id, "📐 این بخش بزودی فعال میشه.")
    if m.text == "🛒 بازار نقل و انتقالات":
        return bot.send_message(m.chat.id, "🔄 این بخش در دست ساخت است.")
    if m.text == "📊 جدول لیگ":
        return bot.send_message(m.chat.id, "📊 جدول لیگ به زودی اضافه میشه.")
    if m.text == "🪙 فروشگاه":
        return bot.send_message(m.chat.id, "🪙 فروشگاه در نسخه بعدی فعاله.")

    return bot.send_message(m.chat.id, "❗ لطفاً از دکمه‌های منو استفاده کن.")

# === پروفایل ===
def show_profile(m):
    user = get_user(m.chat.id)
    if not user:
        return bot.send_message(m.chat.id, "❗ ابتدا /start را بزن.")

    txt = f"""📋 پروفایل شما:

🏷 تیم: {user['team_name']}
💰 سکه: {user['coins']}
💎 جم: {user['gems']}
⚽️ امتیاز: {user['points']}
📐 ترکیب: {user['formation']}
🎯 تاکتیک: {user['tactic']}

👥 بازیکنان اصلی:
"""
    players = user.get("players", [])
    if players:
        for p in players:
            txt += f"• {p['name']} ({p['position']}) - 💵 {p['price']}M\n"
    else:
        txt += "هیچ بازیکنی نداری!"

    bot.send_message(m.chat.id, txt)

# === منو اصلی ===
def show_menu(cid):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 ترکیب و تاکتیک", "🛒 بازار نقل و انتقالات")
    markup.add("📊 جدول لیگ", "🪙 فروشگاه", "👤 پروفایل")
    bot.send_message(cid, "🏟 منوی اصلی:", reply_markup=markup)

# === Flask + Webhook ===
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return 'ok'

@app.route('/')
def index():
    return 'ربات در حال اجراست.'

def scheduler_loop():
    schedule.every().day.at("21:00").do(lambda: print("⚽️ شبیه‌سازی بازی‌ها..."))
    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"https://special-coach.onrender.com/{TOKEN}")  # 🔁 آدرس واقعی Render جایگزین کن
    threading.Thread(target=scheduler_loop).start()
    app.run(host="0.0.0.0", port=10000)
