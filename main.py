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

# ۵۰ بازیکن واقعی
ALL_PLAYERS = {
    "player1": {"name": "بازیکن ضعیف 1", "overall": 40, "position": "DF", "price_coins": 20, "price_gems": 1},
    # ... (بقیه بازیکنان)
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

# منوها
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

# مدیریت کاربران
user_states = {}
participants = set()

@bot.message_handler(commands=["start"])
def start_command(message):
    # ... (کد قبلی بدون تغییر)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    # ... (کد قبلی بدون تغییر)

# ثبت نام کاربر
@bot.message_handler(func=lambda message: user_states.get(str(message.from_user.id)) == "awaiting_team")
def get_team_name(message):
    # ... (کد قبلی بدون تغییر)

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    # ... (کد قبلی با اضافه شدن last_reward)

# بخش فروشگاه بازیکن
@bot.message_handler(func=lambda m: m.text == "🏪 فروشگاه بازیکن")
def show_store(m):
    # ... (کد قبلی بدون تغییر)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def handle_buy(c):
    # ... (کد قبلی بدون تغییر)

# بخش ترکیب و تاکتیک
@bot.message_handler(func=lambda m: m.text == "📋 ترکیب و تاکتیک")
def tactic_menu(m):
    # ... (کد قبلی بدون تغییر)

# ... (سایر توابع مربوط به تاکتیک بدون تغییر)

# بازی شبانه
@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def join_night_game(m):
    # ... (کد قبلی بدون تغییر)

@bot.message_handler(func=lambda m: m.text == "📄 گزارش بازی")
def match_report(m):
    # ... (کد قبلی بدون تغییر)

def simulate_match(user1, user2, users):
    # ... (کد قبلی بدون تغییر)

def run_nightly_game():
    # ... (کد قبلی بدون تغییر)

# کیف پول و پرداخت
@bot.message_handler(func=lambda m: m.text == "👛 کیف پول")
def wallet(m):
    # ... (کد قبلی بدون تغییر)

@bot.message_handler(func=lambda m: m.text == "🔄 تبدیل سکه به جم")
def convert_coins(m):
    # ... (کد قبلی بدون تغییر)

@bot.message_handler(func=lambda m: m.text == "📤 ارسال فیش")
def ask_receipt(m):
    bot.send_message(m.chat.id, "🧾 لطفاً فیش پرداخت خود را ارسال کنید (متن یا عکس):", reply_markup=back_menu())

@bot.message_handler(content_types=["text", "photo"])
def handle_receipt(m):
    if m.text and m.text.strip() in ["📄 گزارش بازی", "🎁 پاداش روزانه", "🏆 برترین‌ها", "بازگشت به منو"]:
        return
    
    if m.content_type == "text":
        bot.send_message(ADMIN_ID, f"📝 فیش متنی از کاربر:\nآیدی: {m.from_user.id}\nنام: {m.from_user.first_name}\nمتن:\n{m.text}")
    elif m.content_type == "photo":
        bot.send_photo(ADMIN_ID, m.photo[-1].file_id, 
                      caption=f"📸 فیش تصویری از کاربر\nآیدی: {m.from_user.id}\nنام: {m.from_user.first_name}")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"confirm_{m.from_user.id}"),
               types.InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_{m.from_user.id}"))
    
    bot.send_message(ADMIN_ID, "لطفاً پرداخت را بررسی کنید:", reply_markup=markup)
    bot.send_message(m.chat.id, "✅ فیش شما دریافت شد و در حال بررسی است. نتیجه را به شما اطلاع خواهیم داد.", reply_markup=back_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith(("confirm_", "reject_")))
def handle_receipt_admin(c):
    uid = int(c.data.split("_")[1])
    users = load_users()
    
    if c.data.startswith("confirm_"):
        users[str(uid)]["coins"] = users.get(str(uid), {}).get("coins", 0) + 100
        save_users(users)
        bot.send_message(uid, "🎉 پرداخت شما تایید شد! 100 سکه به حساب شما اضافه شد.", reply_markup=main_menu())
        bot.answer_callback_query(c.id, "پرداخت تایید شد")
    else:
        bot.send_message(uid, "❌ متاسفانه پرداخت شما تایید نشد. لطفاً با پشتیبانی تماس بگیرید.", reply_markup=main_menu())
        bot.answer_callback_query(c.id, "پرداخت رد شد")
    
    try:
        bot.delete_message(c.message.chat.id, c.message.message_id)
    except:
        pass

# پاداش روزانه
@bot.message_handler(func=lambda m: m.text == "🎁 پاداش روزانه")
def daily_reward(m):
    try:
        uid = str(m.from_user.id)
        users = load_users()
        
        if uid not in users:
            return bot.send_message(m.chat.id, "❌ ابتدا باید ثبت نام کنید!", reply_markup=back_menu())
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if users[uid].get("last_reward", "") == today:
            return bot.send_message(m.chat.id, "⏳ شما امروز پاداش خود را دریافت کرده‌اید!", reply_markup=back_menu())
        
        users[uid]["gems"] = users[uid].get("gems", 0) + 2
        users[uid]["last_reward"] = today
        save_users(users)
        
        bot.send_message(m.chat.id, f"🎉 پاداش روزانه دریافت کردید!\n➕ 2 جم به حساب شما اضافه شد\n💎 موجودی جم: {users[uid]['gems']}", 
                        reply_markup=back_menu())
    except Exception as e:
        print(f"خطا در پاداش روزانه: {e}")
        bot.send_message(m.chat.id, "⚠️ خطایی رخ داد. لطفاً بعداً تلاش کنید.", reply_markup=back_menu())

# برترین‌ها
@bot.message_handler(func=lambda m: m.text == "🏆 برترین‌ها")
def top_players(m):
    try:
        users = load_users()
        rankings = []
        
        for uid, data in users.items():
            if not data.get("team") or not data.get("match_history"):
                continue
                
            total = len(data["match_history"])
            wins = sum(1 for r in data["match_history"] if data["team"] in r and "برنده شد" in r)
            rate = (wins / total) * 100 if total > 0 else 0
            
            rankings.append({
                "team": data["team"],
                "score": data.get("score", 0),
                "rate": rate,
                "wins": wins,
                "matches": total
            })
        
        rankings.sort(key=lambda x: (-x["score"], -x["rate"]))
        
        text = "🏆 رتبه‌بندی برترین تیم‌ها:\n\n"
        for i, team in enumerate(rankings[:10], 1):
            text += (f"{i}. {team['team']}\n"
                    f"⭐ امتیاز: {team['score']} | "
                    f"📊 درصد برد: {team['rate']:.1f}%\n"
                    f"✅ {team['wins']} برد از {team['matches']} بازی\n\n")
        
        if not rankings:
            text = "هنوز هیچ بازی انجام نشده است."
            
        bot.send_message(m.chat.id, text, reply_markup=back_menu())
    except Exception as e:
        print(f"خطا در برترین‌ها: {e}")
        bot.send_message(m.chat.id, "⚠️ خطا در دریافت رتبه‌بندی", reply_markup=back_menu())

# وب هوک
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "ربات فوتبال فعال است"

def start_bot():
    threading.Thread(target=run_nightly_game).start()
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    print("ربات در حال اجرا...")
    start_bot()
