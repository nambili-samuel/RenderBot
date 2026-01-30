import os
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==============================
# CONFIG
# ==============================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = os.getenv("WEBHOOK_URL")  # https://renderbot-x64y.onrender.com
PORT = int(os.getenv("PORT", "10000"))

if not TOKEN or not BASE_URL:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or WEBHOOK_URL")

WEBHOOK_PATH = "webhook"
WEBHOOK_URL = f"{BASE_URL}/{WEBHOOK_PATH}"

# ==============================
# LOGGING
# ==============================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ==============================
# HANDLERS
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I’m alive and running on Render via webhook 🚀"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Menu coming soon!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🧠 You said:\n{update.message.text}"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Button clicked!")

# ==============================
# MAIN
# ==============================
def main():
    logger.info("🚀 Starting bot in WEBHOOK mode")
    logger.info(f"🌐 Webhook URL: {WEBHOOK_URL}")

    app = Application.builder().token(TOKEN).build()

    # Order matters
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button_handler))

    # IMPORTANT: do NOT catch commands here
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
