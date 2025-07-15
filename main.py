import telebot
from telebot import types
import json, os
from flask import Flask, request
import random
import datetime
import threading

TOKEN = '7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

ADMIN_ID = 5542927340
CHANNEL_USERNAME = "Specialcoach1"

if not os.path.exists("data"):
    os.makedirs("data")

users_path = "data/users.json"
players_path = "data/players.json"

# ایجاد فایل‌های مورد نیاز اگر وجود ندارند
if not os.path.exists(users_path):
    with open(users_path, "w") as f:
        json.dump({}, f)

if not os.path.exists(players_path):
    # ایجاد ۵ بازیکن اولیه ضعیف
    starting_players = [
        {"name": "بازیکن ۱", "position": "FW", "overall": 50, "price_coins": 100, "price_gems": 1},
        {"name": "بازیکن ۲", "position": "MF", "overall": 45, "price_coins": 90, "price_gems": 1},
        {"name": "بازیکن ۳", "position": "DF", "overall": 40, "price_coins": 80, "price_gems": 1},
        {"name": "بازیکن ۴", "position": "DF", "overall": 42, "price_coins": 85, "price_gems": 1},
        {"name": "بازیکن ۵", "position": "GK", "overall": 38, "price_coins": 70, "price_gems": 1}
    ]
    with open(players_path, "w", encoding="utf-8") as f:
        json.dump(starting_players, f)

def load_users():
    with open(users_path, "r") as f:
        return json.load(f)

def load_players():
    with open(players_path, "r", encoding="utf-8") as f:
        return json.load(f)

def assign_starting_players(uid):
    starting_players = load_players()[:5]  # ۵ بازیکن اولیه ضعیف
    
    user = users.get(uid)
    if not user:
        return

    user["team_players"] = [p["name"] for p in starting_players]
    users[uid] = user
    save_users()

def save_users(data=None):
    if data:
        with open(users_path, "w") as f:
            json.dump(data, f)
    else:
        with open(users_path, "w") as f:
            json.dump(users, f)

users = load_users()
players = load_players()

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⚽ ترکیب و تاکتیک", "🛒 فروشگاه بازیکن")
    markup.add("🎮 بازی شبانه", "🏆 برترین‌ها")
    markup.add("👛 کیف پول", "🎁 پاداش روزانه")
    return markup

def back_to_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بازگشت به منو")
    return markup

@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.from_user.id)

    # عضویت اجباری
    try:
        chat_member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", msg.from_user.id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}"))
            markup.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_sub"))
            bot.send_message(msg.chat.id, "🔒 برای استفاده از ربات، ابتدا در کانال عضو شوید:", reply_markup=markup)
            return
    except:
        bot.send_message(msg.chat.id, "⚠️ خطا در بررسی عضویت. دوباره تلاش کن.")
        return

    # اگر ثبت‌نام کرده، مستقیم منو
    if uid in users and users[uid].get("registered"):
        bot.send_message(msg.chat.id, "👋 خوش برگشتی!", reply_markup=main_menu())
        return

    # شروع ثبت‌نام جدید
    users[uid] = {"step": "ask_team", "registered": False, "wallet": {"coins": 100, "gems": 5}}  # اعتبار اولیه
    save_users()
    bot.send_message(msg.chat.id, "🏟 نام تیم خود را وارد کن:")

@bot.message_handler(func=lambda m: users.get(str(m.from_user.id), {}).get("step") == "ask_team")
def ask_team_handler(msg):
    uid = str(msg.from_user.id)
    team_name = msg.text.strip()
    if len(team_name) < 3:
        bot.send_message(msg.chat.id, "اسم تیم باید حداقل ۳ کاراکتر باشه. دوباره وارد کن:")
        return
    users[uid]["team_name"] = team_name
    users[uid]["step"] = "ask_contact"
    save_users()
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("ارسال شماره تماس", request_contact=True))
    bot.send_message(msg.chat.id, "📱 لطفا شماره تماس خود را با دکمه زیر ارسال کن:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def contact_handler(msg):
    uid = str(msg.from_user.id)
    if users.get(uid, {}).get("step") != "ask_contact":
        return
    if msg.contact is None or msg.contact.user_id != msg.from_user.id:
        bot.send_message(msg.chat.id, "⚠️ لطفا فقط شماره تماس خودت رو ارسال کن.")
        return
    users[uid]["phone"] = msg.contact.phone_number
    users[uid]["registered"] = True
    users[uid]["step"] = "registered"
    assign_starting_players(uid)  # اختصاص بازیکنان اولیه
    save_users()
    bot.send_message(msg.chat.id, f"✅ ثبت‌نام شما با موفقیت انجام شد.\n\nخوش آمدید {users[uid]['team_name']} عزیز!", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    try:
        chat_member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", call.from_user.id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            bot.answer_callback_query(call.id, "✅ عضویت تایید شد!")

            uid = str(call.from_user.id)
            if uid in users and users[uid].get("registered"):
                bot.send_message(call.message.chat.id, "👋 خوش آمدی!", reply_markup=main_menu())
            else:
                users[uid] = {"step": "ask_team", "registered": False, "wallet": {"coins": 100, "gems": 5}}
                save_users()
                bot.send_message(call.message.chat.id, "🏟 نام تیم خود را وارد کن:")
        else:
            bot.answer_callback_query(call.id, "⛔ هنوز عضو نیستی!", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, "⛔ خطا در بررسی عضویت. لطفا دوباره امتحان کن.", show_alert=True)

@bot.message_handler(func=lambda m: users.get(str(m.from_user.id), {}).get("registered") == True)
def main_menu_handler(msg):
    text = msg.text

    if text == "⚽ ترکیب و تاکتیک":
        show_formation_menu(msg)
    elif text == "🛒 فروشگاه بازیکن":
        show_store(msg)
    elif text == "🎮 بازی شبانه":
        join_night_game(msg)
    elif text == "🏆 برترین‌ها":
        show_leaderboard(msg)
    elif text == "👛 کیف پول":
        show_wallet(msg)
    elif text == "🎁 پاداش روزانه":
        give_daily_reward(msg)
    elif text == "بازگشت به منو":
        bot.send_message(msg.chat.id, "🔙 بازگشت به منوی اصلی", reply_markup=main_menu())
    else:
        bot.send_message(msg.chat.id, "لطفا از منوی پایین استفاده کنید.", reply_markup=main_menu())

def show_formation_menu(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user:
        bot.send_message(msg.chat.id, "❌ ابتدا ثبت‌نام کنید.")
        return

    team_player_names = user.get("team_players", [])
    team_players = [p for p in players if p["name"] in team_player_names]

    if not team_players:
        bot.send_message(msg.chat.id, "🏟 هنوز بازیکنی در تیم خود ندارید.")
        return

    # دسته‌بندی بازیکنان بر اساس پست
    gk = [p for p in team_players if p["position"] == "GK"]
    defn = [p for p in team_players if p["position"] == "DF"]
    mid = [p for p in team_players if p["position"] == "MF"]
    fw = [p for p in team_players if p["position"] == "FW"]

    # شماتیک متنی ساده
    schematic = "📋 ترکیب تیم شما:\n\n"

    # مهاجمان (مثلا 2 نفر در خط حمله)
    schematic += "⚽ خط حمله:\n"
    for i in range(min(2, len(fw))):
        schematic += f"• {fw[i]['name']} (قدرت: {fw[i]['overall']})\n"

    # هافبک‌ها (2 نفر)
    schematic += "\n🔄 هافبک‌ها:\n"
    for i in range(min(2, len(mid))):
        schematic += f"• {mid[i]['name']} (قدرت: {mid[i]['overall']})\n"

    # مدافعان (3 نفر)
    schematic += "\n🛡 مدافعان:\n"
    for i in range(min(3, len(defn))):
        schematic += f"• {defn[i]['name']} (قدرت: {defn[i]['overall']})\n"

    # دروازه‌بان (1 نفر)
    if gk:
        schematic += "\n🧤 دروازه‌بان:\n"
        schematic += f"• {gk[0]['name']} (قدرت: {gk[0]['overall']})\n"

    bot.send_message(msg.chat.id, schematic, reply_markup=back_to_menu_keyboard())

def show_store(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user:
        bot.send_message(msg.chat.id, "❌ ابتدا ثبت‌نام کنید.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    text = "🛒 فروشگاه بازیکنان:\n\n"
    
    for i, p in enumerate(players):
        owned = "✅ (مال شما)" if p["name"] in user.get("team_players", []) else ""
        text += f"{i+1}. {p['name']} - پست: {p['position']}\nقدرت: {p['overall']} - قیمت: {p['price_gems']} جم یا {p['price_coins']} سکه {owned}\n\n"
        markup.add(f"خرید {p['name']}")
    
    markup.add("بازگشت به منو")
    bot.send_message(msg.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text.startswith("خرید "))
def buy_player(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user:
        bot.send_message(msg.chat.id, "❌ ابتدا ثبت‌نام کنید.")
        return

    player_name = msg.text.replace("خرید ", "").strip()
    player = next((p for p in players if p["name"] == player_name), None)
    
    if not player:
        bot.send_message(msg.chat.id, "❌ بازیکن موردنظر پیدا نشد.")
        return

    if player["name"] in user.get("team_players", []):
        bot.send_message(msg.chat.id, "❌ این بازیکن قبلا خریداری شده است.")
        return

    wallet = user.get("wallet", {"coins": 0, "gems": 0})
    
    # چک کردن موجودی
    if wallet["gems"] >= player["price_gems"]:
        wallet["gems"] -= player["price_gems"]
        payment_method = "جم"
    elif wallet["coins"] >= player["price_coins"]:
        wallet["coins"] -= player["price_coins"]
        payment_method = "سکه"
    else:
        bot.send_message(msg.chat.id, "❌ موجودی کافی ندارید.")
        return

    # اضافه کردن بازیکن به تیم
    if "team_players" not in user:
        user["team_players"] = []
    
    user["team_players"].append(player["name"])
    user["wallet"] = wallet
    users[uid] = user
    save_users()

    bot.send_message(msg.chat.id, f"✅ بازیکن {player['name']} با موفقیت خریداری شد. (پرداخت با {payment_method})", reply_markup=back_to_menu_keyboard())

@bot.message_handler(func=lambda m: m.text == "👛 کیف پول")
def show_wallet(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user:
        bot.send_message(msg.chat.id, "❌ ابتدا ثبت‌نام کنید.")
        return

    wallet = user.get("wallet", {"coins": 0, "gems": 0})
    text = f"""💰 کیف پول شما:

سکه‌ها: {wallet['coins']} 🪙
جم‌ها: {wallet['gems']} 💎

💳 آدرس ترون برای واریز:
`TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb`

💸 نرخ تبدیل:
۱۰۰ سکه = ۱ جم"""

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🔄 تبدیل سکه به جم", "🔙 بازگشت به منو")
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔄 تبدیل سکه به جم")
def convert_coins_to_gems(msg):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user:
        bot.send_message(msg.chat.id, "❌ ابتدا ثبت‌نام کنید.")
        return

    wallet = user.get("wallet", {"coins": 0, "gems": 0})
    coins = wallet["coins"]
    
    if coins < 100:
        bot.send_message(msg.chat.id, "❌ حداقل ۱۰۰ سکه نیاز دارید برای تبدیل به ۱ جم.")
        return

    gems_to_add = coins // 100
    coins_left = coins % 100

    wallet["gems"] += gems_to_add
    wallet["coins"] = coins_left
    user["wallet"] = wallet
    users[uid] = user
    save_users()

    bot.send_message(msg.chat.id, f"✅ تبدیل موفق:\n{gems_to_add} جم اضافه شد\nسکه باقیمانده: {coins_left}", reply_markup=back_to_menu_keyboard())

@bot.message_handler(content_types=['photo'])
def handle_payment_receipt(msg):
    uid = str(msg.from_user.id)
    admin_id = ADMIN_ID

    # ارسال عکس به ادمین
    bot.forward_message(admin_id, msg.chat.id, msg.message_id)
    
    # ارسال اطلاعات کاربر به ادمین
    user = users.get(uid, {})
    user_info = f"User ID: {uid}\nName: {msg.from_user.first_name}\nTeam: {user.get('team_name', 'N/A')}"
    bot.send_message(admin_id, f"🧾 فیش پرداختی جدید:\n{user_info}")

    # دکمه تایید و رد برای ادمین
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{uid}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{uid}")
    )
    bot.send_message(admin_id, "لطفا وضعیت فیش را تایید یا رد کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def handle_admin_receipt_decision(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ شما اجازه انجام این کار را ندارید.")
        return

    uid = call.data.split("_")[1]
    user = users.get(uid)
    if not user:
        bot.answer_callback_query(call.id, "❌ کاربر پیدا نشد.")
        return

    if call.data.startswith("approve_"):
        wallet = user.get("wallet", {"coins": 0, "gems": 0})
        wallet["coins"] = wallet.get("coins", 0) + 100
        user["wallet"] = wallet
        users[uid] = user
        save_users()
        
        bot.edit_message_text("✅ فیش تایید شد و ۱۰۰ سکه به کیف پول اضافه شد.", call.message.chat.id, call.message.message_id)
        bot.send_message(uid, "✅ فیش پرداخت شما تایید شد و ۱۰۰ سکه به کیف پول شما اضافه شد.")
    else:
        bot.edit_message_text("❌ فیش رد شد.", call.message.chat.id, call.message.message_id)
        bot.send_message(uid, "❌ فیش پرداخت شما رد شد. لطفا با پشتیبانی تماس بگیرید.")

# بخش بازی شبانه
night_game_participants = set()
night_game_results = {}

def run_night_games():
    participants = list(night_game_participants)
    random.shuffle(participants)

    while len(participants) >= 2:
        uid1 = participants.pop()
        uid2 = participants.pop()

        user1 = users.get(uid1, {})
        user2 = users.get(uid2, {})

        # محاسبه قدرت تیم‌ها
        team1_players = [p for p in players if p["name"] in user1.get("team_players", [])]
        team2_players = [p for p in players if p["name"] in user2.get("team_players", [])]
        
        power1 = sum(p["overall"] for p in team1_players) + random.randint(-10, 10)
        power2 = sum(p["overall"] for p in team2_players) + random.randint(-10, 10)

        diff = power1 - power2

        if diff > 5:
            winner, loser = uid1, uid2
            result_text = f"🏆 تیم {user1.get('team_name','بازیکن1')} برنده شد!"
            score1, score2 = 3, 1
        elif diff < -5:
            winner, loser = uid2, uid1
            result_text = f"🏆 تیم {user2.get('team_name','بازیکن2')} برنده شد!"
            score1, score2 = 1, 3
        else:
            winner = loser = None
            result_text = "⚖️ بازی مساوی شد!"
            score1 = score2 = 2

        # ذخیره نتیجه
        night_game_results[uid1] = {"opponent": uid2, "result": result_text, "score": score1}
        night_game_results[uid2] = {"opponent": uid1, "result": result_text, "score": score2}

        # به‌روزرسانی امتیاز و سکه‌ها
        def update_user(uid, is_winner, is_draw):
            u = users.get(uid)
            if not u:
                return
            wallet = u.get("wallet", {"coins":0, "gems":0})
            u["score"] = u.get("score", 0)
            u["wins"] = u.get("wins", 0)
            u["draws"] = u.get("draws", 0)
            u["losses"] = u.get("losses", 0)

            if is_winner:
                u["score"] += 20
                wallet["coins"] = wallet.get("coins",0) + 100
                u["wins"] += 1
            elif is_draw:
                u["score"] += 5
                wallet["coins"] = wallet.get("coins",0) + 40
                u["draws"] += 1
            else:
                u["score"] = max(u.get("score",0) - 10, 0)
                wallet["coins"] = max(wallet.get("coins",0) - 20, 0)
                u["losses"] += 1
            u["wallet"] = wallet

        if winner is None:
            update_user(uid1, False, True)
            update_user(uid2, False, True)
        else:
            update_user(winner, True, False)
            update_user(loser, False, False)

        save_users()

        # ارسال نتایج به کاربران
        bot.send_message(uid1, f"🎮 نتیجه بازی شبانه:\nحریف: {user2.get('team_name', 'تیم ناشناس')}\n{result_text}")
        bot.send_message(uid2, f"🎮 نتیجه بازی شبانه:\nحریف: {user1.get('team_name', 'تیم ناشناس')}\n{result_text}")

    night_game_participants.clear()

def schedule_night_game():
    now = datetime.datetime.now()
    target = now.replace(hour=21, minute=0, second=0, microsecond=0)  # ساعت 9 شب
    if now > target:
        target += datetime.timedelta(days=1)
    delay = (target - now).total_seconds()
    threading.Timer(delay, night_game_wrapper).start()

def night_game_wrapper():
    run_night_games()
    schedule_night_game()  # برنامه‌ریزی برای روز بعد

# شروع زمان‌بندی بازی شبانه
schedule_night_game()

@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def join_night_game(msg):
    uid = str(msg.from_user.id)
    if uid in night_game_participants:
        bot.send_message(msg.chat.id, "✅ شما قبلا در بازی شبانه ثبت‌نام کرده‌اید.")
    else:
        night_game_participants.add(uid)
        bot.send_message(msg.chat.id, "🎮 شما در لیست بازی شبانه ثبت شدید. ساعت ۹ شب بازی شروع می‌شود!")

def show_leaderboard(msg):
    # رتبه بندی بر اساس امتیاز
    leaderboard = sorted(
        [(uid, u.get("score", 0), u.get("team_name", "ناشناس")) for uid, u in users.items() if u.get("registered")],
        key=lambda x: x[1],
        reverse=True
    )[:10]

    text = "🏆 جدول برترین‌ها:\n\n"
    for i, (uid, score, name) in enumerate(leaderboard, start=1):
        text += f"{i}. {name} - امتیاز: {score}\n"

    bot.send_message(msg.chat.id, text, reply_markup=main_menu())

# پاداش روزانه
daily_reward_claimed = set()

@bot.message_handler(func=lambda m: m.text == "🎁 پاداش روزانه")
def give_daily_reward(msg):
    uid = str(msg.from_user.id)
    today = datetime.date.today().isoformat()
    key = f"{uid}_{today}"
    
    if key in daily_reward_claimed:
        bot.send_message(msg.chat.id, "❌ امروز پاداشت رو گرفتی، لطفا فردا بیا.")
        return

    wallet = users[uid].get("wallet", {"coins":0, "gems":0})
    wallet["gems"] = wallet.get("gems", 0) + 2
    users[uid]["wallet"] = wallet
    daily_reward_claimed.add(key)
    save_users()
    
    bot.send_message(msg.chat.id, "🎉 ۲ جم به کیف پول شما اضافه شد!", reply_markup=main_menu())

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
