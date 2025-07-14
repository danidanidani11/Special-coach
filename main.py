import telebot
from flask import Flask, request
import json, threading, time, schedule, random

TOKEN = '7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc'
ADMIN_ID = 5542927340
CHANNEL = '@Specialcoach1'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

users_file = 'users.json'
players_file = 'players.json'

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def get_user(uid):
    users = load_json(users_file)
    return users.get(str(uid), None)

def save_user(uid, user_data):
    users = load_json(users_file)
    users[str(uid)] = user_data
    save_json(users_file, users)

# ───── START + ثبت تیم ─────
@bot.message_handler(commands=['start'])
def start(m):
    users = load_json(users_file)
    if str(m.chat.id) in users:
        bot.send_message(m.chat.id, "👋 خوش برگشتی مربی!")
        return show_menu(m.chat.id)
    bot.send_message(m.chat.id, "⚽️ خوش اومدی به لیگ مربیان! اسم تیمت چیه؟")
    bot.register_next_step_handler(m, set_team_name)

def set_team_name(m):
    team = m.text.strip()
    players = random.sample(load_json(players_file), 11)
    user_data = {
        "team_name": team,
        "coins": 100,
        "gems": 5,
        "players": players,
        "formation": "4-4-2",
        "tactic": "تعادلی",
        "points": 0
    }
    save_user(m.chat.id, user_data)
    bot.send_message(m.chat.id, f"✅ تیم {team} ساخته شد!")
    show_menu(m.chat.id)

# ───── منوی اصلی ─────
def show_menu(cid):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 ترکیب و تاکتیک", "🛒 بازار نقل و انتقالات")
    markup.add("📊 جدول لیگ", "🪙 فروشگاه", "👤 پروفایل")
    bot.send_message(cid, "منوی اصلی:", reply_markup=markup)

# ───── تاکتیک روزانه ─────
@bot.message_handler(func=lambda m: m.text == "📋 ترکیب و تاکتیک")
def tactic_handler(m):
    bot.send_message(m.chat.id, "📐 یکی از تاکتیک‌های زیر رو انتخاب کن:\n1️⃣ ضدحمله\n2️⃣ پرس بالا\n3️⃣ تعادلی")
    bot.register_next_step_handler(m, set_tactic)

def set_tactic(m):
    t = m.text.strip()
    user = get_user(m.chat.id)
    if user:
        user["tactic"] = t
        save_user(m.chat.id, user)
        bot.send_message(m.chat.id, f"✅ تاکتیک روزانه تنظیم شد: {t}")
        show_menu(m.chat.id)

# ───── شبیه‌سازی بازی روزانه ─────
def simulate_daily_match():
    users = load_json(users_file)
    for uid, user in users.items():
        score = random.randint(0, 3)
        enemy_score = random.randint(0, 3)
        result = f"📊 نتیجه بازی روزانه:\n{user['team_name']} {score} - {enemy_score} حریف"
        if score > enemy_score:
            user["points"] += 3
            result += "\n🏆 پیروزی! +3 امتیاز"
        elif score == enemy_score:
            user["points"] += 1
            result += "\n🤝 مساوی! +1 امتیاز"
        else:
            result += "\n❌ شکست!"
        save_user(uid, user)
        try:
            bot.send_message(int(uid), result)
        except:
            continue

# ───── زمان‌بندی اجرای بازی روزانه ─────
def scheduler_loop():
    schedule.every().day.at("21:00").do(simulate_daily_match)
    while True:
        schedule.run_pending()
        time.sleep(10)

# ───── Flask برای اجرا روی Render ─────
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return 'ok'

@app.route('/')
def index():
    return 'Bot is running.'

def start_flask():
    app.run(host="0.0.0.0", port=10000)

# ───── شروع برنامه ─────
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"https://your-render-url.onrender.com/{TOKEN}")
    threading.Thread(target=scheduler_loop).start()
    start_flask()
