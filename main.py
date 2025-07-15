import telebot, json, random, datetime, threading
from telebot import types

# ==== تنظیمات اصلی ====
BOT_TOKEN = '7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc'
ADMIN_ID = 5542927340
CHANNEL_USERNAME = '@Specialcoach1'
TRON_ADDRESS = 'TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb'

bot = telebot.TeleBot(BOT_TOKEN)

# ==== لود داده‌ها ====
def load_json(path):
    try:
        return json.load(open(path, encoding='utf-8'))
    except:
        return {}
def save_json(path, data):
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

users = load_json('data/users.json')
players = load_json('data/players.json')
matches = load_json('data/matches.json')

states = {}

# ==== چک عضویت در کانال ====
def is_user_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member','administrator','creator']
    except:
        return False

# ==== منوی اصلی ====
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('📋 لیست بازیکنان','🛒 فروشگاه','⚽ ترکیب و تاکتیک')
    kb.row('⏱️ شروع بازی','🏆 برترین‌ها','💼 کیف پول')
    return kb

# ==== استارت ====
@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = str(m.from_user.id)
    if not is_user_subscribed(m.from_user.id):
        bot.send_message(m.chat.id, f"⚠️ لطفاً ابتدا عضو کانال شوید:\n{CHANNEL_USERNAME}")
        return
    if uid not in users:
        states[uid] = 'ask_team'
        bot.send_message(m.chat.id, "👥 نام تیم خود را وارد کنید:")
    else:
        bot.send_message(m.chat.id, "🌟 خوش آمدید!", reply_markup=main_menu())

# ==== گرفتن نام تیم ====
@bot.message_handler(func=lambda m: states.get(str(m.from_user.id)) == 'ask_team')
def handle_team_name(m):
    uid = str(m.from_user.id)
    users[uid] = {
        "team_name": m.text,
        "contact": None,
        "players": [],
        "coins": 0,
        "gems": 0,
        "points": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "formation": None,
        "tactics": {}
    }
    save_json('data/users.json', users)
    states[uid] = 'ask_contact'
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📞 ارسال شماره من", request_contact=True))
    bot.send_message(m.chat.id, "📞 لطفاً شماره تماس خود را ارسال کنید:", reply_markup=kb)

# ==== گرفتن شماره تماس ====
@bot.message_handler(content_types=['contact'])
def handle_contact(m):
    uid = str(m.from_user.id)
    if states.get(uid) != 'ask_contact': return
    users[uid]['contact'] = m.contact.phone_number
    save_json('data/users.json', users)
    states.pop(uid)
    bot.send_message(m.chat.id, "✅ ثبت‌نام کامل شد!", reply_markup=main_menu())

# ==== منوی اصلی ====
@bot.message_handler(func=lambda m: m.text in ['📋 لیست بازیکنان','🛒 فروشگاه','⚽ ترکیب و تاکتیک','⏱️ شروع بازی','🏆 برترین‌ها','💼 کیف پول'])
def handle_main_menu(m):
    uid = str(m.from_user.id)
    u = users.get(uid)
    if not u:
        bot.send_message(m.chat.id, "❗ ابتدا /start را بزنید.")
        return

    if m.text == '📋 لیست بازیکنان':
        msg = ""
        for p in players:
            msg += f"{p['id']} • {p['name']} | 🎯 {p['skill']} | 💰 {p['price_coins']} سکه / 💎 {p['price_gems']} جم\n"
        bot.send_message(m.chat.id, msg)
    
    elif m.text == '🛒 فروشگاه':
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add('🥇 خرید جم','👥 خرید بازیکن')
        kb.add('🔙 بازگشت')
        bot.send_message(m.chat.id, "🛍️ فروشگاه:", reply_markup=kb)
    
    elif m.text == '⚽ ترکیب و تاکتیک':
        bot.send_message(m.chat.id, "⚙️ بخش ترکیب و تاکتیک در حال ساخت است.")
    
    elif m.text == '⏱️ شروع بازی':
        bot.send_message(m.chat.id, "🎮 بازی ساعت ۹ شب شروع خواهد شد. لطفاً منتظر بمانید.")
    
    elif m.text == '🏆 برترین‌ها':
        top = sorted(users.items(), key=lambda x: x[1]["points"], reverse=True)[:10]
        msg = "🏆 برترین مربی‌ها:\n"
        for i, (uid, info) in enumerate(top, 1):
            total = info['wins'] + info['draws'] + info['losses']
            rate = f"{(info['wins']/total*100):.1f}%" if total else "0%"
            msg += f"{i} • {info['team_name']} - {rate} برد - {info['points']} امتیاز\n"
        bot.send_message(m.chat.id, msg)

    elif m.text == '💼 کیف پول':
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add('📤 واریز','📥 خرید جم با سکه')
        kb.add('🔙 بازگشت')
        bot.send_message(m.chat.id, f"💰 سکه: {u['coins']} | 💎 جم: {u['gems']}\nآدرس ترون برای پرداخت:\n{TRON_ADDRESS}", reply_markup=kb)

# ==== اجرای ربات ====
bot.infinity_polling()
