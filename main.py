import telebot
from telebot import types
from flask import Flask, request
import os, time, json, threading, random, datetime

TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
WEBHOOK_URL = "https://special-coach.onrender.com/" + TOKEN
ADMIN_ID = 5542927340
CHANNEL = "@Specialcoach1"
TRON_ADDRESS = "TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
DATA_FOLDER = "data"
USERS_FILE = os.path.join(DATA_FOLDER, "users.json")

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# لیست کامل بازیکنان
ALL_PLAYERS = {
    "player1": {"name": "بازیکن ضعیف 1", "overall": 40, "position": "DF", "price_coins": 20, "price_gems": 1},
    "player2": {"name": "بازیکن ضعیف 2", "overall": 42, "position": "DF", "price_coins": 25, "price_gems": 1},
    # ... (بقیه بازیکنان)
    "player50": {"name": "Ter Stegen", "overall": 88, "position": "GK", "price_coins": 400, "price_gems": 8}
}

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# مدیریت منوها
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 ترکیب و تاکتیک", "🏪 فروشگاه بازیکن")
    markup.row("🎮 بازی شبانه", "📄 گزارش بازی")
    markup.row("👛 کیف پول", "🎁 پاداش روزانه")
    markup.row("🏆 برترین‌ها")
    return markup

def back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بازگشت به منو")
    return markup

# سیستم ثبت نام
user_states = {}
participants = set()

@bot.message_handler(commands=["start"])
def start_command(message):
    uid = str(message.from_user.id)
    users = load_users()

    if uid in users:
        bot.send_message(message.chat.id, "👋 خوش آمدید مجدد!", reply_markup=main_menu())
        return

    if not is_member(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL.strip('@')}"))
        markup.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_join"))
        bot.send_message(message.chat.id, "برای استفاده از ربات باید در کانال عضو شوید:", reply_markup=markup)
        return

    user_states[uid] = "awaiting_team"
    bot.send_message(message.chat.id, "🏟️ لطفاً نام تیم خود را وارد کنید:")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if is_member(call.from_user.id):
        uid = str(call.from_user.id)
        user_states[uid] = "awaiting_team"
        bot.send_message(call.message.chat.id, "✅ عضویت شما تایید شد!\n\n🏟️ لطفاً نام تیم خود را وارد کنید:")
    else:
        bot.answer_callback_query(call.id, "❌ هنوز در کانال عضو نشده‌اید!")

@bot.message_handler(func=lambda message: user_states.get(str(message.from_user.id)) == "awaiting_team")
def get_team_name(message):
    uid = str(message.from_user.id)
    team_name = message.text.strip()

    if len(team_name) < 3:
        bot.send_message(message.chat.id, "❗ نام تیم باید حداقل ۳ کاراکتر باشد.")
        return

    user_states[uid] = {"step": "awaiting_phone", "team": team_name}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 ارسال شماره تماس", request_contact=True))
    bot.send_message(message.chat.id, "📱 لطفاً شماره تماس خود را ارسال کنید:", reply_markup=markup)

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
        "players": [f"player{i}" for i in range(1, 6)],
        "tactic": {
            "formation": "",
            "mode": "",
            "style": "",
            "offside": "",
            "press": ""
        },
        "score": 0,
        "coins": 100,
        "gems": 2,
        "match_history": [],
        "last_reward": ""
    }

    save_users(users)
    del user_states[uid]

    bot.send_message(message.chat.id, "🎉 ثبت‌نام شما با موفقیت انجام شد! به منوی اصلی خوش آمدید.", reply_markup=main_menu())

# سیستم فروشگاه بازیکن
@bot.message_handler(func=lambda m: m.text == "🏪 فروشگاه بازیکن")
def show_store(m):
    uid = str(m.from_user.id)
    users = load_users()
    
    if uid not in users:
        return bot.send_message(m.chat.id, "❌ ابتدا باید ثبت نام کنید!", reply_markup=back_menu())

    text = "🏪 لیست بازیکنان قابل خرید:\n\n"
    markup = types.InlineKeyboardMarkup()
    
    for pid, player in ALL_PLAYERS.items():
        if pid in users[uid]["players"]:
            continue
            
        btn_text = f"{player['name']} ({player['position']}) - ⚡{player['overall']} | "
        btn_text += f"💰{player['price_coins']} سکه | 💎{player['price_gems']} جم"
        
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{pid}"))

    if not markup.keyboard:
        return bot.send_message(m.chat.id, "✅ شما تمام بازیکنان را خریداری کرده‌اید!", reply_markup=back_menu())

    bot.send_message(m.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def handle_buy(c):
    uid = str(c.from_user.id)
    users = load_users()
    pid = c.data[4:]  # حذف پیشوند buy_
    
    if pid not in ALL_PLAYERS:
        return bot.answer_callback_query(c.id, "❌ بازیکن یافت نشد!")

    if pid in users[uid]["players"]:
        return bot.answer_callback_query(c.id, "⚠️ شما قبلاً این بازیکن را خریداری کرده‌اید")

    if len(users[uid]["players"]) >= 8:
        return bot.answer_callback_query(c.id, "❌ حداکثر ۸ بازیکن می‌توانید داشته باشید")

    player = ALL_PLAYERS[pid]
    
    # بررسی موجودی
    if users[uid]["coins"] >= player["price_coins"]:
        users[uid]["coins"] -= player["price_coins"]
    elif users[uid]["gems"] >= player["price_gems"]:
        users[uid]["gems"] -= player["price_gems"]
    else:
        return bot.answer_callback_query(c.id, "❌ موجودی کافی ندارید")

    users[uid]["players"].append(pid)
    save_users(users)
    
    bot.answer_callback_query(c.id, f"✅ {player['name']} با موفقیت خریداری شد!")
    bot.send_message(c.message.chat.id, 
                    f"🎉 بازیکن {player['name']} به تیم شما اضافه شد!\n"
                    f"📍 پست: {player['position']}\n"
                    f"⚡ قدرت: {player['overall']}",
                    reply_markup=back_menu())

# سیستم ترکیب و تاکتیک
@bot.message_handler(func=lambda m: m.text == "📋 ترکیب و تاکتیک")
def tactic_menu(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📌 انتخاب ترکیب", "⚔️ سبک بازی")
    markup.row("🧠 تاکتیک", "🪤 تله آفساید", "🔥 پرسینگ")
    markup.row("📊 شماتیک تیم")
    markup.row("بازگشت به منو")
    bot.send_message(m.chat.id, "⚙️ گزینه مورد نظر را انتخاب کنید:", reply_markup=markup)

# ... (سایر توابع مربوط به تاکتیک)

# سیستم بازی شبانه
@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def join_night_game(m):
    uid = str(m.from_user.id)
    participants.add(uid)
    bot.send_message(m.chat.id, "✅ شما برای بازی امشب ثبت‌نام شدید. نتیجه پس از انجام بازی ارسال خواهد شد.", reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "📄 گزارش بازی")
def match_report(m):
    uid = str(m.from_user.id)
    users = load_users()
    
    if uid not in users:
        return bot.send_message(m.chat.id, "❌ ابتدا باید ثبت نام کنید!", reply_markup=back_menu())
    
    history = users[uid].get("match_history", [])
    if not history:
        return bot.send_message(m.chat.id, "📭 شما هنوز هیچ بازی انجام نداده‌اید.", reply_markup=back_menu())
    
    report = "📋 تاریخچه آخرین بازی‌های شما:\n\n" + "\n\n".join(history[-5:])
    bot.send_message(m.chat.id, report, reply_markup=back_menu())

def simulate_match(user1, user2, users):
    # محاسبات بازی
    pass

def run_nightly_game():
    while True:
        now = datetime.datetime.now()
        if now.hour == 22 and now.minute == 0:
            users = load_users()
            players = list(participants)
            random.shuffle(players)
            
            for i in range(0, len(players)-1, 2):
                simulate_match(players[i], players[i+1], users)
                
                try:
                    bot.send_message(players[i], "🎮 بازی شما انجام شد! برای مشاهده نتیجه به بخش گزارش بازی مراجعه کنید.")
                    bot.send_message(players[i+1], "🎮 بازی شما انجام شد! برای مشاهده نتیجه به بخش گزارش بازی مراجعه کنید.")
                except:
                    continue
            
            participants.clear()
            save_users(users)
        
        time.sleep(60)

# سیستم کیف پول
@bot.message_handler(func=lambda m: m.text == "👛 کیف پول")
def wallet(m):
    uid = str(m.from_user.id)
    users = load_users()
    
    if uid not in users:
        return bot.send_message(m.chat.id, "❌ ابتدا باید ثبت نام کنید!", reply_markup=back_menu())
    
    user = users[uid]
    text = (
        "💰 کیف پول شما:\n\n"
        f"🪙 سکه‌ها: {user['coins']}\n"
        f"💎 جم‌ها: {user['gems']}\n\n"
        f"💳 آدرس TRX: {TRON_ADDRESS}\n\n"
        "برای واریز، مبلغ را به آدرس بالا ارسال کرده و فیش پرداخت را ارسال کنید."
    )
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🔄 تبدیل سکه به جم", "📤 ارسال فیش پرداخت")
    markup.row("بازگشت به منو")
    
    bot.send_message(m.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔄 تبدیل سکه به جم")
def convert_coins(m):
    uid = str(m.from_user.id)
    users = load_users()
    
    if uid not in users:
        return bot.send_message(m.chat.id, "❌ ابتدا باید ثبت نام کنید!", reply_markup=back_menu())
    
    if users[uid]["coins"] >= 100:
        users[uid]["coins"] -= 100
        users[uid]["gems"] += 1
        save_users(users)
        bot.send_message(m.chat.id, "✅ تبدیل با موفقیت انجام شد!\n100 سکه ➡️ 1 جم", reply_markup=back_menu())
    else:
        bot.send_message(m.chat.id, "❌ موجودی سکه شما کافی نیست!", reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "📤 ارسال فیش پرداخت")
def ask_receipt(m):
    bot.send_message(m.chat.id, "📎 لطفاً فیش پرداخت خود را ارسال کنید (عکس یا متن):", reply_markup=back_menu())

@bot.message_handler(content_types=["text", "photo"])
def handle_receipt(m):
    if m.text and m.text.strip() in ["📄 گزارش بازی", "🎁 پاداش روزانه", "🏆 برترین‌ها", "بازگشت به منو"]:
        return
    
    if m.content_type == "text":
        bot.send_message(
            ADMIN_ID,
            f"📩 فیش متنی جدید\n\n"
            f"👤 کاربر: {m.from_user.first_name}\n"
            f"🆔 آیدی: {m.from_user.id}\n"
            f"📝 متن فیش:\n{m.text}"
        )
    elif m.content_type == "photo":
        bot.send_photo(
            ADMIN_ID,
            m.photo[-1].file_id,
            caption=f"📸 فیش تصویری\n\n👤 کاربر: {m.from_user.first_name}\n🆔 آیدی: {m.from_user.id}"
        )
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"approve_{m.from_user.id}"),
        types.InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_{m.from_user.id}")
    )
    
    bot.send_message(ADMIN_ID, "لطفاً پرداخت را بررسی کنید:", reply_markup=markup)
    bot.send_message(m.chat.id, "✅ فیش شما دریافت شد و در حال بررسی است.", reply_markup=back_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith(("approve_", "reject_")))
def handle_payment_verification(c):
    action, uid = c.data.split("_")
    users = load_users()
    
    if action == "approve":
        users[uid]["coins"] = users.get(uid, {}).get("coins", 0) + 100
        save_users(users)
        bot.send_message(uid, "🎉 پرداخت شما تایید شد!\n100 سکه به حساب شما اضافه شد.", reply_markup=main_menu())
        bot.answer_callback_query(c.id, "پرداخت تایید شد")
    else:
        bot.send_message(uid, "❌ پرداخت شما تایید نشد. لطفاً با پشتیبانی تماس بگیرید.", reply_markup=main_menu())
        bot.answer_callback_query(c.id, "پرداخت رد شد")
    
    try:
        bot.delete_message(c.message.chat.id, c.message.message_id)
    except:
        pass

# سیستم پاداش روزانه
@bot.message_handler(func=lambda m: m.text == "🎁 پاداش روزانه")
def daily_reward(m):
    try:
        uid = str(m.from_user.id)
        users = load_users()
        
        if uid not in users:
            return bot.send_message(m.chat.id, "❌ ابتدا باید ثبت نام کنید!", reply_markup=back_menu())
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        last_reward = users[uid].get("last_reward", "")
        
        if last_reward == today:
            return bot.send_message(m.chat.id, "⏳ شما امروز پاداش خود را دریافت کرده‌اید!", reply_markup=back_menu())
        
        users[uid]["gems"] += 2
        users[uid]["last_reward"] = today
        save_users(users)
        
        bot.send_message(
            m.chat.id,
            f"🎉 پاداش روزانه شما:\n\n"
            f"➕ 2 جم دریافت کردید\n"
            f"💎 موجودی جم: {users[uid]['gems']}",
            reply_markup=back_menu()
        )
    except Exception as e:
        print(f"خطا در پاداش روزانه: {e}")
        bot.send_message(m.chat.id, "⚠️ خطایی رخ داد. لطفاً بعداً تلاش کنید.", reply_markup=back_menu())

# سیستم برترین‌ها
@bot.message_handler(func=lambda m: m.text == "🏆 برترین‌ها")
def top_players(m):
    try:
        users = load_users()
        rankings = []
        
        for uid, data in users.items():
            if not data.get("team") or not data.get("match_history"):
                continue
                
            total_games = len(data["match_history"])
            wins = sum(1 for r in data["match_history"] if data["team"] in r and "برنده شد" in r)
            win_rate = (wins / total_games) * 100 if total_games > 0 else 0
            
            rankings.append({
                "team": data["team"],
                "score": data.get("score", 0),
                "win_rate": win_rate,
                "wins": wins,
                "games": total_games
            })
        
        rankings.sort(key=lambda x: (-x["score"], -x["win_rate"]))
        
        text = "🏆 جدول برترین تیم‌ها:\n\n"
        for i, team in enumerate(rankings[:10], 1):
            text += (
                f"{i}. {team['team']}\n"
                f"⭐ امتیاز: {team['score']} | "
                f"📊 درصد برد: {team['win_rate']:.1f}%\n"
                f"✅ {team['wins']} برد از {team['games']} بازی\n\n"
            )
        
        if not rankings:
            text = "هنوز هیچ بازی انجام نشده است."
        
        bot.send_message(m.chat.id, text, reply_markup=back_menu())
    except Exception as e:
        print(f"خطا در سیستم برترین‌ها: {e}")
        bot.send_message(m.chat.id, "⚠️ خطا در دریافت اطلاعات برترین‌ها", reply_markup=back_menu())

# وب هوک و اجرا
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "ربات فوتبال آنلاین فعال است"

def start_bot():
    threading.Thread(target=run_nightly_game).start()
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    print("ربات در حال اجرا...")
    start_bot()
