import telebot

TOKEN = "7721577419:AAGF6eX2kt5sD4FADDNNIuY0WJE7wBrnhFc"
bot = telebot.TeleBot(TOKEN)

bot.remove_webhook()
print("✅ Webhook حذف شد")
