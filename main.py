import os
import json
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("TOKEN")
WARNS_FILE = "warns.json"

def load_warns():
    if not os.path.exists(WARNS_FILE):
        return {}
    with open(WARNS_FILE, "r") as f:
        return json.load(f)

def save_warns(warns):
    with open(WARNS_FILE, "w") as f:
        json.dump(warns, f)

def cleanup_warns(warns):
    now = datetime.utcnow()
    for user_id in list(warns.keys()):
        warns[user_id] = [w for w in warns[user_id] if datetime.fromisoformat(w["date"]) + timedelta(days=30) > now]
        if not warns[user_id]:
            del warns[user_id]
    return warns

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Trebuie să dai reply la un mesaj ca să avertizezi!")
        return

    warns = load_warns()
    user_id = str(update.message.reply_to_message.from_user.id)
    reason = " ".join(context.args) if context.args else "Fără motiv"

    if user_id not in warns:
        warns[user_id] = []

    warns[user_id].append({"date": datetime.utcnow().isoformat(), "reason": reason})
    warns = cleanup_warns(warns)
    save_warns(warns)

    count = len(warns[user_id])
 await update.message.reply_text(
    f"⚠️ Avertisment #{count} pentru {update.message.reply_to_message.from_user.mention_html()}.",
    parse_mode="HTML"
)

    if count >= 3:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, update.message.reply_to_message.from_user.id)
            await update.message.reply_text("🚫 Utilizatorul a fost banat deoarece a primit 3 avertismente.")
        except Exception as e:
            await update.message.reply_text(f"❌ Eroare la banare: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Botul este online. Folosește /warn ca să avertizezi un utilizator.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("warn", warn))
    app.run_polling()

if __name__ == "__main__":
    main()
