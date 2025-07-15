import telebot, json, random, datetime, threading
from telebot import types

BOT_TOKEN = '7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc'
ADMIN_ID = 5542927340
CHANNEL_USERNAME = '@Specialcoach1'
TRON_ADDRESS = 'TJ4xrwKJzKjk6FgKfuuqwah3Az5Ur22kJb'

bot = telebot.TeleBot(BOT_TOKEN)

# Load/save
def load(path):
    try: return json.load(open(path, encoding='utf-8'))
    except: return {}
def save(path, data):
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

users = load('data/users.json')
players = load('data/players.json')
matches = load('data/matches.json')

states = {}
pending_payment = {}

# Subscription check
def is_subscribed(uid):
    try:
        st = bot.get_chat_member(CHANNEL_USERNAME, uid).status
        return st in ['member','administrator','creator']
    except:
        return False

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('📋لیست بازیکنان','🛒فروشگاه','⚽ترکیب و تاکتیک')
    kb.row('⏱️شروع بازی','🏆برترین‌ها','💼کیف پول')
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    uid = str(m.from_user.id)
    if not is_subscribed(m.from_user.id):
        bot.send_message(m.chat.id, f"لطفاً ابتدا عضو کانال شوید:\n{CHANNEL_USERNAME}")
        return
    if uid not in users:
        states[uid] = 'ask_team'
        bot.send_message(m.chat.id, "نام تیم خود را وارد کنید:")
    else:
        bot.send_message(m.chat.id, "خوش آمدید!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: states.get(str(m.from_user.id)) == 'ask_team')
def ask_team(m):
    uid = str(m.from_user.id)
    users[uid] = {"team_name": m.text, "contact": None, "players": [], "coins":0, "gems":0,
                  "points":0,"wins":0,"losses":0,"draws":0, "formation":None,"tactics":{}}
    save('data/users.json', users)
    states[uid] = 'ask_contact'
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📞ارسال شماره من", request_contact=True))
    bot.send_message(m.chat.id, "لطفاً شماره تماس خود را ارسال کنید:", reply_markup=kb)

@bot.message_handler(content_types=['contact'])
def ask_contact(m):
    uid = str(m.from_user.id)
    if states.get(uid) != 'ask_contact': return
    users[uid]['contact'] = m.contact.phone_number
    save('data/users.json', users)
    states.pop(uid)
    bot.send_message(m.chat.id, "✅ ثبت‌نام کامل شد!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text in ['📋لیست بازیکنان','🛒فروشگاه','⚽ترکیب و تاکتیک','⏱️شروع بازی','🏆برترین‌ها','💼کیف پول'])
def menu(m):
    uid = str(m.from_user.id); u=users.get(uid)
    if not u:
        bot.send_message(m.chat.id, "لطفاً /start را بزنید.")
        return
    t = m.text
    if t == '📋لیست بازیکنان':
        msg = "\n".join(f"{p['id']}. {p['name']} – skill:{p['skill']} – {p['price_coins']}سکه/{p['price_gems']}جم" for p in players)
        bot.send_message(m.chat.id, msg)
    elif t == '🛒فروشگاه':
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add('🥇خرید جم','👥خرید بازیکن','🔙بازگشت')
        bot.send_message(m.chat.id, "فروشگاه:", reply_markup=kb)
    elif t == '👥خرید بازیکن':
        bot.send_message(m.chat.id, "لطفاً آی‌دی بازیکن را وارد کنید:")
        states[uid] = 'buy_player'
    elif t == '🥇خرید جم':
        bot.send_message(m.chat.id, f"لطفاً فیش واریز را ارسال کنید (عکس یا متن). آدرس:\n{TRON_ADDRESS}")
        states[uid] = 'await_payment'
    elif t == '⚽ترکیب و تاکتیک':
        # ترکيب + تاکتيک منو
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add('۱-۲-۲','۱-۱-۳','۱-۳-۱','۱-۴')
        kb.add('هجومی','دفاعی','متعادل')
        kb.add('پاسکاری','بازی با وینگ')
        kb.add('تله اوفساید','نپرس')
        kb.add('پرس ۱۰۰','پرس ۵۰','پرس ۰')
        bot.send_message(m.chat.id, "لطفاً ترکیب و تاکتیک‌ها را انتخاب کنید:", reply_markup=kb)
        states[uid] = 'tactic'
    elif t == '⏱️شروع بازی':
        bot.send_message(m.chat.id, "🔄 بازی ساعت ۲۱ به‌صورت رندوم شروع می‌شود.")
    elif t == '🏆برترین‌ها':
        top = sorted(users.items(), key=lambda x: x[1]['points'], reverse=True)[:10]
        msg = "🏆برترین‌ها:\n"
        for i,(uidk,inf) in enumerate(top,1):
            total = inf['wins']+inf['draws']+inf['losses']
            rate = f"{inf['wins']/total*100:.1f}%" if total else "0%"
            msg+=f"{i}. {inf['team_name']} – {rate} – {inf['points']}امتیاز\n"
        bot.send_message(m.chat.id, msg)
    elif t == '💼کیف پول':
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add('📤واریز','📥خرید جم','🔙بازگشت')
        bot.send_message(m.chat.id, f"سکه:{u['coins']} جم:{u['gems']}\nآدرس ترون:\n{TRON_ADDRESS}", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(str(m.from_user.id))=='buy_player')
def process_buy(m):
    uid=str(m.from_user.id); u=users[uid]
    pid=int(m.text)
    p=next((x for x in players if x['id']==pid),None)
    if not p:
        bot.send_message(m.chat.id,"⚠️ ID نامعتبر.")
    else:
        cost = p['price_gems'] if u['gems']>=p['price_gems'] else None
        if cost and u['gems']>=p['price_gems']:
            u['gems']-=p['price_gems']; u['players'].append(p['id'])
            bot.send_message(m.chat.id,"✅ خرید انجام شد."); save('data/users.json',users)
        elif u['coins']>=p['price_coins']:
            u['coins']-=p['price_coins']; u['players'].append(p['id'])
            bot.send_message(m.chat.id,"✅ خرید انجام شد."); save('data/users.json',users)
        else:
            bot.send_message(m.chat.id,"⚠️ موجودی کافی نیست.")
    states.pop(uid); bot.send_message(m.chat.id, "بازگشت به منو.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: states.get(str(m.from_user.id))=='await_payment')
def handle_payment(m):
    uid=str(m.from_user.id)
    pending_payment[uid] = m.text or m.photo
    bot.send_message(ADMIN_ID, f"💰 فیش جدید از @{m.from_user.username}:\n{m.text or '<عکس>'}",
                     reply_markup=types.InlineKeyboardMarkup().add(
                         types.InlineKeyboardButton("✅ تأیید", callback_data=f"pay_ok:{uid}"),
                         types.InlineKeyboardButton("❌ رد", callback_data=f"pay_no:{uid}")
                     ))
    bot.send_message(m.chat.id,"✅ فیش ارسال شد، منتظر تأیید ادمین باشید.")
    states.pop(uid)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith('pay_'))
def admin_pay(c):
    op, uid = c.data.split(':')
    u=users[uid]
    if op=='pay_ok':
        u['coins'] += 100; save('data/users.json',users)
        bot.send_message(uid, "✅ پرداخت تأیید شد؛ ۱۰۰ سکه به حساب شما اضافه شد.")
        bot.answer_callback_query(c.id, "تأیید شد")
    else:
        bot.send_message(uid,"❌ پرداخت شما رد شد.")
        bot.answer_callback_query(c.id, "رد شد")

@bot.message_handler(func=lambda m: states.get(str(m.from_user.id))=='tactic')
def save_tactic(m):
    uid=str(m.from_user.id); u=users[uid]
    key=m.text
    # simplified storage
    u['tactics'][key] = u['tactics'].get(key, key)
    save('data/users.json',users)
    bot.send_message(m.chat.id,f"✅ گزینه ثبت شد: {key}", reply_markup=main_menu())
    states.pop(uid)

def simulate_matches():
    now = datetime.datetime.now()
    # schedule at 21:00 daily
    next_run = now.replace(hour=21,minute=0,second=0) \
                + datetime.timedelta(days=(0 if now.hour<21 else 1))
    delay=(next_run-now).total_seconds()
    threading.Timer(delay, run_matches).start()

def run_matches():
    uids=list(users.keys())
    random.shuffle(uids)
    pairs = [uids[i:i+2] for i in range(0,len(uids),2)]
    for p in pairs:
        if len(p)<2: continue
        a,b = p
        # compare number of players as proxy
        sa=len(users[a]['players']); sb=len(users[b]['players'])
        if sa>sb: res=(a,b,1)
        elif sb>sa: res=(b,a,1)
        else: res=(a,b,0)
        award(*res)
    save('data/users.json',users)
    for uid in users:
        bot.send_message(uid, "🔔 بازی امشب انجام شد! برای مشاهده گزارش /start را بزنید.")
    simulate_matches()

def award(winner, loser, draw):
    if draw==0:
        users[winner]['points']+=5; users[loser]['points']+=5
        users[winner]['draws']+=1; users[loser]['draws']+=1
    else:
        users[winner]['points']+=20; users[winner]['wins']+=1
        users[loser]['points']-=10; users[loser]['losses']+=1

if __name__=='__main__':
    simulate_matches()
    bot.remove_webhook()
    bot.infinity_polling()
