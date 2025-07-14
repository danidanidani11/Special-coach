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

@bot.message_handler(func=lambda m: m.text == "📋 ترکیب و تاکتیک")
def formation_and_tactic(m):
    user = get_user(m.chat.id)
    if not user:
        return bot.send_message(m.chat.id, "❗ ابتدا /start را بزن.")

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    formations = ["4-4-2", "4-3-3", "3-5-2", "5-3-2"]
    tactics = ["تعادلی", "هجومی", "دفاعی", "ضدحمله"]

    for f in formations:
        callback_data = f"set_formation:{f}"
        btn = telebot.types.InlineKeyboardButton(f"⚽ {f}", callback_data=callback_data)
        markup.add(btn)

    for t in tactics:
        callback_data = f"set_tactic:{t}"
        btn = telebot.types.InlineKeyboardButton(f"🎯 {t}", callback_data=callback_data)
        markup.add(btn)

    bot.send_message(m.chat.id, "📐 ترکیب و تاکتیکت رو انتخاب کن:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def callback_set_formation_tactic(call):
    user = get_user(call.message.chat.id)
    if not user:
        return bot.answer_callback_query(call.id, "❗ ابتدا /start بزن.")

    data = call.data
    if data.startswith("set_formation:"):
        formation = data.split(":")[1]
        user['formation'] = formation
        save_user(call.message.chat.id, user)
        bot.edit_message_text(f"✅ ترکیب به {formation} تغییر کرد.", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "ترکیب تغییر کرد.")
    elif data.startswith("set_tactic:"):
        tactic = data.split(":")[1]
        user['tactic'] = tactic
        save_user(call.message.chat.id, user)
        bot.edit_message_text(f"✅ تاکتیک به {tactic} تغییر کرد.", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "تاکتیک تغییر کرد.")

@bot.message_handler(func=lambda m: m.text == "🛒 بازار نقل و انتقالات")
def transfer_market(m):
    user = get_user(m.chat.id)
    if not user:
        return bot.send_message(m.chat.id, "❗ ابتدا /start را بزن.")

    all_players = load_json("players.json")
    owned_names = [p['name'] for p in user.get("players", [])]

    available = [p for p in all_players if p['name'] not in owned_names]

    if not available:
        return bot.send_message(m.chat.id, "⚠️ هیچ بازیکنی برای خرید در دسترس نیست.")

    text = "🏷 بازیکنان آزاد برای خرید:\n\n"
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)

    for p in available[:10]:  # فقط ۱۰ تا اول
        price = p['price']
        gem_price = int(price * 0.2)  # ۲۰٪ قیمت به جم تبدیل
        btn = telebot.types.InlineKeyboardButton(
            f"خرید {p['name']} - قیمت: {price} سکه / {gem_price} جم",
            callback_data=f"buy_player:{p['name']}"
        )
        markup.add(btn)

    bot.send_message(m.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_player:"))
def buy_player(call):
    user = get_user(call.message.chat.id)
    if not user:
        return bot.answer_callback_query(call.id, "❗ ابتدا /start بزن.")

    player_name = call.data.split(":")[1]
    all_players = load_json("players.json")
    player = next((p for p in all_players if p['name'] == player_name), None)
    if not player:
        return bot.answer_callback_query(call.id, "⚠️ بازیکن یافت نشد.")

    # بررسی مالکیت قبلی
    if any(p['name'] == player_name for p in user.get("players", [])):
        return bot.answer_callback_query(call.id, "❗ شما قبلاً این بازیکن را خریداری کرده‌اید.")

    price = player['price']
    gem_price = int(price * 0.2)

    # اگر قیمت جم بیشتر از 0 بود (مثلاً بازیکنان خاص)
    # اجازه بده با جم بخرند در غیر اینصورت فقط با سکه
    # اینجا مثلا بازیکنای گرون تر از 40 فقط با جم
    if price > 40:
        if user['gems'] < gem_price:
            return bot.answer_callback_query(call.id, f"❌ جم کافی نیست! نیاز به {gem_price} جم داری.")
        user['gems'] -= gem_price
    else:
        if user['coins'] < price:
            return bot.answer_callback_query(call.id, f"❌ سکه کافی نیست! نیاز به {price} سکه داری.")
        user['coins'] -= price

    # اضافه کردن بازیکن به تیم
    user['players'].append(player)
    save_user(call.message.chat.id, user)
    bot.answer_callback_query(call.id, f"🎉 بازیکن {player_name} خریداری شد!")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

@bot.message_handler(func=lambda m: m.text == "🪙 فروشگاه")
def shop(m):
    user = get_user(m.chat.id)
    if not user:
        return bot.send_message(m.chat.id, "❗ ابتدا /start را بزن.")

    text = f"""🪙 فروشگاه جم

سکه فعلی شما: {user['coins']}
جم فعلی شما: {user['gems']}

قیمت‌ها:
۱ جم = ۲۰ سکه
۵ جم = ۹۰ سکه (تخفیف)
۱۰ جم = ۱۷۰ سکه (تخفیف بیشتر)

برای خرید مقدار مورد نظر عدد جم را وارد کنید:
مثلاً برای خرید ۵ جم، عدد ۵ را ارسال کنید.
"""
    bot.send_message(m.chat.id, text)
    user['step'] = "buy_gems"
    users = load_json("users.json")
    users[str(m.chat.id)] = user
    save_json("users.json", users)

@bot.message_handler(func=lambda m: True)
def handle_buy_gems(m):
    users = load_json("users.json")
    user = users.get(str(m.chat.id))
    if not user or user.get("step") != "buy_gems":
        return  # این پیام برای سایر حالات است

    try:
        amount = int(m.text.strip())
        prices = {1:20, 5:90, 10:170}
        if amount not in prices:
            return bot.send_message(m.chat.id, "❌ مقدار معتبر نیست. فقط 1، 5 یا 10 را وارد کن.")
        price = prices[amount]
    except:
        return bot.send_message(m.chat.id, "❌ لطفاً فقط عدد بفرست.")

    if user['coins'] < price:
        return bot.send_message(m.chat.id, f"❌ سکه کافی نیست! برای {amount} جم به {price} سکه نیاز داری.")

    # کم کردن سکه و اضافه کردن جم
    user['coins'] -= price
    user['gems'] += amount
    user['step'] = None
    users[str(m.chat.id)] = user
    save_json("users.json", users)

    bot.send_message(m.chat.id, f"✅ {amount} جم با موفقیت خریدی. سکه‌های باقی‌مانده: {user['coins']}")

@bot.message_handler(func=lambda m: m.text == "📊 جدول لیگ")
def league_table(m):
    users = load_json("users.json")
    if not users:
        return bot.send_message(m.chat.id, "⚠️ هنوز بازیکنی ثبت نشده.")

    # مرتب‌سازی بر اساس points به صورت نزولی
    sorted_users = sorted(users.values(), key=lambda x: x.get("points", 0), reverse=True)

    txt = "🏆 جدول لیگ - ۱۰ تیم برتر:\n\n"
    for i, u in enumerate(sorted_users[:10], start=1):
        txt += f"{i}. {u.get('team_name', 'ناشناخته')} - امتیاز: {u.get('points',0)}\n"

    bot.send_message(m.chat.id, txt)

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"https://special-coach.onrender.com/{TOKEN}")  # 🔁 آدرس واقعی Render جایگزین کن
    threading.Thread(target=scheduler_loop).start()
    app.run(host="0.0.0.0", port=10000)
