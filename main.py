import telebot
from telebot import types
import json, os
from flask import Flask, request

TOKEN = '7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

ADMIN_ID = 5542927340
CHANNEL_USERNAME = "Specialcoach1"

if not os.path.exists("data"):
    os.makedirs("data")

users_path = "data/users.json"
if not os.path.exists(users_path):
    with open(users_path, "w") as f:
        json.dump({}, f)

def load_users():
    with open(users_path, "r") as f:
        return json.load(f)

def save_users(data=None):
    if data:
        with open(users_path, "w") as f:
            json.dump(data, f)
    else:
        with open(users_path, "w") as f:
            json.dump(users, f)

users = load_users()

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⚽ ترکیب و تاکتیک", "🛒 فروشگاه بازیکن")
    markup.add("🎮 بازی شبانه", "🏆 برترین‌ها")
    markup.add("👛 کیف پول", "🎁 پاداش روزانه")
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
    users[uid] = {"step": "ask_team", "registered": False}
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
                users[uid] = {"step": "ask_team", "registered": False}
                save_users()
                bot.send_message(call.message.chat.id, "🏟 نام تیم خود را وارد کن:")
        else:
            bot.answer_callback_query(call.id, "⛔ هنوز عضو نیستی!", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, "⛔ خطا در بررسی عضویت. لطفا دوباره امتحان کن.", show_alert=True)

# لیست بازیکنان نمونه (می‌تونی این رو جداگانه بذاری و از فایل بارگذاری کنی)
players = [
    # بازیکنان ضعیف (قیمت کم)
    {"name": "Player A", "overall": 60, "price_coins": 10, "price_gems": 1, "position": "FW"},
    {"name": "Player B", "overall": 62, "price_coins": 15, "price_gems": 1, "position": "MF"},
    # ... 23 بازیکن ضعیف دیگه
    # بازیکنان قوی (قیمت بالا)
    {"name": "Star Player 1", "overall": 90, "price_coins": 300, "price_gems": 50, "position": "FW"},
    {"name": "Star Player 2", "overall": 88, "price_coins": 250, "price_gems": 45, "position": "GK"},
    # ... بقیه بازیکنان خوب
]

# منوی اصلی
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
    # فرض کن users[uid]["team_players"] لیست بازیکنان خریداری شده است
    # شماتیک ساده:
    team_players = users[uid].get("team_players", [])

    # دسته‌بندی بازیکنان بر اساس پست
    gk = [p for p in team_players if p["position"] == "GK"]
    defn = [p for p in team_players if p["position"] == "DF"]
    mid = [p for p in team_players if p["position"] == "MF"]
    fw = [p for p in team_players if p["position"] == "FW"]

    # شماتیک متنی ساده
    schematic = ""

    # مهاجمان (مثلا 2 نفر در خط حمله)
    for i in range(min(2, len(fw))):
        schematic += fw[i]["name"].ljust(15)
    schematic += "\n"

    # هافبک‌ها (2 نفر)
    for i in range(min(2, len(mid))):
        schematic += mid[i]["name"].ljust(15)
    schematic += "\n"

    # مدافعان (3 نفر)
    for i in range(min(3, len(defn))):
        schematic += defn[i]["name"].ljust(15)
    schematic += "\n"

    # دروازه‌بان (1 نفر)
    if gk:
        schematic += gk[0]["name"].ljust(15) + "\n"

    if schematic.strip() == "":
        schematic = "🏟 هنوز بازیکنی نخریدی."

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بازگشت به منو")
    bot.send_message(msg.chat.id, f"📋 ترکیب شماتیک تیم شما:\n\n{schematic}", reply_markup=markup)

def show_store(msg):
    uid = str(msg.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # نمایش 5 بازیکن نمونه برای خرید
    text = "🛒 فروشگاه بازیکنان:\n"
    for i, p in enumerate(players[:5]):
        text += f"{i+1}. {p['name']} - اورال: {p['overall']} - قیمت: {p['price_gems']} جم و {p['price_coins']} سکه\n"
        markup.add(f"خرید {p['name']}")
    markup.add("بازگشت به منو")
    bot.send_message(msg.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: any(p['name'].lower() == m.text.lower() for p in players))
def buy_player(msg):
    uid = str(msg.from_user.id)
    player_name = msg.text.strip().lower()
    user = users.get(uid)
    if not user:
        bot.send_message(msg.chat.id, "❌ ابتدا ثبت‌نام کنید.")
        return

    player = next((p for p in players if p['name'].lower() == player_name), None)
    if not player:
        bot.send_message(msg.chat.id, "❌ بازیکن موردنظر پیدا نشد.")
        return

    wallet = user.get("wallet", {"coins":0, "gems":0})
    # اول با جم چک می‌کنیم بعد با سکه
    if wallet.get("gems", 0) >= player["price_gems"]:
        wallet["gems"] -= player["price_gems"]
    elif wallet.get("coins", 0) >= player["price_coins"]:
        wallet["coins"] -= player["price_coins"]
    else:
        bot.send_message(msg.chat.id, "❌ سکه یا جم کافی ندارید.")
        return

    # اضافه کردن بازیکن به تیم
    team = user.get("team_players", [])
    if len(team) >= 8:
        bot.send_message(msg.chat.id, "❌ حداکثر ۸ بازیکن در تیم می‌توانید داشته باشید.")
        return

    if player["name"] in team:
        bot.send_message(msg.chat.id, "❌ این بازیکن قبلا خریداری شده است.")
        return

    team.append(player["name"])
    user["team_players"] = team
    user["wallet"] = wallet
    users[uid] = user
    save_users()

    bot.send_message(msg.chat.id, f"✅ بازیکن {player['name']} با موفقیت خریداری شد.", reply_markup=back_to_menu_keyboard())
def show_wallet(msg):
    uid = str(msg.from_user.id)
    wallet = users[uid].get("wallet", {"coins": 0, "gems": 0})
    text = f"💰 کیف پول شما:\nسکه: {wallet.get('coins',0)}\nجم: {wallet.get('gems',0)}\n\nبرای خرید جم، فیش واریز رو ارسال کن."
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بازگشت به منو")
    bot.send_message(msg.chat.id, text, reply_markup=markup)

@bot.message_handler(content_types=['photo', 'text'])
def handle_payment_proof(msg):
    uid = str(msg.from_user.id)
    # فرض کنیم پیام فیش واریز است
    if users.get(uid, {}).get("registered") and msg.content_type in ['photo', 'text']:
        bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{uid}"))
        markup.add(types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{uid}"))
        bot.send_message(ADMIN_ID, f"📥 فیش واریز از {users[uid]['team_name']} دریافت شد.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def handle_payment_approval(call):
    if str(call.from_user.id) != str(ADMIN_ID):
        bot.answer_callback_query(call.id, "⛔ شما دسترسی ندارید.")
        return

    data = call.data
    uid = data.split("_")[1]

    if data.startswith("approve_"):
        if uid in users:
            wallet = users[uid].get("wallet", {"coins":0, "gems":0})
            wallet["coins"] = wallet.get("coins",0) + 100  # ۱۰۰ سکه اضافه می‌کنیم
            users[uid]["wallet"] = wallet
            save_users()
            bot.edit_message_text(f"✅ پرداخت تایید شد و ۱۰۰ سکه به کیف پول اضافه شد.", call.message.chat.id, call.message.message_id)
            bot.send_message(uid, "💰 پرداخت شما تایید شد و ۱۰۰ سکه به کیف پول اضافه شد.")
    elif data.startswith("reject_"):
        bot.edit_message_text(f"❌ پرداخت رد شد.", call.message.chat.id, call.message.message_id)
        bot.send_message(uid, "❌ پرداخت شما رد شد.")

night_game_participants = set()

def join_night_game(msg):
    uid = str(msg.from_user.id)
    if uid in night_game_participants:
        bot.send_message(msg.chat.id, "✅ شما قبلا در بازی شبانه ثبت‌نام کرده‌اید.")
    else:
        night_game_participants.add(uid)
        bot.send_message(msg.chat.id, "🎮 شما در لیست بازی شبانه ثبت شدید. ساعت ۹ شب بازی شروع می‌شود!")

def show_leaderboard(msg):
    # نمونه رتبه بندی
    leaderboard = sorted(
        [(uid, u.get("win_rate", 0), u.get("score", 0)) for uid, u in users.items()],
        key=lambda x: (x[1], x[2]),
        reverse=True
    )[:10]

    text = "🏆 برترین‌ها:\n"
    for i, (uid, win_rate, score) in enumerate(leaderboard, start=1):
        name = users[uid].get("team_name", "ناشناس")
        text += f"{i}. {name} - درصد برد: {win_rate}% - امتیاز: {score}\n"

    bot.send_message(msg.chat.id, text, reply_markup=main_menu())

import random
import datetime
import threading

# مجموعه شرکت‌کنندگان بازی شبانه
night_game_participants = set()

# ذخیره نتیجه بازی برای هر کاربر
night_game_results = {}

def run_night_games():
    print("⌛ اجرای بازی شبانه راس ساعت ۲۱...")
    participants = list(night_game_participants)
    random.shuffle(participants)

    while len(participants) >= 2:
        uid1 = participants.pop()
        uid2 = participants.pop()

        user1 = users.get(uid1, {})
        user2 = users.get(uid2, {})

        # محاسبه قدرت تقریبی تیم بر اساس تعداد بازیکن و امتیاز تاکتیک
        power1 = len(user1.get("team_players", [])) * 10 + user1.get("score", 50)
        power2 = len(user2.get("team_players", [])) * 10 + user2.get("score", 50)

        # شبیه‌سازی بازی با کمی تصادف
        diff = power1 - power2 + random.randint(-10, 10)

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
                u["score"] -= 10
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

    # خالی کردن لیست شرکت‌کنندگان پس از بازی
    night_game_participants.clear()

# تابع زمان‌بندی اجرای بازی شبانه ساعت 21:00
def schedule_night_game():
    now = datetime.datetime.now()
    target = now.replace(hour=21, minute=0, second=0, microsecond=0)
    if now > target:
        target += datetime.timedelta(days=1)
    delay = (target - now).total_seconds()
    threading.Timer(delay, night_game_wrapper).start()

def night_game_wrapper():
    run_night_games()
    schedule_night_game()  # برنامه‌ریزی برای روز بعد

# شروع زمان‌بندی هنگام اجرای برنامه
schedule_night_game()

# هندلر برای ورود به بازی شبانه
@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def join_night_game(msg):
    uid = str(msg.from_user.id)
    if uid in night_game_participants:
        bot.send_message(msg.chat.id, "✅ شما قبلا در بازی شبانه ثبت‌نام کرده‌اید.")
    else:
        night_game_participants.add(uid)
        bot.send_message(msg.chat.id, "🎮 شما در لیست بازی شبانه ثبت شدید. ساعت ۹ شب بازی شروع می‌شود!")

# نمایش گزارش بازی برای کاربر
@bot.message_handler(func=lambda m: m.text == "📄 گزارش بازی")
def show_game_report(msg):
    uid = str(msg.from_user.id)
    res = night_game_results.get(uid)
    if not res:
        bot.send_message(msg.chat.id, "❌ هنوز بازی‌ای انجام ندادی یا گزارش در دسترس نیست.")
        return

    opp_name = users.get(res["opponent"], {}).get("team_name", "حریف")
    text = f"🎮 گزارش بازی:\nبا تیم: {opp_name}\nنتیجه: {res['result']}\nامتیاز کسب شده: {res['score']}"
    bot.send_message(msg.chat.id, text, reply_markup=main_menu())

# پاداش روزانه: روزی 2 جم یک‌بار
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
    bot.send_message(msg.chat.id, "🎉 پاداش روزانه: ۲ جم به کیف پول شما اضافه شد!", reply_markup=main_menu())

# Flask webhook endpoint برای رندر
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    # اگر میخوای polling، این خط رو اینجا بذار (اما برای رندر بهتره webhook باشه)
    # bot.polling(none_stop=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
