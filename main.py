import json
import os
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
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
    for user_id in list(warns.keys()):
        warns[user_id] = [w for w in warns[user_id] if datetime.fromisoformat(w["date"]) + timedelta(days=30) > now]
        if not warns[user_id]:
            del warns[user_id]
    return warns

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Sunt activ.")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Scrie motivul avertismentului.")
        return

    reason = ' '.join(context.args)
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.message.from_user
    warns = load_warns()
    user_id = str(user.id)

    warns.setdefault(user_id, []).append({"reason": reason, "date": datetime.utcnow().isoformat()})
    save_warns(warns)

    await update.message.reply_text(f"Avertisment pentru {user.mention_html()}.
Motiv: {reason}", parse_mode="HTML")

async def warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.message.from_user
    warns = load_warns()
    warns = cleanup_warns(warns)
    save_warns(warns)
    user_id = str(user.id)

    if user_id not in warns:
        await update.message.reply_text("Acest utilizator nu are avertismente.")
    else:
        warns_list = warns[user_id]
        text = f"{user.mention_html()} are {len(warns_list)} avertismente:
"
        for i, warn in enumerate(warns_list, start=1):
            text += f"{i}. {warn['reason']} (data: {warn['date']})
"
        await update.message.reply_text(text, parse_mode="HTML")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("warn", warn))
    application.add_handler(CommandHandler("warns", warns))
    application.run_polling()

if __name__ == "__main__":
    main()