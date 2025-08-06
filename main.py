import json
import os
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    filters, CallbackContext
)

TOKEN = os.getenv("TOKEN")  # Setează tokenul din variabilele de mediu pe Render

WARNS_FILE = "warns.json"

# ====== UTILITARE ======
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

# ====== COMENZI ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Botul este activ!")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    warns = load_warns()
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None

    if not user:
        await update.message.reply_text("Trebuie să răspunzi la mesajul utilizatorului pe care vrei să-l avertizezi.")
        return

    reason = " ".join(context.args) if context.args else "Nespecificat"
    warns.setdefault(str(user.id), []).append({
        "date": datetime.utcnow().isoformat(),
        "reason": reason
    })
    save_warns(warns)

    count = len(warns[str(user.id)])
    await update.message.reply_text(
        f"⚠️ Avertisment #{count} pentru {update.message.reply_to_message.from_user.mention_html()}.",
        parse_mode="HTML"
    )

async def warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    warns = load_warns()
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None

    if not user:
        await update.message.reply_text("Trebuie să răspunzi la mesajul utilizatorului.")
        return

    user_warns = warns.get(str(user.id), [])
    if not user_warns:
        await update.message.reply_text("Acest utilizator nu are avertismente.")
    else:
        text = "\n".join([f"{i+1}. {w['reason']} - {w['date']}" for i, w in enumerate(user_warns)])
        await update.message.reply_text(f"Avertismente pentru {user.mention_html()}:\n{text}", parse_mode="HTML")

# ====== PORNIRE BOT ======
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("warn", warn))
    application.add_handler(CommandHandler("warns", warns))

    application.run_polling()

if __name__ == "__main__":
    main()
