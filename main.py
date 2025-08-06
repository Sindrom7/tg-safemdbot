
import os
import json
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

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
    for user_id in list(warns):
        warns[user_id] = [w for w in warns[user_id] if datetime.fromisoformat(w["date"]) + timedelta(days=30) > now]
        if not warns[user_id]:
            del warns[user_id]
    return warns

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Botul este activ!")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Folosește comanda ca reply la mesajul utilizatorului.")
        return

    reason = " ".join(context.args) if context.args else "Nespecificat"
    user_id = str(update.message.reply_to_message.from_user.id)

    warns = load_warns()
    warns.setdefault(user_id, [])
    warns[user_id].append({"date": datetime.utcnow().isoformat(), "reason": reason})
    warns = cleanup_warns(warns)
    save_warns(warns)

    count = len(warns[user_id])
    await update.message.reply_text(f'⚠️ Avertisment #{count} pentru {update.message.reply_to_message.from_user.mention_html()}.
Motiv: {reason}", parse_mode="HTML")

    if count >= 3:
        await update.message.reply_text(f"{update.message.reply_to_message.from_user.mention_html()} a primit 3 avertismente și va fi banat.", parse_mode="HTML")
        await context.bot.ban_chat_member(update.effective_chat.id, update.message.reply_to_message.from_user.id)

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Folosește comanda ca reply la mesajul utilizatorului.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Specifică numărul de minute pentru mute.")
        return

    try:
        minutes = int(context.args[0])
        until_date = datetime.utcnow() + timedelta(minutes=minutes)
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            update.message.reply_to_message.from_user.id,
            ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await update.message.reply_text(f"🔇 Utilizatorul a fost blocat pentru {minutes} minute.")
    except ValueError:
        await update.message.reply_text("Valoare invalidă pentru minute.")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("warn", warn))
    application.add_handler(CommandHandler("mute", mute))
    application.run_polling()

if __name__ == "__main__":
    main()
