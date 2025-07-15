import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler
)
from apscheduler.schedulers.background import BackgroundScheduler
import random
from datetime import datetime
import json
import os

# تنظیمات پایه
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc'
ADMIN_ID = 5542927340
CHANNEL = '@Specialcoach1'
TRON_ADDRESS = 'TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb'

# حالت‌های گفتگو
JOIN_CHANNEL, TEAM_NAME, SHARE_CONTACT = range(3)

# ساختارهای داده
players = [
    {"id": i, "name": f"بازیکن ضعیف {i}", "price": 1, "coins": 10, "attack": 50+i, "defense": 50-i, "stamina": 50} for i in range(1, 26)
] + [
    {"id": i, "name": f"بازیکن خوب {i-25}", "price": 10+(i-26), "coins": 100+(i-26)*5, "attack": 70+(i-26)*2, "defense": 60+(i-26), "stamina": 65+(i-26)} for i in range(26, 51)
]

formations = [
    {"id": 1, "name": "1-2-2", "description": "دفاع محور", "attack": 0.95, "defense": 1.05},
    {"id": 2, "name": "1-1-3", "description": "حمله محور", "attack": 1.05, "defense": 0.95},
    {"id": 3, "name": "1-3-1", "description": "متوازن", "attack": 1.0, "defense": 1.0},
    {"id": 4, "name": "1-4", "description": "دفاع بسیار قوی", "attack": 0.9, "defense": 1.1},
]

tactics = [
    {"id": 1, "name": "هجومی", "attack_boost": 15, "defense_penalty": 10},
    {"id": 2, "name": "دفاعی", "defense_boost": 15, "attack_penalty": 10},
    {"id": 3, "name": "متعادل", "attack_boost": 5, "defense_boost": 5},
]

play_styles = [
    {"id": 1, "name": "پاسکاری", "effect": "pass_accuracy"},
    {"id": 2, "name": "بازی با وینگ", "effect": "wing_attack"},
]

# مدیریت داده‌ها
def load_data():
    try:
        with open('data.json', 'r') as f:
            return json.load(f)
    except:
        return {"users": {}, "matches": [], "transactions": []}

def save_data(data):
    with open('data.json', 'w') as f:
        json.dump(data, f)

# دستورات کاربر
def start(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    if not is_member(user_id):
        keyboard = [[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL[1:]}")]]
        update.message.reply_text("برای استفاده از ربات لطفا ابتدا در کانال ما عضو شوید:", reply_markup=InlineKeyboardMarkup(keyboard))
        return JOIN_CHANNEL
    return ask_team_name(update)

def is_member(user_id: int) -> bool:
    # در حالت واقعی باید چک شود کاربر در کانال عضو هست یا نه
    return True

def ask_team_name(update: Update) -> int:
    update.message.reply_text("لطفا نام تیم خود را وارد کنید:")
    return TEAM_NAME

def get_team_name(update: Update, context: CallbackContext) -> int:
    context.user_data['team_name'] = update.message.text
    update.message.reply_text(
        "لطفا شماره تماس خود را با دکمه زیر به اشتراک بگذارید:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("اشتراک گذاری شماره تماس", request_contact=True)]], resize_keyboard=True)
    )
    return SHARE_CONTACT

def get_contact(update: Update, context: CallbackContext) -> int:
    data = load_data()
    user_id = update.effective_user.id
    data["users"][str(user_id)] = {
        "username": update.effective_user.username,
        "team_name": context.user_data['team_name'],
        "phone": update.message.contact.phone_number,
        "coins": 0,
        "gems": 0,
        "points": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "players": [],
        "formation": None,
        "tactic": None,
        "play_style": None,
        "offside_trap": False,
        "pressing": None
    }
    save_data(data)
    update.message.reply_text("ثبت نام شما با موفقیت انجام شد!", reply_markup=ReplyKeyboardRemove())
    show_main_menu(update)
    return ConversationHandler.END

def show_main_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("ترکیب و تاکتیک", callback_data="formation_menu")],
        [InlineKeyboardButton("لیست بازیکنان", callback_data="players_list_1")],
        [InlineKeyboardButton("کیف پول", callback_data="wallet")],
        [InlineKeyboardButton("برترین‌ها 🏆", callback_data="top_players")],
        [InlineKeyboardButton("گزارش بازی‌ها", callback_data="match_reports")]
    ]
    update.message.reply_text("منوی اصلی:", reply_markup=InlineKeyboardMarkup(keyboard))

# سیستم بازی
def schedule_daily_matches():
    scheduler = BackgroundScheduler()
    scheduler.add_job(start_daily_matches, 'cron', hour=21, minute=0, timezone='Asia/Tehran')
    scheduler.start()

def start_daily_matches():
    data = load_data()
    active_users = [uid for uid in data["users"] if data["users"][uid].get("formation")]
    random.shuffle(active_users)
    
    for i in range(0, len(active_users)-1, 2):
        user1, user2 = active_users[i], active_users[i+1]
        result = play_match(user1, user2, data)
        data["matches"].append({
            "user1": user1,
            "user2": user2,
            "result": result,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
    
    save_data(data)

def play_match(user1, user2, data):
    team1 = data["users"][user1]
    team2 = data["users"][user2]
    
    score1 = calculate_team_score(team1)
    score2 = calculate_team_score(team2)
    
    if abs(score1 - score2) < 5:
        data["users"][user1]["points"] += 5
        data["users"][user2]["points"] += 5
        data["users"][user1]["draws"] += 1
        data["users"][user2]["draws"] += 1
        return "draw"
    elif score1 > score2:
        data["users"][user1]["points"] += 20
        data["users"][user2]["points"] -= 10
        data["users"][user1]["wins"] += 1
        data["users"][user2]["losses"] += 1
        return f"{user1}_win"
    else:
        data["users"][user1]["points"] -= 10
        data["users"][user2]["points"] += 20
        data["users"][user1]["losses"] += 1
        data["users"][user2]["wins"] += 1
        return f"{user2}_win"

def calculate_team_score(team):
    if not team["players"]:
        return 0
    
    avg_stats = {
        "attack": sum(p["attack"] for p in team["players"]) / len(team["players"]),
        "defense": sum(p["defense"] for p in team["players"]) / len(team["players"]),
        "stamina": sum(p["stamina"] for p in team["players"]) / len(team["players"])
    }
    
    formation = next(f for f in formations if f["id"] == team["formation"])
    tactic = next(t for t in tactics if t["id"] == team["tactic"])
    
    attack_score = avg_stats["attack"] * formation["attack"] * (1 + tactic["attack_boost"]/100)
    defense_score = avg_stats["defense"] * formation["defense"] * (1 + tactic["defense_boost"]/100)
    
    return (attack_score + defense_score + avg_stats["stamina"]) / 3 * random.uniform(0.95, 1.05)

# اجرای ربات
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            JOIN_CHANNEL: [MessageHandler(Filters.text & ~Filters.command, lambda u,c: ask_team_name(u) if is_member(u.effective_user.id) else u.message.reply_text("لطفا ابتدا در کانال عضو شوید!"))],
            TEAM_NAME: [MessageHandler(Filters.text & ~Filters.command, get_team_name)],
            SHARE_CONTACT: [MessageHandler(Filters.contact, get_contact)],
        },
        fallbacks=[CommandHandler('cancel', lambda u,c: u.message.reply_text('ثبت نام لغو شد.'))]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(button_handler))

    schedule_daily_matches()
    updater.start_polling()
    updater.idle()

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == "formation_menu":
        show_formation_menu(query)
    elif data.startswith("select_formation_"):
        select_formation(query, context)
    elif data == "players_list_1":
        show_players_list(query, 1)
    elif data.startswith("players_list_"):
        show_players_list(query, int(data.split("_")[2]))
    elif data == "wallet":
        show_wallet(query)
    elif data == "top_players":
        show_top_players(query)
    elif data == "match_reports":
        show_match_reports(query)

def show_formation_menu(query):
    keyboard = [[InlineKeyboardButton(f["name"], callback_data=f"select_formation_{f['id']}")] for f in formations]
    query.edit_message_text("ترکیب مورد نظر خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

def select_formation(query, context):
    formation_id = int(query.data.split("_")[2])
    context.user_data['formation'] = formation_id
    show_tactics_menu(query)

def show_tactics_menu(query):
    keyboard = [[InlineKeyboardButton(t["name"], callback_data=f"select_tactic_{t['id']}")] for t in tactics]
    query.edit_message_text("تاکتیک مورد نظر خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

def show_players_list(query, page):
    start_idx = (page-1)*5
    end_idx = min(start_idx+5, len(players))
    
    keyboard = [
        [InlineKeyboardButton(f"{p['name']} - {p['price']} جم - {p['coins']} سکه", callback_data=f"view_player_{p['id']}")] 
        for p in players[start_idx:end_idx]
    ]
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("صفحه قبل", callback_data=f"players_list_{page-1}"))
    if end_idx < len(players):
        nav_buttons.append(InlineKeyboardButton("صفحه بعد", callback_data=f"players_list_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data="main_menu")])
    
    query.edit_message_text(f"لیست بازیکنان (صفحه {page}):", reply_markup=InlineKeyboardMarkup(keyboard))

def show_wallet(query):
    data = load_data()
    user_id = str(query.from_user.id)
    user = data["users"].get(user_id, {"coins": 0, "gems": 0})
    
    keyboard = [
        [InlineKeyboardButton("خرید جم (100 سکه = 1 جم)", callback_data="buy_gems")],
        [InlineKeyboardButton("شارژ کیف پول", callback_data="charge_wallet")],
        [InlineKeyboardButton("بازگشت", callback_data="main_menu")]
    ]
    
    query.edit_message_text(
        f"موجودی شما:\n🎟️ سکه: {user['coins']}\n💎 جم: {user['gems']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_top_players(query):
    data = load_data()
    top_users = sorted(
        [(uid, data["users"][uid]) for uid in data["users"]],
        key=lambda x: (-x[1]["points"], -x[1]["wins"])
    )[:10]
    
    text = "🏆 برترین‌ها:\n\n"
    for i, (uid, user) in enumerate(top_users, 1):
        total = user["wins"] + user["draws"] + user["losses"]
        win_rate = (user["wins"] / total * 100) if total > 0 else 0
        text += f"{i}. {user['team_name']} - برد: {win_rate:.1f}% - امتیاز: {user['points']}\n"
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="main_menu")]]))

if __name__ == '__main__':
    main()
