import os
import json
import threading
import time
import random
from datetime import datetime, timedelta

import telebot
from telebot import types
from flask import Flask, request

TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
ADMIN_ID = 5542927340
CHANNEL = "Specialcoach1"
TRON_ADDRESS = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.mkdir(DATA_FOLDER)

USERS_FILE = os.path.join(DATA_FOLDER, "users.json")
PLAYERS_FILE = os.path.join(DATA_FOLDER, "players.json")
NIGHT_GAME_FILE = os.path.join(DATA_FOLDER, "night_game.json")

# --- بارگذاری و ذخیره داده‌ها ---

def load_json(filename):
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

users = load_json(USERS_FILE)  # ساختار: {user_id: {...}}
players = load_json(PLAYERS_FILE)  # ساختار: {player_id: {...}}
night_game = load_json(NIGHT_GAME_FILE)  # ساختار: {"players": [user_id,...], "matches": {...}}

if "players" not in night_game:
    night_game["players"] = []
if "matches" not in night_game:
    night_game["matches"] = {}

# --- لیست بازیکنان نمونه (پست، اسم، قدرت، قیمت جم، قیمت سکه) ---

if not players:
    # بار اول، ۵۰ بازیکن واقعی نمونه (با پست)
    sample_players = [
        {"id": 1, "name": "Ter Stegen", "position": "GK", "overall": 88, "price_gem": 20, "price_coin": 200},
        {"id": 2, "name": "Sergio Ramos", "position": "DEF", "overall": 85, "price_gem": 18, "price_coin": 180},
        {"id": 3, "name": "Xavi", "position": "MID", "overall": 86, "price_gem": 19, "price_coin": 190},
        {"id": 4, "name": "Messi", "position": "FWD", "overall": 93, "price_gem": 40, "price_coin": 400},
        {"id": 5, "name": "Suarez", "position": "FWD", "overall": 89, "price_gem": 30, "price_coin": 300},
        # ... بقیه ۴۵ بازیکن ضعیف و خوب رو مشابه اضافه کن
    ]
    for p in sample_players:
        players[str(p["id"])] = p
    save_json(PLAYERS_FILE, players)

# --- منوی اصلی ---

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 بازی شبانه", "🏆 برترین‌ها")
    markup.add("🧠 ترکیب و تاکتیک", "🛒 فروشگاه بازیکن")
    markup.add("💰 کیف پول", "🎁 پاداش روزانه")
    markup.add("بازگشت به منو")
    return markup

# --- ثبت‌نام اجباری ---

def save_users():
    save_json(USERS_FILE, users)

@bot.message_handler(commands=["start"])
def handle_start(msg):
    uid = str(msg.from_user.id)
    if uid in users and users[uid].get("registered"):
        bot.send_message(uid, "👋 خوش آمدی به منوی اصلی!", reply_markup=main_menu())
        return

    users[uid] = {
        "registered": False,
        "step": "ask_team_name",
        "team_name": None,
        "phone": None,
        "players": [],
        "coins": 0,
        "gems": 0,
        "score": 0,
        "wins": 0,
        "games_played": 0,
        "formation": "1-4-3",
        "tactic": "متعادل",
        "style": "پاسکاری",
        "offside_trap": False,
        "pressing": "پرس ۱۰۰ درصد",
    }
    save_users()
    bot.send_message(uid, "لطفا نام تیم خود را وارد کنید:")

@bot.message_handler(func=lambda m: users.get(str(m.from_user.id), {}).get("step") == "ask_team_name")
def ask_team_name(msg):
    uid = str(msg.from_user.id)
    team_name = msg.text.strip()
    if len(team_name) < 3:
        bot.send_message(msg.chat.id, "نام تیم باید حداقل ۳ حرف باشد. دوباره وارد کنید:")
        return
    users[uid]["team_name"] = team_name
    users[uid]["step"] = "ask_phone"
    save_users()
    # درخواست شماره تماس با دکمه share contact
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_phone = types.KeyboardButton("ارسال شماره تماس", request_contact=True)
    markup.add(button_phone)
    bot.send_message(msg.chat.id, "لطفا شماره تماس خود را با دکمه زیر ارسال کنید:", reply_markup=markup)

@bot.message_handler(content_types=["contact"])
def handle_contact(msg):
    uid = str(msg.from_user.id)
    if users.get(uid, {}).get("step") != "ask_phone":
        bot.send_message(msg.chat.id, "برای ثبت نام ابتدا نام تیم را وارد کنید.")
        return
    contact = msg.contact
    if contact.user_id != int(uid):
        bot.send_message(msg.chat.id, "لطفا شماره تماس خود را ارسال کنید.")
        return
    users[uid]["phone"] = contact.phone_number
    users[uid]["registered"] = True
    users[uid]["step"] = None
    save_users()
    bot.send_message(msg.chat.id, "ثبت‌نام با موفقیت انجام شد. به منو برگشتید.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: users.get(str(m.from_user.id), {}).get("step") == "ask_phone")
def ask_phone_manual(msg):
    # اگر کاربر شماره نداد و دستی نوشت، تذکر بده که باید با دکمه ارسال کنه
    bot.send_message(msg.chat.id, "لطفا شماره تماس خود را با دکمه مخصوص ارسال کنید.")

# --- پاداش روزانه ---

daily_bonus_claimed = {}

@bot.message_handler(func=lambda m: m.text and m.text.strip() == "🎁 پاداش روزانه")
def handle_daily_bonus(msg):
    uid = str(msg.from_user.id)
    today = datetime.now().date()
    last_claim = daily_bonus_claimed.get(uid)
    if last_claim == today:
        bot.send_message(msg.chat.id, "شما امروز پاداش را دریافت کرده‌اید.", reply_markup=main_menu())
        return
    users[uid]["gems"] = users[uid].get("gems", 0) + 2
    daily_bonus_claimed[uid] = today
    save_users()
    bot.send_message(msg.chat.id, "🎉 روزانه ۲ جم به شما اضافه شد.", reply_markup=main_menu())

# --- بازی شبانه ---

def save_night_game():
    save_json(NIGHT_GAME_FILE, night_game)

@bot.message_handler(func=lambda m: m.text and m.text.strip() == "🎮 بازی شبانه")
def handle_night_game(msg):
    uid = str(msg.from_user.id)
    if not users.get(uid, {}).get("registered"):
        bot.send_message(msg.chat.id, "ابتدا ثبت‌نام کنید.", reply_markup=main_menu())
        return
    if uid not in night_game["players"]:
        night_game["players"].append(uid)
        save_night_game()
        bot.send_message(msg.chat.id, "✅ شما در لیست شرکت‌کنندگان بازی شبانه قرار گرفتید. ساعت ۹ شب بازی شروع می‌شود!", reply_markup=main_menu())
    else:
        bot.send_message(msg.chat.id, "شما قبلا در لیست شرکت‌کنندگان هستید.", reply_markup=main_menu())

# --- زمان‌بندی بازی شبانه ---

def game_simulation():
    while True:
        now = datetime.now()
        if now.hour == 21 and now.minute == 0:
            # شروع بازی
            players_in_game = night_game.get("players", [])
            random.shuffle(players_in_game)
            matches = {}
            results_texts = {}
            for i in range(0, len(players_in_game) - 1, 2):
                p1 = players_in_game[i]
                p2 = players_in_game[i+1]

                # شبیه‌سازی منطقی بازی بر اساس تاکتیک و قدرت بازیکنان (مثلاً ساده)
                user1 = users[p1]
                user2 = users[p2]

                score1 = random.randint(0,3) + (5 if user1.get("tactic") == "هجومی" else 0)
                score2 = random.randint(0,3) + (5 if user2.get("tactic") == "هجومی" else 0)

                if score1 > score2:
                    winner = p1
                    users[p1]["score"] = users[p1].get("score",0) + 20
                    users[p1]["coins"] = users[p1].get("coins",0) + 100
                    users[p1]["wins"] = users[p1].get("wins",0) + 1
                    users[p2]["score"] = users[p2].get("score",0) - 10
                    users[p2]["coins"] = users[p2].get("coins",0) + 20
                elif score2 > score1:
                    winner = p2
                    users[p2]["score"] = users[p2].get("score",0) + 20
                    users[p2]["coins"] = users[p2].get("coins",0) + 100
                    users[p2]["wins"] = users[p2].get("wins",0) + 1
                    users[p1]["score"] = users[p1].get("score",0) - 10
                    users[p1]["coins"] = users[p1].get("coins",0) + 20
                else:
                    winner = None
                    users[p1]["score"] = users[p1].get("score",0) + 5
                    users[p2]["score"] = users[p2].get("score",0) + 5
                    users[p1]["coins"] = users[p1].get("coins",0) + 40
                    users[p2]["coins"] = users[p2].get("coins",0) + 40

                users[p1]["games_played"] = users[p1].get("games_played",0) + 1
                users[p2]["games_played"] = users[p2].get("games_played",0) + 1

                # گزارش ساده
                results_texts[p1] = f"⚽ بازی شبانه تمام شد. نتیجه: {score1} - {score2}."
                results_texts[p2] = f"⚽ بازی شبانه تمام شد. نتیجه: {score1} - {score2}."

            # ذخیره نتایج
            night_game["matches"] = results_texts
            night_game["players"] = []  # خالی کردن لیست بعد از بازی
            save_night_game()
            save_users()

            # ارسال گزارش به همه بازیکنان
            for uid, text in results_texts.items():
                try:
                    bot.send_message(int(uid), text, reply_markup=main_menu())
                except Exception as e:
                    print(f"Error sending match result to {uid}: {e}")

        time.sleep(30)

# --- برترین‌ها ---

@bot.message_handler(func=lambda m: m.text and m.text.strip() == "🏆 برترین‌ها")
def handle_leaderboard(msg):
    leaderboard_text = "🏆 برترین‌ها:\n\n"
    ranked = sorted(users.items(), key=lambda x: x[1].get("score", 0), reverse=True)[:10]
    for i, (uid, user) in enumerate(ranked, start=1):
        wins = user.get("wins", 0)
        total_games = user.get("games_played", 1)
        win_rate = int((wins / total_games) * 100) if total_games > 0 else 0
        leaderboard_text += f"{i}. {user.get('team_name', 'ناشناخته')}: {win_rate}% برد - {user.get('score', 0)} امتیاز\n"
    bot.send_message(msg.chat.id, leaderboard_text, reply_markup=main_menu())

# --- فروشگاه بازیکن ---

@bot.message_handler(func=lambda m: m.text and m.text.strip() == "🛒 فروشگاه بازیکن")
def handle_store(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user:
        bot.send_message(msg.chat.id, "ابتدا ثبت‌نام کنید.", reply_markup=main_menu())
        return

    markup = types.InlineKeyboardMarkup()
    for pid, p in players.items():
        btn_text = f"{p['name']} ({p['position']}) - {p['price_gem']} جم / {p['price_coin']} سکه"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{pid}"))

    bot.send_message(msg.chat.id, "بازیکنان قابل خرید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy_player(call):
    uid = str(call.from_user.id)
    pid = call.data.split("_")[1]
    user = users.get(uid)
    player = players.get(pid)
    if not user or not player:
        bot.answer_callback_query(call.id, "خطا در اطلاعات.")
        return

    # اولویت خرید با جم
    if user.get("gems", 0) >= player["price_gem"]:
        user["gems"] -= player["price_gem"]
        user["players"].append(pid)
        bot.answer_callback_query(call.id, f"بازیکن {player['name']} با جم خریداری شد.")
        save_users()
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        return
    # بعد سکه
    if user.get("coins", 0) >= player["price_coin"]:
        user["coins"] -= player["price_coin"]
        user["players"].append(pid)
        bot.answer_callback_query(call.id, f"بازیکن {player['name']} با سکه خریداری شد.")
        save_users()
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        return

    bot.answer_callback_query(call.id, "جم یا سکه کافی ندارید.")

# --- بازگشت به منو ---

@bot.message_handler(func=lambda m: m.text and m.text.strip() == "بازگشت به منو")
def handle_back(msg):
    bot.send_message(msg.chat.id, "🔙 بازگشت به منو", reply_markup=main_menu())

# --- اجرای ترد بازی شبانه ---

threading.Thread(target=game_simulation, daemon=True).start()

# --- اجرای ربات در وب (برای Render) ---

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return {"ok": True}

@app.route("/", methods=["GET"])
def root():
    return "Football Bot is running!"

bot.remove_webhook()
bot.set_webhook(url=f"https://special-coach.onrender.com/{TOKEN}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
