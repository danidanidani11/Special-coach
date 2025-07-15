import telebot
from telebot import types
import json, os
from flask import Flask, request
import datetime, threading, random

TOKEN = '7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

ADMIN_ID = 5542927340
CHANNEL_USERNAME = "Specialcoach1"

# مسیر فایل‌ها
if not os.path.exists("data"):
    os.makedirs("data")

users_path = "data/users.json"
players_path = "data/players.json"

# بارگذاری اولیه
if not os.path.exists(users_path):
    with open(users_path, "w") as f:
        json.dump({}, f)

with open(players_path, "r", encoding="utf-8") as f:
    players = json.load(f)

# بارگذاری کاربران
def load_users():
    with open(users_path, "r") as f:
        return json.load(f)

def save_users(data=None):
    with open(users_path, "w") as f:
        json.dump(data if data else users, f)

users = load_users()

# ۵ بازیکن اولیه به تیم اضافه شود
def assign_starting_players(uid):
    starter_names = ["player1", "player2", "player3", "player4", "player5"]
    starter_players = [p for p in players if p["name"] in starter_names]

    users[uid]["team_players"] = starter_players
    users[uid]["wallet"] = {"coins": 0, "gems": 0}
    users[uid]["score"] = 0
    save_users()

# منوی اصلی
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⚽ ترکیب و تاکتیک", "🛒 فروشگاه بازیکن")
    markup.add("🎮 بازی شبانه", "🏆 برترین‌ها")
    markup.add("👛 کیف پول", "🎁 پاداش روزانه")
    return markup

@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.from_user.id)

    # بررسی عضویت در کانال
    try:
        chat_member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", msg.from_user.id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}"))
            markup.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_sub"))
            bot.send_message(msg.chat.id, "🔒 لطفاً ابتدا در کانال عضو شوید:", reply_markup=markup)
            return
    except:
        bot.send_message(msg.chat.id, "⚠️ خطا در بررسی عضویت. لطفا مجددا امتحان کن.")
        return

    if uid in users and users[uid].get("registered"):
        bot.send_message(msg.chat.id, "👋 خوش برگشتی!", reply_markup=main_menu())
        return

    users[uid] = {"step": "ask_team", "registered": False}
    save_users()
    bot.send_message(msg.chat.id, "🏟 نام تیم خود را وارد کن:")

@bot.message_handler(func=lambda m: users.get(str(m.from_user.id), {}).get("step") == "ask_team")
def handle_team_name(msg):
    uid = str(msg.from_user.id)
    name = msg.text.strip()

    if len(name) < 3:
        bot.send_message(msg.chat.id, "❗ نام تیم باید حداقل ۳ کاراکتر باشد.")
        return

    users[uid]["team_name"] = name
    users[uid]["step"] = "ask_contact"
    save_users()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("ارسال شماره تماس", request_contact=True))
    bot.send_message(msg.chat.id, "📱 لطفاً شماره تماس خود را با دکمه زیر ارسال کن:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(msg):
    uid = str(msg.from_user.id)
    if users.get(uid, {}).get("step") != "ask_contact":
        return

    if not msg.contact or msg.contact.user_id != msg.from_user.id:
        bot.send_message(msg.chat.id, "❌ لطفاً فقط شماره خودت رو ارسال کن.")
        return

    users[uid]["phone"] = msg.contact.phone_number
    users[uid]["registered"] = True
    users[uid]["step"] = "registered"
    assign_starting_players(uid)
    save_users()

    bot.send_message(msg.chat.id, f"✅ ثبت‌نام انجام شد!\nخوش آمدی {users[uid]['team_name']} 🌟", reply_markup=main_menu())

def show_store(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    text = "🛒 لیست بازیکنان موجود:\n"
    for p in players:
        text += f"{p['name']} - {p['position']} | اورال: {p['overall']} | 💎 {p['price_gems']} جم یا 🪙 {p['price_coins']} سکه\n"
        markup.add(f"خرید {p['name']}")

    markup.add("بازگشت به منو")
    bot.send_message(msg.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text.startswith("خرید "))
def buy_player(msg):
    uid = str(msg.from_user.id)
    name = msg.text.replace("خرید ", "").strip()
    user = users.get(uid)

    player = next((p for p in players if p['name'].lower() == name.lower()), None)
    if not player:
        bot.send_message(msg.chat.id, "❌ بازیکن پیدا نشد.")
        return

    wallet = user.get("wallet", {"coins":0, "gems":0})
    if wallet["gems"] >= player["price_gems"]:
        wallet["gems"] -= player["price_gems"]
    elif wallet["coins"] >= player["price_coins"]:
        wallet["coins"] -= player["price_coins"]
    else:
        bot.send_message(msg.chat.id, "❌ سکه یا جم کافی ندارید.")
        return

    if "team_players" not in user:
        user["team_players"] = []

    if player in user["team_players"] or player["name"] in [p["name"] for p in user["team_players"]]:
        bot.send_message(msg.chat.id, "❌ این بازیکن قبلاً خریداری شده.")
        return

    if len(user["team_players"]) >= 8:
        bot.send_message(msg.chat.id, "❌ حداکثر ۸ بازیکن می‌تونی داشته باشی.")
        return

    user["team_players"].append(player)
    user["wallet"] = wallet
    users[uid] = user
    save_users()

    bot.send_message(msg.chat.id, f"✅ بازیکن {player['name']} به تیم شما اضافه شد.", reply_markup=main_menu())

def show_formation_menu(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid, {})
    team = user.get("team_players", [])

    gk = [p for p in team if p["position"] == "GK"]
    df = [p for p in team if p["position"] == "DF"]
    mf = [p for p in team if p["position"] == "MF"]
    fw = [p for p in team if p["position"] == "FW"]

    schematic = "📋 ترکیب تیم:\n\n"

    if fw:
        schematic += "⚔ مهاجم:\n" + " | ".join([p["name"] for p in fw]) + "\n\n"
    if mf:
        schematic += "🎯 هافبک:\n" + " | ".join([p["name"] for p in mf]) + "\n\n"
    if df:
        schematic += "🛡 مدافع:\n" + " | ".join([p["name"] for p in df]) + "\n\n"
    if gk:
        schematic += "🧤 دروازه‌بان:\n" + " | ".join([p["name"] for p in gk]) + "\n\n"

    if not team:
        schematic = "⚠️ هنوز بازیکنی در تیم شما نیست."

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بازگشت به منو")
    bot.send_message(msg.chat.id, schematic, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👛 کیف پول")
def show_wallet(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid, {})
    wallet = user.get("wallet", {"coins": 0, "gems": 0})
    text = f"""💼 کیف پول شما:

🪙 سکه: {wallet.get('coins', 0)}
💎 جم: {wallet.get('gems', 0)}

💳 آدرس ترون:
`TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb`

📤 برای خرید سکه یا جم، فیش خود را (عکس یا متن) ارسال کنید.
🔄 برای تبدیل ۱۰۰ سکه به ۱ جم دکمه زیر را بزنید."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔄 تبدیل سکه به جم", "بازگشت به منو")
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(content_types=['text', 'photo'])
def handle_payment(msg):
    uid = str(msg.from_user.id)
    if msg.chat.type != "private":
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{uid}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{uid}")
    )

    if msg.content_type == "text":
        bot.send_message(ADMIN_ID, f"🧾 فیش متنی:\nاز: {msg.from_user.first_name}\n\n{msg.text}", reply_markup=markup)
    elif msg.content_type == "photo":
        bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
        bot.send_message(ADMIN_ID, f"🧾 عکس فیش از: {msg.from_user.first_name}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def handle_receipt_decision(call):
    uid = call.data.split("_")[1]
    if str(call.from_user.id) != str(ADMIN_ID):
        return

    user = users.get(uid)
    if not user:
        return

    wallet = user.get("wallet", {"coins":0, "gems":0})
    if call.data.startswith("approve_"):
        wallet["coins"] += 100
        bot.edit_message_text("✅ فیش تایید شد. ۱۰۰ سکه اضافه شد.", call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text("❌ فیش رد شد.", call.message.chat.id, call.message.message_id)

    user["wallet"] = wallet
    users[uid] = user
    save_users()

@bot.message_handler(func=lambda m: m.text == "🔄 تبدیل سکه به جم")
def convert_coins(m):
    uid = str(m.from_user.id)
    user = users.get(uid)
    wallet = user.get("wallet", {"coins": 0, "gems": 0})
    if wallet["coins"] < 100:
        bot.send_message(m.chat.id, "❌ حداقل ۱۰۰ سکه لازم است.")
        return
    gems = wallet["coins"] // 100
    wallet["gems"] += gems
    wallet["coins"] %= 100
    user["wallet"] = wallet
    save_users()
    bot.send_message(m.chat.id, f"✅ {gems} جم اضافه شد.", reply_markup=main_menu())

# بازی شبانه
night_game_participants = set()
night_game_results = {}

@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def join_night_game(msg):
    uid = str(msg.from_user.id)
    if uid in night_game_participants:
        bot.send_message(msg.chat.id, "📌 قبلاً ثبت شده‌اید.")
    else:
        night_game_participants.add(uid)
        bot.send_message(msg.chat.id, "✅ در لیست بازی شبانه قرار گرفتید.")

def run_night_games():
    participants = list(night_game_participants)
    random.shuffle(participants)
    while len(participants) >= 2:
        uid1, uid2 = participants.pop(), participants.pop()
        u1, u2 = users[uid1], users[uid2]
        score1 = len(u1.get("team_players", [])) * 10 + u1.get("score", 0)
        score2 = len(u2.get("team_players", [])) * 10 + u2.get("score", 0)
        diff = score1 - score2 + random.randint(-10, 10)

        if diff > 5:
            winner, loser = uid1, uid2
            result = f"🏆 {u1['team_name']} برد!"
            update_result(uid1, True, False)
            update_result(uid2, False, False)
        elif diff < -5:
            winner, loser = uid2, uid1
            result = f"🏆 {u2['team_name']} برد!"
            update_result(uid2, True, False)
            update_result(uid1, False, False)
        else:
            result = "⚖️ بازی مساوی شد!"
            update_result(uid1, False, True)
            update_result(uid2, False, True)

        night_game_results[uid1] = {"opponent": uid2, "result": result}
        night_game_results[uid2] = {"opponent": uid1, "result": result}

    save_users()
    night_game_participants.clear()

def update_result(uid, win, draw):
    u = users.get(uid)
    wallet = u.get("wallet", {"coins":0, "gems":0})
    if win:
        u["score"] += 20
        wallet["coins"] += 100
    elif draw:
        u["score"] += 5
        wallet["coins"] += 40
    else:
        u["score"] -= 10
        wallet["coins"] = max(wallet["coins"] - 20, 0)
    u["wallet"] = wallet

def schedule_night_game():
    now = datetime.datetime.now()
    target = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    threading.Timer((target - now).total_seconds(), night_game_wrapper).start()

def night_game_wrapper():
    run_night_games()
    schedule_night_game()

schedule_night_game()

@bot.message_handler(func=lambda m: m.text == "📄 گزارش بازی")
def show_game_report(msg):
    uid = str(msg.from_user.id)
    res = night_game_results.get(uid)
    if not res:
        bot.send_message(msg.chat.id, "❌ گزارشی یافت نشد.")
        return
    opp = users.get(res["opponent"], {}).get("team_name", "حریف")
    bot.send_message(msg.chat.id, f"🎮 بازی مقابل {opp}\nنتیجه: {res['result']}")

# پاداش روزانه
claimed_today = set()

@bot.message_handler(func=lambda m: m.text == "🎁 پاداش روزانه")
def daily_reward(msg):
    uid = str(msg.from_user.id)
    key = f"{uid}_{datetime.date.today().isoformat()}"
    if key in claimed_today:
        bot.send_message(msg.chat.id, "❗ امروز پاداش را دریافت کرده‌ای.")
        return
    user = users.get(uid)
    wallet = user.get("wallet", {"coins":0, "gems":0})
    wallet["gems"] += 2
    user["wallet"] = wallet
    users[uid] = user
    claimed_today.add(key)
    save_users()
    bot.send_message(msg.chat.id, "🎉 ۲ جم به شما اهدا شد.", reply_markup=main_menu())

# اجرای Flask
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
