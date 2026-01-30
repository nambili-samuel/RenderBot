import os
import logging
import random
import re
import asyncio
import time
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TimedOut, NetworkError
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from database import Database
from knowledge_base import KnowledgeBase

# =========================================================
# CONFIGURATION
# =========================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-app.onrender.com
PORT = int(os.getenv("PORT", 10000))

if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("❌ TELEGRAM_BOT_TOKEN or WEBHOOK_URL not set")

ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = set(map(int, ADMIN_IDS_STR.split(","))) if ADMIN_IDS_STR else set()

# =========================================================
# LOGGING
# =========================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================================================
# BOT CORE
# =========================================================
class EvaGeisesBot:
    def __init__(self):
        self.db = Database()
        self.kb = KnowledgeBase()
        self.last_activity = {}
        self.welcomed_users = set()
        self.last_greeting = {}
        self.last_property_post = {}

    def get_greeting(self):
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 21:
            return "Good evening"
        return "Hello"

    def is_chat_quiet(self, chat_id, minutes=20):
        last = self.last_activity.get(str(chat_id))
        return not last or datetime.now() - last > timedelta(minutes=minutes)

    def should_send_greeting(self, chat_id):
        now = datetime.now()
        last = self.last_greeting.get(chat_id)
        if not last or now - last > timedelta(hours=2):
            self.last_greeting[chat_id] = now
            return True
        return False

    def analyze_message(self, message, user_id, chat_id):
        msg = message.lower().strip()
        self.last_activity[str(chat_id)] = datetime.now()

        if "namibia" in msg or "eva" in msg or "?" in msg:
            return True, "search"
        return False, None

    def generate_response(self, message, response_type):
        results = self.kb.search(message, limit=1)
        if results:
            r = results[0]
            return f"🇳🇦 *{r['topic']}*\n\n{r['content']}\n\n📱 Use /menu for more!"
        return "🤔 Ask me anything about Namibia or use /menu!"

    def generate_welcome(self, name):
        return f"👋 Welcome {name}! I’m Eva, your Namibia expert 🇳🇦\n\nUse /menu to explore!"

# =========================================================
# MENU
# =========================================================
class InteractiveMenu:
    def __init__(self, kb):
        self.kb = kb

    def main_menu(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Real Estate", callback_data="cat_Real Estate")],
            [InlineKeyboardButton("🏞️ Tourism", callback_data="cat_Tourism")],
            [InlineKeyboardButton("🦁 Wildlife", callback_data="cat_Wildlife")],
            [InlineKeyboardButton("ℹ️ Info", callback_data="cat_Practical")],
        ])

eva = EvaGeisesBot()
menu = InteractiveMenu(eva.kb)

# =========================================================
# HANDLERS
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    eva.db.add_user(user.id, user.username or "Unknown")
    await update.message.reply_text(
        f"👋 {eva.get_greeting()} {user.first_name}!\n\n🇳🇦 I’m Eva. Ask me about Namibia or use /menu!",
        parse_mode="Markdown"
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Choose a topic:*",
        parse_mode="Markdown",
        reply_markup=menu.main_menu()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    msg = update.message.text

    eva.db.add_user(user_id, update.effective_user.username or "Unknown")
    eva.db.log_query(user_id, msg)

    should, kind = eva.analyze_message(msg, user_id, chat_id)
    if should:
        reply = eva.generate_response(msg, kind)
        await update.message.reply_text(reply, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📚 Use /menu or ask me a question about Namibia 🇳🇦",
        parse_mode="Markdown"
    )

# =========================================================
# MAIN (WEBHOOK MODE)
# =========================================================
def main():
    logger.info("🚀 Starting Eva Geises in WEBHOOK mode")

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(20)
        .read_timeout(20)
        .write_timeout(20)
        .build()
    )

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    logger.info(f"🌐 Webhook URL: {WEBHOOK_URL}/webhook")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=f"{WEBHOOK_URL}/webhook",
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
