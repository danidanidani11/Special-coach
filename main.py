import telebot
from flask import Flask, request
import threading, schedule, time, json, random

TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
CHANNEL = "@Specialcoach1"
ADMIN_ID = 5542927340
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

def load_json(path):
    try:
        with open(path,'r') as f: return json.load(f)
    except: return {}

def save_json(path,data):
    with open(path,'w') as f: json.dump(data,f,indent=2)

def get_user(uid):
    return load_json("users.json").get(str(uid))

def save_user(uid,data):
    users=load_json("users.json")
    users[str(uid)]=data
    save_json("users.json",users)

def is_member(uid):
    try:
        s=bot.get_chat_member(CHANNEL,uid).status
        return s in ["member","administrator","creator"]
    except: return False

def give_initial_players():
    allp=load_json("players.json")
    localsp=[p for p in allp if p["name"].startswith("Local")]
    return random.sample(localsp,5)

@bot.message_handler(commands=["start"])
def start(m):
    if not is_member(m.chat.id):
        inline=telebot.types.InlineKeyboardMarkup()
        btn=telebot.types.InlineKeyboardButton("عضویت در کانال",url=f"https://t.me/{CHANNEL[1:]}")
        inline.add(btn)
        return bot.send_message(m.chat.id,"🔐 ابتدا عضو کانال شو",reply_markup=inline)
    users=load_json("users.json")
    if str(m.chat.id) not in users:
        users[str(m.chat.id)]={"step":None,"coins":0,"gems":0}
        save_json("users.json",users)
    users=str(m.chat.id)

    bot.send_message(m.chat.id,"✅ سلام مربی! خوش برگشتی.",reply_markup=None)
    show_menu(m.chat.id)

@bot.message_handler(content_types=['contact'])
def handle_contact(m):
    # no change

@bot.callback_query_handler(lambda c: c.data.startswith("confirm_receipt:"))
def confirm_receipt(c):
    parts = c.data.split(":")
    user_id = int(parts[1])
    admin_id = int(parts[2])  # این مقدار فقط برای بررسی سازگاری گذاشته شده، می‌تونی حذفش کنی
    amount = int(parts[3])

    if c.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(c.id, "❗ فقط ادمین می‌تونه این کار رو انجام بده.")

    user = get_user(user_id)
    if not user:
        return bot.answer_callback_query(c.id, "❌ کاربر پیدا نشد!")

    user['coins'] += amount
    save_user(user_id, user)

    bot.answer_callback_query(c.id, "✅ سکه به کاربر اضافه شد.")
    bot.send_message(user_id, f"✅ {amount} سکه با موفقیت به حسابت اضافه شد.")
    bot.edit_message_text("✅ رسید تایید شد و سکه اضافه شد.", c.message.chat.id, c.message.message_id)

@bot.callback_query_handler(lambda c:c.data=="back_to_menu")
def back(c):
    bot.send_message(c.message.chat.id,"⏮ بازگشت به منو")
    show_menu(c.message.chat.id)

# handle msgs:
@bot.message_handler(func=lambda m:True)
def h(m):
    if not is_member(m.chat.id): return start(m)
    u=get_user(m.chat.id)
    if not u: return start(m)
    txt=m.text

    if txt=="🪙 فروشگاه":
        kb=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🎟 خرید سکه","💎 خرید جم","🔙 بازگشت")
        u['step']="shop"
        save_user(m.chat.id,u)
        return bot.send_message(m.chat.id,"🪙 فروشگاه: انتخاب کن",reply_markup=kb)
    if u.get('step')=="shop":
        if txt=="🎟 خرید سکه":
            bot.send_message(m.chat.id,"📥 برای خرید سکه، مبلغ رو (عدد) بفرست:")
            u['step']="buy_coins"
            save_user(m.chat.id,u);return
        if txt=="💎 خرید جم":
            bot.send_message(m.chat.id,"📥 برای خرید جم، عدد مورد نظر رو بفرست:")
            u['step']="buy_gems"
            save_user(m.chat.id,u);return
        if txt=="🔙 بازگشت":
            u['step']=None;save_user(m.chat.id,u)
            return show_menu(m.chat.id)
    if u.get('step')=="buy_coins":
        try:
            amt=int(txt)
        except: return bot.send_message(m.chat.id,"❌ عدد معتبر بفرست")
        bot.send_message(m.chat.id,f"✅ رسید {amt} سکه ارسال شد، منتظر تایید ادمین",reply_markup=None)
        bot.send_message(ADMIN_ID,f"📥 رسید خرید {amt} سکه از @{m.from_user.username or m.chat.id}",reply_markup=telebot.types.InlineKeyboardMarkup().add(telebot.types.InlineKeyboardButton("✅ تأیید",callback_data=f"confirm_receipt:{m.chat.id}:{0}:{amt}"),telebot.types.InlineKeyboardButton("❌ رد",callback_data="back_to_menu")))
        u['step']=None;save_user(m.chat.id,u);return
    if u.get('step')=="buy_gems":
        try:
            amt=int(txt); prices={1:20,5:90,10:170}
            if amt not in prices: return bot.send_message(m.chat.id,"عدد معتبر نیست")
        except: return bot.send_message(m.chat.id,"عدد معتبر بفرست")
        if u['coins']<prices[amt]: return bot.send_message(m.chat.id,"سکه کافی نیست")
        u['coins']-=prices[amt];u['gems']+=amt
        u['step']=None;save_user(m.chat.id,u)
        return bot.send_message(m.chat.id,f"✅ {amt} جم خریدی، سکه باقیمانده: {u['coins']}")
    if txt=="📋 ترکیب و تاکتیک":
        kb=telebot.types.InlineKeyboardMarkup(row_width=2)
        sections=[
            ("chg_form","تغییر ترکیب"),("chg_tact","تغییر تاکتیک"),
            ("sv_form","ذخیره چینش"),("ld_form","بارگذاری چینش"),
            ("analyze","آنالیز")
        ]
        for code,lab in sections:
            kb.add(telebot.types.InlineKeyboardButton(lab,callback_data=code))
        return bot.send_message(m.chat.id,"📐 بخش ترکیب و تاکتیک:",reply_markup=kb)
    if txt=="👤 پروفایل":
        return show_profile(m)
    if txt=="/start":
        return start(m)

    return bot.send_message(m.chat.id,"❗ از منو استفاده کن.")

# بخش‌های callback برای ck فرم، آنالیز و ذخیره و بارگذاری رو ساده نگهدار:
@bot.callback_query_handler(lambda c:c.data in ["chg_form","chg_tact","sv_form","ld_form","analyze"])
def cb2(c):
    u=get_user(c.message.chat.id)
    if not u: return
    txt=""
    if c.data=="chg_form":
        u['formation']="4-3-3" if u.get('formation')!="4-3-3" else "3-5-2"
        txt=f"✅ ترکیب: {u['formation']}"
    elif c.data=="chg_tact":
        u['tactic']="هجومی" if u.get('tactic')!="هجومی" else "دفاعی"
        txt=f"✅ تاکتیک: {u['tactic']}"
    elif c.data=="sv_form":
        u['saved_form']=u.get('formation')
        txt="📥 چینش ذخیره شد"
    elif c.data=="ld_form":
        if 'saved_form' in u: 
            u['formation']=u['saved_form']
            txt="📤 چینش بارگذاری شد"
        else: txt="❗ چیزی ذخیره نشده!"
    else:
        txt=f"📊 آنالیز: امتیاز {u.get('points',0)}, سکه {u['coins']}, جم {u['gems']}"
    save_user(c.message.chat.id,u)
    bot.edit_message_text(txt, c.message.chat.id, c.message.message_id)
    bot.answer_callback_query(c.id)

def show_profile(m):
    u=get_user(m.chat.id)
    pl=u.get('players',[])
    txt=f"""📋 پروفایل:

🏷 {u['team_name']} | ⚽️ ترکیب: {u.get('formation')} | 🎯 تاکتیک: {u.get('tactic')}

💰 سکه: {u['coins']} | 💎 جم: {u['gems']} | ⚡️ امتیاز: {u.get('points')}

👥 بازیکنان:
"""
    for p in pl: txt+=f"• {p['name']} ({p['position']})\n"
    bot.send_message(m.chat.id,txt)

def transfer_market(m): pass
def league_table(m): pass

@app.route(f'/{TOKEN}',methods=['POST'])
def w():bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode())]);return'ok'
@app.route('/')
def i():return'up'

def sim(): pass

if __name__=='__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"https://your-app.onrender.com/{TOKEN}")
    threading.Thread(target=lambda:(schedule.every().day.at("21:00").do(sim),[schedule.run_pending() or time.sleep(10)]),daemon=True).start()
    app.run(host="0.0.0.0",port=10000)
