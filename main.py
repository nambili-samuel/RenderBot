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
from health_server import run_health_server_background

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================================================
# CONFIGURATION
# =========================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN not set")
    exit(1)

ADMIN_IDS_STR = os.environ.get("ADMIN_IDS", "")
ADMIN_IDS = set(map(int, ADMIN_IDS_STR.split(','))) if ADMIN_IDS_STR else set()

# Webhook configuration
WEBHOOK_URL = "https://renderbot-x64y.onrender.com/webhook"
PORT = int(os.environ.get("PORT", "10000"))

# =========================================================
# EVA GEISES - NAMIBIA BOT ENGINE WITH REAL ESTATE
# =========================================================
class EvaGeisesBot:
    def __init__(self):
        self.db = Database()
        self.kb = KnowledgeBase()
        self.last_activity = {}
        self.welcomed_users = set()
        self.last_greeting = {}
        self.last_property_post = {}
        logger.info(f"🇳🇦 Eva Geises initialized with {len(self.kb.get_all_topics())} topics")
    
    def get_greeting(self):
        """Get time-appropriate greeting"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 21:
            return "Good evening"
        else:
            return "Hello"
    
    def analyze_message(self, message, user_id, chat_id):
        """Analyze if Eva should respond"""
        msg = message.lower().strip()
        self.last_activity[str(chat_id)] = datetime.now()
        
        response_types = []
        
        # 1. Direct mentions - 100%
        bot_mentions = ["@eva", "eva", "@namibiabot", "namibia bot", "hey bot", "hello bot", "hey eva"]
        if any(mention in msg for mention in bot_mentions):
            response_types.append(("search", 100))
        
        # 2. Questions - 90%
        question_words = ["what", "how", "where", "when", "why", "who", "which", 
                         "can you", "tell me", "explain", "show me", "is", "are", "do", "does"]
        if "?" in msg or any(msg.startswith(w) for w in question_words):
            response_types.append(("search", 90))
        
        # 3. Greetings - 80%
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", 
                    "moro", "greetings", "hallo", "howzit"]
        if any(g in msg.split() for g in greetings):
            response_types.append(("greeting", 80))
        
        # 4. Namibia mentions - 85%
        if "namibia" in msg or "namibian" in msg:
            response_types.append(("search", 85))
        
        # 5. Real estate keywords - 95%
        real_estate_keywords = ["house", "property", "land", "plot", "sale", "buy", 
                               "real estate", "windhoek west", "omuthiya", "okahandja",
                               "bedroom", "bedroomed", "rent", "invest"]
        if any(keyword in msg for keyword in real_estate_keywords):
            response_types.append(("search", 95))
        
        # 6. Specific topics - 90%
        topics = ["etosha", "sossusvlei", "swakopmund", "windhoek", "himba", "herero", 
                 "desert", "dunes", "fish river", "cheetah", "elephant", "lion", "wildlife",
                 "safari", "namib", "capital", "visa", "currency", "weather"]
        if any(t in msg for t in topics):
            response_types.append(("search", 90))
        
        # 7. Travel keywords - 80%
        travel = ["travel", "tour", "visit", "trip", "vacation", "holiday", 
                 "destination", "tourist", "booking"]
        if any(w in msg for w in travel):
            response_types.append(("search", 80))
        
        # 8. Quiet chat - 30%
        if self.is_chat_quiet(chat_id, minutes=20):
            response_types.append(("conversation_starter", 30))
        
        if response_types:
            response_types.sort(key=lambda x: x[1], reverse=True)
            top = response_types[0]
            if random.random() < (top[1] / 100):
                return True, top[0]
        
        return False, None
    
    def is_chat_quiet(self, chat_id, minutes=20):
        """Check if chat quiet"""
        chat_id_str = str(chat_id)
        if chat_id_str not in self.last_activity:
            return True
        return datetime.now() - self.last_activity[chat_id_str] > timedelta(minutes=minutes)
    
    def should_send_greeting(self, chat_id):
        """Check if should send periodic greeting (every 2 hours)"""
        chat_id_str = str(chat_id)
        now = datetime.now()
        
        if chat_id_str not in self.last_greeting:
            self.last_greeting[chat_id_str] = now
            return True
        
        if now - self.last_greeting[chat_id_str] > timedelta(hours=2):
            self.last_greeting[chat_id_str] = now
            return True
        
        return False
    
    def get_periodic_greeting(self):
        """Get varied time-based greetings"""
        hour = datetime.now().hour
        
        if 5 <= hour < 8:
            greetings = [
                "🌅 *Rise and shine, Namibia lovers!*\n\nWhat's everyone up to today?\n\n📱 Check /menu for Namibia info!",
                "☀️ *Early morning vibes!*\n\nAnyone planning a Namibia adventure?\n\n💡 Use /menu to explore!",
                "🌄 *Good morning, everyone!*\n\nWhat aspect of Namibia interests you most?\n\n📚 Try /menu!"
            ]
        elif 8 <= hour < 12:
            greetings = [
                "☕ *Good morning, Namibia enthusiasts!*\n\nWhat brings you here today?\n\n📱 Use /menu to discover!",
                "🌞 *Morning everyone!*\n\nReady to learn something amazing about Namibia?\n\n💡 Check /menu!",
                "👋 *Good morning!*\n\nAsk me anything about Namibia or use /menu! 🇳🇦"
            ]
        elif 12 <= hour < 17:
            greetings = [
                "🌤️ *Good afternoon, everyone!*\n\nWhat Namibia topic shall we explore?\n\n📱 Use /menu!",
                "☀️ *Afternoon vibes!*\n\nAnyone curious about Namibia wildlife?\n\n🦁 Try /menu → Wildlife!",
                "👋 *Good afternoon!*\n\nI'm here to answer Namibia questions! 🇳🇦\n\n💡 /menu for topics!"
            ]
        elif 17 <= hour < 21:
            greetings = [
                "🌆 *Good evening, Namibia fans!*\n\nHow's everyone doing?\n\n📱 Use /menu to explore!",
                "🌅 *Evening everyone!*\n\nPerfect time to learn about Namibia!\n\n💡 Check /menu!",
                "👋 *Good evening!*\n\nReady for some Namibia facts? 🇳🇦\n\n📚 Try /menu!"
            ]
        else:
            greetings = [
                "🌙 *Good evening, night owls!*\n\nWhat Namibia topic interests you?\n\n📱 Use /menu!",
                "✨ *Hello everyone!*\n\nI'm here if you need Namibia info! 🇳🇦\n\n💡 Try /menu!",
                "🌟 *Evening, travelers!*\n\nAsk me about Namibia anytime!\n\n📚 Use /menu!"
            ]
        
        return random.choice(greetings)
    
    def generate_response(self, message, response_type):
        """Generate Eva's response"""
        clean_msg = re.sub(r'@[^\s]*', '', message.lower()).strip()
        clean_msg = re.sub(r'(hey|hello|hi)\s+(eva|bot|namibia)', '', clean_msg).strip()
        
        # Search knowledge base
        if response_type == "search" and clean_msg:
            results = self.kb.search(clean_msg, limit=3)
            
            if results:
                best = results[0]
                
                response = f"🤔 *Based on your question:*\n\n"
                response += f"**{best['topic']}**\n"
                response += f"{best['content']}\n\n"
                
                # Add related topics
                if len(results) > 1:
                    response += "📚 *Related topics:*\n"
                    for i, res in enumerate(results[1:3], 1):
                        response += f"{i}. {res['topic']}\n"
                    response += "\n"
                
                response += "💡 Ask me more or use /menu to explore!"
                return response
            else:
                return f"🤔 *Interesting question about:* \"{clean_msg}\"\n\nI don't have info on that yet, but I'm learning! 📚\n\nMeanwhile, explore /menu to see what I know! 🇳🇦"
        
        # Greeting response
        elif response_type == "greeting":
            greeting = self.get_greeting()
            responses = [
                f"{greeting}! 👋 I'm Eva, your Namibia guide! 🇳🇦\n\nWhat interests you? Tourism? Wildlife? Real Estate?\n\nUse /menu to explore! 📱",
                f"{greeting}! 🌟 Ready to discover Namibia?\n\nI can help with:\n• Tourism & Safari\n• Wildlife & Nature\n• Real Estate Opportunities\n• Culture & History\n\nJust ask or use /menu! 🗺️",
                f"{greeting}! ✨ I'm Eva, here to share Namibia's wonders!\n\nAsk anything or browse /menu for topics! 🦁"
            ]
            return random.choice(responses)
        
        # Conversation starter
        elif response_type == "conversation_starter":
            starters = [
                "🌅 *Did you know?*\n\nNamibia has one of the oldest deserts in the world - the Namib Desert!\n\nWhat would you like to learn about Namibia? Use /menu! 🏜️",
                "🦒 *Fascinating fact!*\n\nEtosha National Park hosts over 100 mammal species!\n\nCurious about Namibia wildlife? Check /menu! 🦁",
                "🏠 *Real Estate Highlight*\n\nNamibia offers great property investment opportunities!\n\nInterested? Use /properties or /menu! 🏘️",
                "🌍 *Travel Tip*\n\nNamibia is known for its stunning landscapes and friendly people!\n\nPlan your visit - explore /menu for info! ✈️"
            ]
            return random.choice(starters)
        
        return None

# Initialize Eva instance
eva = EvaGeisesBot()

# Menu manager
class MenuManager:
    def __init__(self):
        self.categories = eva.kb.get_categories()
    
    def main_menu(self):
        """Create main menu"""
        keyboard = []
        
        # Category buttons (2 per row)
        row = []
        emoji_map = {
            "Real Estate": "🏠", "Tourism": "🏞️", "History": "📜",
            "Culture": "👥", "Practical": "ℹ️", "Wildlife": "🦁",
            "Facts": "🚀", "Geography": "🗺️"
        }
        
        for cat in self.categories:
            emoji = emoji_map.get(cat, "📌")
            row.append(InlineKeyboardButton(f"{emoji} {cat}", callback_data=f"cat_{cat}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        # Add Properties button
        keyboard.append([InlineKeyboardButton("🏘️ View Properties", callback_data="cat_Real Estate")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def create_submenu(self, category):
        """Create submenu with topics"""
        topics = eva.kb.get_by_category(category)
        keyboard = []
        
        # Add topic buttons (1 per row for readability)
        for i, topic in enumerate(topics[:10]):  # Show first 10 topics
            topic_name = topic['topic']
            # Truncate long names
            if len(topic_name) > 40:
                topic_name = topic_name[:37] + "..."
            
            keyboard.append([
                InlineKeyboardButton(
                    topic_name,
                    callback_data=f"topic_{category}_{i}"
                )
            ])
        
        # Back button
        keyboard.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu_back")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def back_button(self, category=None):
        """Create back button"""
        keyboard = []
        if category:
            keyboard.append([InlineKeyboardButton(f"⬅️ Back to {category}", callback_data=f"cat_{category}")])
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_back")])
        return InlineKeyboardMarkup(keyboard)
    
    def format_category(self, category):
        """Format category overview"""
        topics = eva.kb.get_by_category(category)
        
        emoji_map = {
            "Real Estate": "🏠", "Tourism": "🏞️", "History": "📜",
            "Culture": "👥", "Practical": "ℹ️", "Wildlife": "🦁",
            "Facts": "🚀", "Geography": "🗺️"
        }
        
        emoji = emoji_map.get(category, "📌")
        
        response = f"{emoji} *{category}*\n\n"
        response += f"I have {len(topics)} topics in this category.\n\n"
        response += "Select a topic below to learn more! 👇"
        
        return response

menu = MenuManager()

# =========================================================
# COMMAND HANDLERS
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user = update.effective_user
    chat = update.effective_chat
    
    eva.db.add_user(user.id, user.username, user.first_name)
    eva.db.add_chat(chat.id, chat.type, chat.title)
    
    welcome = f"🇳🇦 *Welcome to Eva Geises - Your Namibia Expert!*\n\n"
    welcome += f"Hello {user.first_name}! I'm Eva, and I can help you with:\n\n"
    welcome += "🏞️ Tourism & Safari Adventures\n"
    welcome += "🦁 Wildlife & Nature\n"
    welcome += "🏠 Real Estate Opportunities\n"
    welcome += "👥 Culture & History\n"
    welcome += "ℹ️ Practical Travel Info\n\n"
    welcome += "*Commands:*\n"
    welcome += "/menu - Browse all topics\n"
    welcome += "/properties - View real estate\n"
    welcome += "/topics - Quick topic search\n"
    welcome += "/help - Get help\n\n"
    welcome += "💬 Just ask me anything about Namibia!"
    
    await update.message.reply_text(welcome, parse_mode="Markdown")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu command"""
    await update.message.reply_text(
        "🇳🇦 *I am here to help learn Namibia*\n\nWhat would you like to explore?",
        parse_mode="Markdown",
        reply_markup=menu.main_menu()
    )

async def properties_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Properties command"""
    properties = eva.kb.get_by_category("Real Estate")
    
    if not properties:
        await update.message.reply_text("🏠 No properties available at the moment.")
        return
    
    response = "🏠 *Available Properties in Namibia*\n\n"
    
    for i, prop in enumerate(properties[:5], 1):
        response += f"*{i}. {prop['topic']}*\n"
        response += f"{prop['content'][:200]}...\n\n"
    
    response += "💡 Use /menu → Real Estate for full details!"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def topics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Topics command"""
    categories = eva.kb.get_categories()
    
    response = "📚 *Available Topics*\n\n"
    
    emoji_map = {
        "Real Estate": "🏠", "Tourism": "🏞️", "History": "📜",
        "Culture": "👥", "Practical": "ℹ️", "Wildlife": "🦁",
        "Facts": "🚀", "Geography": "🗺️"
    }
    
    for cat in categories:
        topics = eva.kb.get_by_category(cat)
        emoji = emoji_map.get(cat, "📌")
        response += f"{emoji} *{cat}:* {len(topics)} topics\n"
    
    response += "\n💡 Use /menu to explore topics!"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stats command (admin only)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only command")
        return
    
    stats = eva.db.get_stats()
    
    response = "📊 *Bot Statistics*\n\n"
    response += f"👥 Total Users: {stats['total_users']}\n"
    response += f"💬 Total Chats: {stats['total_chats']}\n"
    response += f"✅ Active Chats: {stats['active_chats']}\n"
    response += f"📚 Topics: {len(eva.kb.get_all_topics())}\n"
    response += f"📂 Categories: {len(eva.kb.get_categories())}\n"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    help_text = "🇳🇦 *Eva Geises - Help*\n\n"
    help_text += "*Commands:*\n"
    help_text += "/start - Start the bot\n"
    help_text += "/menu - Browse all topics\n"
    help_text += "/properties - View real estate listings\n"
    help_text += "/topics - See available topics\n"
    help_text += "/help - Show this help\n\n"
    help_text += "*How to use:*\n"
    help_text += "• Just ask me questions about Namibia!\n"
    help_text += "• Use /menu to browse topics\n"
    help_text += "• Mention 'Eva' or 'bot' in groups\n\n"
    help_text += "💬 I respond to questions, greetings, and Namibia-related keywords!"
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add topic command (admin only)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only command")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /add <category> <topic> <content>\n\n"
            "Example: /add Tourism \"Cape Cross\" \"Visit the seal colony...\""
        )
        return
    
    category = context.args[0]
    topic = context.args[1]
    content = " ".join(context.args[2:])
    
    eva.kb.add_topic(category, topic, content)
    
    await update.message.reply_text(f"✅ Added topic '{topic}' to {category}")

# =========================================================
# MESSAGE HANDLERS
# =========================================================
async def handle_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new members"""
    chat = update.effective_chat
    new_members = update.message.new_chat_members
    
    eva.db.add_chat(chat.id, chat.type, chat.title)
    
    for member in new_members:
        if member.id == context.bot.id:
            welcome = "🇳🇦 *Hello everyone! I'm Eva Geises!*\n\n"
            welcome += "I'm here to share knowledge about Namibia:\n\n"
            welcome += "🏞️ Tourism & Wildlife\n"
            welcome += "🏠 Real Estate\n"
            welcome += "👥 Culture & History\n"
            welcome += "ℹ️ Travel Information\n\n"
            welcome += "*How to use me:*\n"
            welcome += "• Ask questions about Namibia\n"
            welcome += "• Mention 'Eva' or 'bot'\n"
            welcome += "• Use /menu to browse topics\n\n"
            welcome += "💬 I'll respond to relevant messages automatically!"
            
            await update.message.reply_text(welcome, parse_mode="Markdown")
            break

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle group messages"""
    message = update.message
    user = update.effective_user
    chat = update.effective_chat
    
    eva.db.add_user(user.id, user.username, user.first_name)
    eva.db.add_chat(chat.id, chat.type, chat.title)
    
    # Analyze message
    should_respond, response_type = eva.analyze_message(message.text, user.id, chat.id)
    
    if should_respond:
        response = eva.generate_response(message.text, response_type)
        if response:
            await message.reply_text(response, parse_mode="Markdown")

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle private messages"""
    message = update.message
    user = update.effective_user
    
    eva.db.add_user(user.id, user.username, user.first_name)
    
    # Always respond in private chats
    should_respond, response_type = eva.analyze_message(message.text, user.id, user.id)
    
    if not should_respond:
        response_type = "search"
    
    response = eva.generate_response(message.text, response_type)
    if response:
        await message.reply_text(response, parse_mode="Markdown")
    else:
        await message.reply_text(
            "🤔 I'm not sure about that.\n\nTry /menu to explore topics or ask something else! 🇳🇦",
            parse_mode="Markdown"
        )

# =========================================================
# SCHEDULED JOBS
# =========================================================
async def post_daily_property(context: ContextTypes.DEFAULT_TYPE):
    """Post daily property to all active chats"""
    try:
        logger.info("🏠 Starting daily property post...")
        properties = eva.kb.get_by_category("Real Estate")
        
        if not properties:
            logger.info("📭 No properties available")
            return
        
        # Select random property
        property_data = random.choice(properties)
        
        # Format message
        message = "🏠 *Today's Featured Property*\n\n"
        message += f"**{property_data['topic']}**\n\n"
        message += f"{property_data['content']}\n\n"
        message += "💡 Interested? Contact us or use /properties for more listings!"
        
        # Send to all active chats
        active_chats = eva.db.get_active_chats()
        
        for chat in active_chats:
            chat_id = chat['chat_id']
            
            # Check if already posted today
            chat_id_str = str(chat_id)
            today = datetime.now().date()
            
            if chat_id_str in eva.last_property_post:
                if eva.last_property_post[chat_id_str].date() == today:
                    continue
            
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown"
                )
                eva.last_property_post[chat_id_str] = datetime.now()
                logger.info(f"✅ Property posted to chat {chat_id}")
                await asyncio.sleep(2)  # Avoid rate limiting
            except Exception as e:
                logger.error(f"❌ Failed to post to chat {chat_id}: {e}")
                # Deactivate chat if bot was removed
                if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                    eva.db.deactivate_chat(chat_id)
                    logger.info(f"🔇 Deactivated chat {chat_id}")
        
        logger.info("✅ Daily property posting complete")
    except Exception as e:
        logger.error(f"❌ Error in daily property post: {e}")

async def send_periodic_greetings(context: ContextTypes.DEFAULT_TYPE):
    """Send periodic greetings to active groups"""
    try:
        logger.info("👋 Starting periodic greetings...")
        active_chats = eva.db.get_active_chats()
        
        if not active_chats:
            logger.info("📭 No active chats for greetings")
            return
        
        for chat in active_chats:
            chat_id = chat['chat_id']
            
            # Check if this chat should receive greeting
            if eva.should_send_greeting(chat_id):
                greeting = eva.get_periodic_greeting()
                
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=greeting,
                        parse_mode="Markdown"
                    )
                    logger.info(f"✅ Greeting sent to chat {chat_id}")
                    await asyncio.sleep(2)  # Avoid rate limiting
                except Exception as e:
                    logger.error(f"❌ Failed to send greeting to chat {chat_id}: {e}")
                    # Deactivate chat if bot was removed
                    if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                        eva.db.deactivate_chat(chat_id)
                        logger.info(f"🔇 Deactivated chat {chat_id}")
        
        logger.info("✅ Periodic greetings complete")
    except Exception as e:
        logger.error(f"❌ Error in periodic greetings: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buttons"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Main menu
    if data == "menu_back":
        await query.edit_message_text(
            "🇳🇦 *I am here to help learn Namibia*\n\nWhat would you like to explore?",
            parse_mode="Markdown",
            reply_markup=menu.main_menu()
        )
    
    # Category selection - show submenu with topic buttons
    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        content = menu.format_category(category)
        
        await query.edit_message_text(
            content,
            parse_mode="Markdown",
            reply_markup=menu.create_submenu(category)
        )
    
    # Topic selection - show detailed information
    elif data.startswith("topic_"):
        # Parse: topic_Category_index
        parts = data.split("_")
        if len(parts) >= 3:
            category = "_".join(parts[1:-1])  # Handle "Real Estate" category
            try:
                topic_index = int(parts[-1])
            except:
                topic_index = 0
            
            topics = eva.kb.get_by_category(category)
            
            if topics and 0 <= topic_index < len(topics):
                topic = topics[topic_index]
                
                # Format detailed topic response
                emoji_map = {
                    "Real Estate": "🏠",
                    "Tourism": "🏞️", "History": "📜", "Culture": "👥",
                    "Practical": "ℹ️", "Wildlife": "🦁", "Facts": "🚀",
                    "Geography": "🗺️"
                }
                
                emoji = emoji_map.get(category, "📌")
                
                response = f"{emoji} *{topic['topic']}*\n\n"
                response += f"{topic['content']}\n\n"
                
                # Add keywords if available
                if topic.get('keywords'):
                    keywords = topic['keywords'].strip()
                    if keywords:
                        response += f"🏷️ *Keywords:* {keywords}\n\n"
                
                response += f"📂 *Category:* {category}\n\n"
                response += "💡 Ask me more questions or explore other topics!"
                
                await query.edit_message_text(
                    response,
                    parse_mode="Markdown",
                    reply_markup=menu.back_button(category)
                )
                return
        
        # Fallback if topic not found
        await query.edit_message_text(
            "❌ Topic not found. Please try another topic.",
            parse_mode="Markdown",
            reply_markup=menu.back_button()
        )

# =========================================================
# MAIN
# =========================================================
async def main():
    """Run Eva with webhook"""
    logger.info("=" * 60)
    logger.info("🇳🇦 EVA GEISES - NAMIBIA EXPERT & REAL ESTATE AGENT")
    logger.info("=" * 60)
    logger.info(f"✅ Topics: {len(eva.kb.get_all_topics())}")
    logger.info(f"✅ Categories: {len(eva.kb.get_categories())}")
    logger.info("=" * 60)
    
    # Start health check server for Render (prevents spin-down)
    run_health_server_background(port=PORT)
    logger.info(f"🏥 Health server started on port {PORT}")
    
    # Build application
    app = Application.builder() \
        .token(TELEGRAM_BOT_TOKEN) \
        .connect_timeout(15) \
        .read_timeout(10) \
        .write_timeout(10) \
        .build()
    
    # Add handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('menu', menu_command))
    app.add_handler(CommandHandler('properties', properties_command))
    app.add_handler(CommandHandler('topics', topics_command))
    app.add_handler(CommandHandler('stats', stats_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('add', add_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_members))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_group_message))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_private_message))
    
    # Schedule daily property posts (at 10 AM every day)
    job_queue = app.job_queue
    job_queue.run_daily(
        post_daily_property,
        time=datetime.strptime("10:00", "%H:%M").time(),
        name="daily_property_post"
    )
    
    # Schedule periodic greetings (every 2 hours)
    job_queue.run_repeating(
        send_periodic_greetings,
        interval=7200,  # 2 hours in seconds
        first=300,  # Start after 5 minutes
        name="periodic_greetings"
    )
    
    logger.info("🚀 Eva is running with webhook mode...")
    logger.info(f"🔗 Webhook URL: {WEBHOOK_URL}")
    logger.info("📅 Daily property posts at 10:00 AM")
    logger.info("👋 Periodic greetings every 2 hours")
    
    # Set webhook
    await app.bot.set_webhook(
        url=WEBHOOK_URL,
        drop_pending_updates=True
    )
    
    # Run webhook on the same port as health server
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    asyncio.run(main())
