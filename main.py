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

# ۵۰ بازیکن واقعی (۲۵ ضعیف، ۲۵ قوی)
ALL_PLAYERS = {
    "player1": {"name": "بازیکن ضعیف 1", "overall": 40, "position": "DF", "price_coins": 20, "price_gems": 1},
    "player2": {"name": "بازیکن ضعیف 2", "overall": 42, "position": "DF", "price_coins": 25, "price_gems": 1},
    "player3": {"name": "بازیکن ضعیف 3", "overall": 43, "position": "MF", "price_coins": 25, "price_gems": 1},
    "player25": {"name": "بازیکن ضعیف 25", "overall": 50, "position": "GK", "price_coins": 30, "price_gems": 1},

    "player26": {"name": "Messi", "overall": 98, "position": "FW", "price_coins": 700, "price_gems": 12},
    "player27": {"name": "Ronaldo", "overall": 97, "position": "FW", "price_coins": 650, "price_gems": 11},
    "player28": {"name": "Modric", "overall": 91, "position": "MF", "price_coins": 450, "price_gems": 7},
    "player50": {"name": "Ter Stegen", "overall": 87, "position": "GK", "price_coins": 350, "price_gems": 5},
    "player29": {"name": "Kdb", "overall": 93, "position": "MF", "price_coins": 500, "price_gems": 8},
    "player30": {"name": "Neymar", "overall": 93, "position": "FW", "price_coins": 525, "price_gems": 9}
}
# سیستم رویدادهای بازی
MATCH_EVENTS = {
    "goal": [
        "⚽ گللل! {player} از تیم {team} گل زد!",
        "⚽⚽⚽ گل زیبایی توسط {player}! نتیجه موقت {score}",
        "گلللللل! {player} از موقعیت استفاده کرد! {score}"
    ],
    "miss": [
        "❌ {player} شوت کرد و توپ به بیرون رفت!",
        "چه فرصت از دست رفته‌ای توسط {player}!",
        "دروازه‌بان توپ رو مهار کرد! شوت {player} به دام افتاد."
    ],
    "foul": [
        "🚩 خطا روی {player}! کارت زرد برای بازیکن حریف",
        "آفساید! داور پرچم رو بالا برد",
        "ضربه آزاد برای تیم {team}"
    ],
    "corner": [
        "🔄 کرنر برای تیم {team}",
        "توپ به بیرون رفت! کرنر برای {team}"
    ],
    "save": [
        "🧤 چه مهار فوق‌العاده‌ای توسط دروازه‌بان {team}!",
        "دروازه‌بان {team} توپ رو نجات داد!"
    ]
}

# اسامی بازیکنان برای گزارش
PLAYER_NAMES = {
    "FW": ["مهاجم تیم", "ستاره هجومی", "شوتزن ماهر"],
    "MF": ["هافبک خلاق", "بازی‌ساز تیم", "بازیکن مرکزی"],
    "DF": ["مدافع قوی", "ستاره دفاعی", "مدافع قدر"],
    "GK": ["دروازه‌بان", "گلر", "دیوار آخر"]
}

def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 ترکیب و تاکتیک", "🏪 فروشگاه بازیکن")
    markup.row("🎮 بازی شبانه", "📄 گزارش بازی")
    markup.row("👛 کیف پول", "🏆 برترین‌ها")
    markup.row("🎁 پاداش روزانه")
    return markup

def back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بازگشت به منو")
    return markup

user_states = {}
participants = set()
daily_rewards = {}

def simulate_live_match(user1, user2, users):
    team1 = users[user1]
    team2 = users[user2]
    
    # ارسال پیام شروع بازی
    start_message = f"⏰ بازی بین {team1['team']} و {team2['team']} آغاز شد!"
    send_to_both(user1, user2, start_message)
    time.sleep(1)

    # محاسبه قدرت تیم‌ها
    power1 = calculate_power(team1)
    power2 = calculate_power(team2)
    
    # شبیه‌سازی بازی دقیقه به دقیقه
    score = [0, 0]  # [تیم1, تیم2]
    events = []
    
    for minute in range(1, 6):  # 5 دقیقه بازی
        minute_report = f"⏱️ دقیقه {minute}:"
        send_to_both(user1, user2, minute_report)
        time.sleep(1)
        
        # تولید رویدادهای بازی
        for _ in range(random.randint(2, 4)):
            event = generate_match_event(team1, team2, score, power1, power2)
            events.append(event)
            send_to_both(user1, user2, event)
            time.sleep(1)
            
            # به‌روزرسانی نتیجه در صورت گل
            if "گلللللل" in event or "گووووول" in event:
                if team1["team"] in event:
                    score[0] += 1
                else:
                    score[1] += 1

    # ثبت نهایی نتیجه
    result_details = create_result(team1, team2, score, events)
    
    # ذخیره تاریخچه برای هر دو تیم
    save_match_history(team1, team2, result_details)
    
    # ارسال نتیجه نهایی
    send_to_both(user1, user2, result_details["result_text"])
    time.sleep(1)
    
    # ارسال خلاصه بازی
    summary = (
        f"📊 خلاصه بازی:\n"
        f"🏟️ {team1['team']} {score[0]} - {score[1]} {team2['team']}\n"
        f"⭐ قدرت تیم‌ها: {power1} vs {power2}\n"
        f"⚽ گل‌ها: {', '.join(e for e in events if 'گل' in e)}"
    )
    send_to_both(user1, user2, summary)

def send_to_both(user1, user2, message):
    try:
        bot.send_message(user1, message)
        bot.send_message(user2, message)
    except:
        pass

def create_result(team1, team2, score, events):
    result = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "score": f"{score[0]}-{score[1]}",
        "events": events,
        "opponent": team2["team"],
        "power": f"{calculate_power(team1)}-{calculate_power(team2)}"
    }
    
    if score[0] > score[1]:
        result["result"] = "win"
        result["result_text"] = f"🏆 {team1['team']} {score[0]}-{score[1]} برنده شد!"
    elif score[0] < score[1]:
        result["result"] = "lose"
        result["result_text"] = f"🏆 {team2['team']} {score[1]}-{score[0]} برنده شد!"
    else:
        result["result"] = "draw"
        result["result_text"] = f"🤝 مساوی {score[0]}-{score[1]}"
    
    return result

def save_match_history(team1, team2, result):
    # برای تیم اول
    team1["match_history"].append(result)
    
    # برای تیم دوم (معکوس)
    opp_result = result.copy()
    opp_result.update({
        "opponent": team1["team"],
        "result": "win" if result["result"] == "lose" else "lose" if result["result"] == "win" else "draw"
    })
    team2["match_history"].append(opp_result)
    
    # محاسبه قدرت تیم‌ها با جزئیات دقیق‌تر
    def calculate_power(team):
        base = sum(ALL_PLAYERS[p]["overall"] for p in team["players"] if p in ALL_PLAYERS) / 11
        tactic_bonus = 0
        
        # تأثیر تاکتیک‌ها (با ضرایب قوی‌تر)
        if team["tactic"].get("mode") == "هجومی": tactic_bonus += 15
        elif team["tactic"].get("mode") == "دفاعی": tactic_bonus -= 10
        
        if team["tactic"].get("press") == "پرس ۱۰۰ درصد": tactic_bonus += 8
        
        return max(30, min(100, base + tactic_bonus + random.randint(-5, 5)))

    power1 = calculate_power(team1)
    power2 = calculate_power(team2)
    
    # محاسبه گل‌ها با فرمول واقع‌گرایانه
    diff = abs(power1 - power2)
    avg_goals = 2 + (diff / 20)  # میانگین گل بر اساس اختلاف قدرت
    
    goals1 = int(avg_goals * (power1 / (power1 + power2))) + random.randint(-1, 1)
    goals2 = int(avg_goals * (power2 / (power1 + power2))) + random.randint(-1, 1)
    
    # جلوگیری از نتایج منفی
    goals1 = max(0, min(5, goals1))
    goals2 = max(0, min(5, goals2))
    
    # ثبت دقیق نتیجه
    result_details = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "score": f"{goals1}-{goals2}",
        "opponent": team2["team"] if user1 == user1 else team1["team"],
        "goals_for": goals1 if user1 == user1 else goals2,
        "goals_against": goals2 if user1 == user1 else goals1,
        "power": f"{int(power1)}-{int(power2)}"  # قدرت تیم‌ها برای دیباگ
    }
    
    if goals1 > goals2:
        team1["score"] += 3
        result_details["result"] = "win"
        result_details["result_text"] = f"🏆 {team1['team']} {goals1}-{goals2} برنده شد!"
    elif goals1 < goals2:
        team2["score"] += 3
        result_details["result"] = "win"
        result_details["result_text"] = f"🏆 {team2['team']} {goals2}-{goals1} برنده شد!"
    else:
        team1["score"] += 1
        team2["score"] += 1
        result_details["result"] = "draw"
        result_details["result_text"] = f"🤝 مساوی {goals1}-{goals2}"
    
    # ذخیره برای هر دو تیم
    team1["match_history"].append(result_details)
    
    opponent_details = result_details.copy()
    opponent_details.update({
        "opponent": team1["team"],
        "goals_for": goals2,
        "goals_against": goals1,
        "result": "lose" if goals1 > goals2 else "win" if goals1 < goals2 else "draw"
    })
    team2["match_history"].append(opponent_details)
    
    # ارسال نتایج به کاربران
    try:
        bot.send_message(user1, result_details["result_text"])
        bot.send_message(user2, opponent_details["result_text"])
    except:
        pass
    
    def get_random_player(team, position=None):
        players = [pid for pid in team["players"] if pid in ALL_PLAYERS and (not position or ALL_PLAYERS[pid]["position"] == position)]
        if not players:
            return None
        return random.choice(players)
    
    def generate_event(team, opponent, event_type, score):
        player_id = get_random_player(team, "FW" if event_type == "goal" else None)
        if not player_id:
            player_id = get_random_player(team)
        
        player_pos = ALL_PLAYERS[player_id]["position"]
        player_name = f"{random.choice(PLAYER_NAMES[player_pos])} ({ALL_PLAYERS[player_id]['name']})"
        
        event_text = random.choice(MATCH_EVENTS[event_type]).format(
            player=player_name,
            team=team["team"],
            score=f"{score[0]}-{score[1]}"
        )
        return event_text
    
    def send_to_both(message):
        try:
            bot.send_message(user1, message)
        except:
            pass
        try:
            bot.send_message(user2, message)
        except:
            pass
    
    send_to_both(f"⏰ بازی بین {team1['team']} و {team2['team']} آغاز شد!")
    time.sleep(2)
    
    score = [0, 0]
    events = []
    match_time = 0
    
    while match_time < 5:  # 5 دقیقه بازی
        match_time += 1
        send_to_both(f"⏱️ دقیقه {match_time}:")
        time.sleep(1)
        
        for _ in range(random.randint(2, 4)):
            event_type = random.choices(
                ["goal", "miss", "foul", "corner", "save"],
                weights=[0.2, 0.3, 0.2, 0.2, 0.1]
            )[0]
            
            if random.random() < 0.5:
                team, opponent = team1, team2
                team_idx = 0
            else:
                team, opponent = team2, team1
                team_idx = 1
            
            if event_type == "goal":
                score[team_idx] += 1
            
            event_text = generate_event(team, opponent, event_type, score)
            send_to_both(event_text)
            events.append(event_text)
            time.sleep(1)
    
    if score[0] > score[1]:
        team1["score"] += 3
        team1["coins"] += 50
        team2["coins"] += 20
        result = f"🏆 {team1['team']} برنده شد! نتیجه نهایی {score[0]}-{score[1]}"
    elif score[0] < score[1]:
        team2["score"] += 3
        team2["coins"] += 50
        team1["coins"] += 20
        result = f"🏆 {team2['team']} برنده شد! نتیجه نهایی {score[1]}-{score[0]}"
    else:
        team1["score"] += 1
        team2["score"] += 1
        team1["coins"] += 30
        team2["coins"] += 30
        result = f"🤝 بازی مساوی شد! نتیجه {score[0]}-{score[1]}"
    
    send_to_both(result + "\n\n📊 بازی به پایان رسید!")
    
    match_details = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "result": result,
        "events": events,
        "opponent": team2['team'] if user1 == user1 else team1['team'],
        "score": f"{score[0]}-{score[1]}"
    }
    
    users[user1]["match_history"].append(match_details)
    users[user2]["match_history"].append(match_details)

def run_nightly_game():
    while True:
        now = datetime.datetime.now()
        if now.hour == 16 and now.minute == 23:
            users = load_users()
            plist = list(participants)
            random.shuffle(plist)
            
            for i in range(0, len(plist)-1, 2):
                threading.Thread(
                    target=simulate_live_match,
                    args=(plist[i], plist[i+1], users)
                ).start()
            
            participants.clear()
            save_users(users)
            time.sleep(60 * 5)
        time.sleep(30)

@bot.message_handler(commands=["start"])
def start_command(message):
    uid = str(message.from_user.id)
    users = load_users()

    if uid in users:
        bot.send_message(message.chat.id, "👋 خوش اومدی مجدد!", reply_markup=main_menu())
        return

    if not is_member(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL.strip('@')}"))
        markup.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_join"))
        bot.send_message(message.chat.id, "برای ادامه باید در کانال عضو بشی:", reply_markup=markup)
        return

    user_states[uid] = "awaiting_team"
    bot.send_message(message.chat.id, "🏟️ نام تیم خود را وارد کن:")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if is_member(call.from_user.id):
        uid = str(call.from_user.id)
        user_states[uid] = "awaiting_team"
        bot.send_message(call.message.chat.id, "✅ عضویت تایید شد!\n\n🏟️ حالا نام تیم خودتو وارد کن:")
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو کانال نشدی!")

@bot.message_handler(func=lambda message: user_states.get(str(message.from_user.id)) == "awaiting_team")
def get_team_name(message):
    uid = str(message.from_user.id)
    team_name = message.text.strip()

    if len(team_name) < 3:
        bot.send_message(message.chat.id, "❗ نام تیم باید حداقل ۳ کاراکتر باشد.")
        return

    user_states[uid] = {"step": "awaiting_phone", "team": team_name}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("📱 ارسال شماره تماس", request_contact=True)
    markup.add(btn)

    bot.send_message(message.chat.id, "لطفاً شماره موبایل خود را ارسال کن:", reply_markup=markup)

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
        "last_daily_reward": None
    }

    save_users(users)
    user_states.pop(uid)

    bot.send_message(message.chat.id, "🎉 ثبت‌نام کامل شد. به منوی اصلی خوش اومدی!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🏆 برترین‌ها")
def show_top_players(m):
    users = load_users()
    if not users:
        return bot.send_message(m.chat.id, "❌ هنوز کاربری ثبت‌نام نکرده است.")
    
    leaderboard = []
    for uid, user in users.items():
        stats = {
            "team": user["team"],
            "score": user["score"],
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "gf": 0,  # گل‌های زده
            "ga": 0   # گل‌های خورده
        }
        
        for match in user["match_history"]:
            if match["result"] == "win":
                stats["wins"] += 1
            elif match["result"] == "lose":
                stats["losses"] += 1
            else:
                stats["draws"] += 1
            
            stats["gf"] += match["goals_for"]
            stats["ga"] += match["goals_against"]
        
        leaderboard.append(stats)
    
    # مرتب‌سازی بر اساس امتیاز > تفاضل گل > گل‌زده
    leaderboard.sort(key=lambda x: (-x["score"], -(x["gf"] - x["ga"]), -x["gf"]))
    
    text = "🏆 جدول برترین‌ها (بر اساس امتیاز و عملکرد):\n\n"
    for i, team in enumerate(leaderboard[:10], 1):
        text += (
            f"{i}. {team['team']}\n"
            f"⭐ امتیاز: {team['score']} (🏆{team['wins']} 🏳️{team['losses']} 🤝{team['draws']})\n"
            f"⚽ گل‌ها: {team['gf']}-{team['ga']} (تفاضل: {team['gf'] - team['ga']})\n\n"
        )
    
    bot.send_message(m.chat.id, text, reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "🎁 پاداش روزانه")
def daily_reward_handler(m):
    uid = str(m.from_user.id)
    users = load_users()
    
    if uid not in users:
        return bot.send_message(m.chat.id, "❌ ابتدا ثبت‌نام کنید.")
    
    now = datetime.datetime.now()
    last_reward = users[uid].get("last_daily_reward")
    
    if last_reward:
        last_date = datetime.datetime.strptime(last_reward, "%Y-%m-%d").date()
        if now.date() == last_date:
            return bot.send_message(m.chat.id, "❌ امروز قبلاً پاداش دریافت کرده‌اید. فردا دوباره امتحان کنید.", reply_markup=back_menu())
    
    users[uid]["coins"] += 50
    users[uid]["last_daily_reward"] = now.strftime("%Y-%m-%d")
    save_users(users)
    
    bot.send_message(m.chat.id, "🎉 پاداش روزانه شما دریافت شد! 50 سکه به حساب شما اضافه شد.", reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "🏪 فروشگاه بازیکن")
def show_store(m):
    uid = str(m.from_user.id)
    users = load_users()
    if uid not in users:
        return bot.send_message(m.chat.id, "❌ ابتدا ثبت‌نام کن")

    text = "🏪 لیست بازیکنان قابل خرید:\n\n"
    markup = types.InlineKeyboardMarkup()
    for pid, pl in ALL_PLAYERS.items():
        if pid in users[uid]["players"]:
            continue

        price = f"{pl['price_gems']} جم / {pl['price_coins']} سکه"
        btn = types.InlineKeyboardButton(f"{pl['name']} ({pl['position']}) ({pl['overall']}) | {price}", callback_data=f"buy_{pid}")
        markup.add(btn)

    if len(markup.keyboard) == 0:
        return bot.send_message(m.chat.id, "✅ همه بازیکنان رو خریدی!", reply_markup=back_menu())

    bot.send_message(m.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def handle_buy(c):
    uid = str(c.from_user.id)
    users = load_users()
    pid = c.data.replace("buy_", "")

    if pid not in ALL_PLAYERS:
        return bot.answer_callback_query(c.id, "❌ بازیکن پیدا نشد.")

    if pid in users[uid]["players"]:
        return bot.answer_callback_query(c.id, "❗ قبلاً خریدی")

    if len(users[uid]["players"]) >= 8:
        return bot.answer_callback_query(c.id, "❗ حداکثر ۸ بازیکن مجاز است.")

    player = ALL_PLAYERS[pid]
    if users[uid]["gems"] >= player["price_gems"]:
        users[uid]["gems"] -= player["price_gems"]
    elif users[uid]["coins"] >= player["price_coins"]:
        users[uid]["coins"] -= player["price_coins"]
    else:
        return bot.answer_callback_query(c.id, "❌ سکه یا جم کافی نداری!")

    users[uid]["players"].append(pid)
    save_users(users)

    bot.answer_callback_query(c.id, "✅ خرید با موفقیت انجام شد!")
    bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    bot.send_message(c.message.chat.id, f"🎉 بازیکن {player['name']} با موفقیت به تیمت اضافه شد.", reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "📋 ترکیب و تاکتیک")
def tactic_menu(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📌 انتخاب ترکیب", "⚔️ سبک بازی")
    markup.row("🧠 تاکتیک", "🪤 تله آفساید", "🔥 پرسینگ")
    markup.row("📊 شماتیک")
    markup.row("بازگشت به منو")
    bot.send_message(m.chat.id, "⚙️ یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📌 انتخاب ترکیب")
def formation_handler(m):
    uid = str(m.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    formations = ["۱-۲-۲", "۱-۱-۳", "۱-۳-۱", "۱-۴"]
    for f in formations:
        markup.add(f)
    markup.add("بازگشت به منو")
    user_states[uid] = "formation"
    bot.send_message(m.chat.id, "🎯 ترکیب مورد نظر را انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🧠 تاکتیک")
def mode_handler(m):
    uid = str(m.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    modes = ["هجومی", "دفاعی", "متعادل"]
    for m_ in modes:
        markup.add(m_)
    markup.add("بازگشت به منو")
    user_states[uid] = "mode"
    bot.send_message(m.chat.id, "🎯 تاکتیک مورد نظر را انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "⚔️ سبک بازی")
def style_handler(m):
    uid = str(m.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    styles = ["پاسکاری", "بازی با وینگ", "ضدحمله"]
    for s in styles:
        markup.add(s)
    markup.add("بازگشت به منو")
    user_states[uid] = "style"
    bot.send_message(m.chat.id, "🎮 سبک بازی مورد نظر را انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🪤 تله آفساید")
def offside_handler(m):
    uid = str(m.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بذار", "نذار", "بازگشت به منو")
    user_states[uid] = "offside"
    bot.send_message(m.chat.id, "🪤 تله آفساید رو فعال می‌کنی؟", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔥 پرسینگ")
def pressing_handler(m):
    uid = str(m.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("پرس ۱۰۰ درصد", "پرس ۵۰ درصد", "پرس نمی‌خوام")
    markup.add("بازگشت به منو")
    user_states[uid] = "press"
    bot.send_message(m.chat.id, "🔥 شدت پرسینگ را مشخص کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(str(m.from_user.id)) in ["formation", "mode", "style", "offside", "press"])
def save_tactic(m):
    uid = str(m.from_user.id)
    field = user_states[uid]
    users = load_users()
    users[uid]["tactic"][field] = m.text
    save_users(users)
    bot.send_message(m.chat.id, f"✅ {field} ذخیره شد.", reply_markup=back_menu())
    user_states.pop(uid)

@bot.message_handler(func=lambda m: m.text == "📊 شماتیک")
def show_schematic(m):
    uid = str(m.from_user.id)
    users = load_users()
    if uid not in users:
        return bot.send_message(m.chat.id, "❌ ابتدا ثبت‌نام کن")

    players = users[uid]["players"]
    lines = {"GK": [], "DF": [], "MF": [], "FW": []}
    for pid in players:
        if pid in ALL_PLAYERS:
            p = ALL_PLAYERS[pid]
            lines[p["position"]].append(p["name"])

    text = f"📊 شماتیک تیم {users[uid]['team']}:\n\n"
    if lines["FW"]: text += "⚽ مهاجم: " + "  ".join(lines["FW"]) + "\n"
    if lines["MF"]: text += "🏃 هافبک: " + "  ".join(lines["MF"]) + "\n"
    if lines["DF"]: text += "🛡 مدافع: " + "  ".join(lines["DF"]) + "\n"
    if lines["GK"]: text += "🧤 دروازه‌بان: " + "  ".join(lines["GK"]) + "\n"

    bot.send_message(m.chat.id, text or "❌ ترکیب خالیه!", reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "🎮 بازی شبانه")
def join_night_game(m):
    uid = str(m.from_user.id)
    participants.add(uid)
    bot.send_message(m.chat.id, "🕘 شما در بازی شبانه امشب ثبت‌نام شدید.", reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "📄 گزارش بازی")
def match_report(m):
    uid = str(m.from_user.id)
    users = load_users()
    
    if uid not in users or not users[uid]["match_history"]:
        return bot.send_message(m.chat.id, "❌ هیچ بازی انجام نداده‌اید.")
    
    text = f"📋 تاریخچه بازی‌های {users[uid]['team']}:\n\n"
    
    for match in reversed(users[uid]["match_history"]):
        text += (
            f"📅 {match['date']}\n"
            f"🆚 مقابل: {match['opponent']}\n"
            f"🔢 نتیجه نهایی: {match['score']}\n"
            f"🏷️ وضعیت: {'برد' if match['result'] == 'win' else 'باخت' if match['result'] == 'lose' else 'مساوی'}\n"
            f"⚡ رویدادهای کلیدی:\n"
        )
        
        # نمایش 3 رویداد برجسته
        for i, event in enumerate(match.get("events", [])[:3], 1):
            text += f"{i}. {event}\n"
        
        text += "――――――――――――――\n"
        
        if len(text) > 3000:
            bot.send_message(m.chat.id, text)
            text = ""
    
    if text:
        bot.send_message(m.chat.id, text, reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "👛 کیف پول")
def wallet(m):
    uid = str(m.from_user.id)
    users = load_users()
    user = users[uid]
    text = f"""
💰 کیف پول شما:

🪙 سکه‌ها: {user['coins']}
💎 جم‌ها: {user['gems']}

📥 تبدیل سکه به جم: هر 100 سکه = 1 جم
🧾 ارسال فیش پرداخت (متن یا عکس)

TRX Address:
{TRON_ADDRESS}
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔄 تبدیل سکه به جم", "📤 ارسال فیش")
    markup.add("بازگشت به منو")
    bot.send_message(m.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔄 تبدیل سکه به جم")
def convert_coins(m):
    uid = str(m.from_user.id)
    users = load_users()
    if users[uid]["coins"] >= 100:
        users[uid]["coins"] -= 100
        users[uid]["gems"] += 1
        save_users(users)
        bot.send_message(m.chat.id, "✅ تبدیل انجام شد!", reply_markup=back_menu())
    else:
        bot.send_message(m.chat.id, "❌ سکه کافی نداری!", reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "📤 ارسال فیش")
def ask_receipt(m):
    bot.send_message(m.chat.id, "🧾 فیش پرداخت را ارسال کن (عکس یا متن):", reply_markup=back_menu())

@bot.message_handler(content_types=["text"], func=lambda m: m.reply_to_message and m.reply_to_message.text == "🧾 فیش پرداخت را ارسال کن (عکس یا متن):")
def handle_text_receipt(m):
    bot.send_message(ADMIN_ID, f"📤 فیش متنی جدید از {m.from_user.first_name}:\n{m.text}")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{m.from_user.id}"))
    markup.add(types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{m.from_user.id}"))
    bot.send_message(ADMIN_ID, f"🎯 فیش جدید برای بررسی:", reply_markup=markup)
    bot.send_message(m.chat.id, "✅ فیش شما دریافت شد و در حال بررسی است.", reply_markup=back_menu())

@bot.message_handler(content_types=["photo"], func=lambda m: m.reply_to_message and m.reply_to_message.text == "🧾 فیش پرداخت را ارسال کن (عکس یا متن):")
def handle_photo_receipt(m):
    bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{m.from_user.id}"))
    markup.add(types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{m.from_user.id}"))
    bot.send_message(ADMIN_ID, f"🎯 فیش جدید برای بررسی:", reply_markup=markup)
    bot.send_message(m.chat.id, "✅ فیش شما دریافت شد و در حال بررسی است.", reply_markup=back_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_") or c.data.startswith("reject_"))
def handle_receipt_admin(c):
    uid = c.data.split("_")[1]
    users = load_users()

    if c.data.startswith("confirm_"):
        users[uid]["coins"] += 100
        save_users(users)
        bot.send_message(int(uid), "✅ فیش تایید شد! 100 سکه به حسابت اضافه شد.")
        bot.edit_message_text("✔️ تایید شد", c.message.chat.id, c.message.message_id)
    else:
        bot.send_message(int(uid), "❌ فیش رد شد.")
        bot.edit_message_text("❌ رد شد", c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: m.text == "بازگشت به منو")
def back_to_main(m):
    bot.send_message(m.chat.id, "منوی اصلی:", reply_markup=main_menu())

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است"

def start_bot():
    threading.Thread(target=run_nightly_game).start()
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    print("ربات در حال اجراست...")
    start_bot()
