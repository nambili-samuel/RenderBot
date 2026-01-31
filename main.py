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
from smart_features import SmartFeatures

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
# EVA GEISES - NAMIBIA BOT ENGINE WITH FULL GROUP MANAGEMENT
# =========================================================
class EvaGeisesBot:
    def __init__(self):
        self.db = Database()
        self.kb = KnowledgeBase()
        self.smart = SmartFeatures()
        self.last_activity = {}
        self.welcomed_users = set()
        self.last_greeting = {}
        self.last_property_post = {}
        self.property_rotation_index = 0
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
        """Analyze if Eva should respond - IMPROVED INTELLIGENCE"""
        msg = message.lower().strip()
        self.last_activity[str(chat_id)] = datetime.now()
        
        response_types = []
        
        # 1. Direct mentions - 100%
        bot_mentions = ["@eva", "eva", "@namibiabot", "namibia bot", "hey bot", "hello bot", "hey eva"]
        if any(mention in msg for mention in bot_mentions):
            response_types.append(("search", 100))
        
        # 2. Questions with ? - 100% (FIXED - was not responding)
        if "?" in msg:
            response_types.append(("search", 100))
        
        # 3. Questions without ? - 95%
        question_words = ["what", "how", "where", "when", "why", "who", "which", 
                         "can you", "tell me", "explain", "show me", "is", "are", "do", "does",
                         "could you", "would you", "should", "will", "give me"]
        if any(msg.startswith(w) for w in question_words):
            response_types.append(("search", 95))
        
        # 4. Greetings - 95% (IMPROVED - respond more often)
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", 
                    "moro", "greetings", "hallo", "howzit", "morning", "afternoon", "evening",
                    "sup", "yo", "heya"]
        # Check if greeting is at start or is standalone
        msg_words = msg.split()
        if len(msg_words) <= 3 and any(g in msg_words for g in greetings):
            # Short message with greeting = definitely a greeting
            response_types.append(("greeting", 95))
        elif any(g in msg_words[:2] for g in greetings):
            # Greeting in first 2 words
            response_types.append(("greeting", 90))
        
        # 5. Namibia mentions - 90%
        if "namibia" in msg or "namibian" in msg or "namibians" in msg:
            response_types.append(("search", 90))
        
        # 6. Real estate keywords - 95%
        real_estate_keywords = ["house", "property", "land", "plot", "sale", "buy", 
                               "real estate", "windhoek west", "omuthiya", "okahandja",
                               "bedroom", "bedroomed", "rent", "invest", "price"]
        if any(keyword in msg for keyword in real_estate_keywords):
            response_types.append(("search", 95))
        
        # 7. Specific topics - 90%
        topics = ["etosha", "sossusvlei", "swakopmund", "windhoek", "himba", "herero", 
                 "desert", "dunes", "fish river", "cheetah", "elephant", "lion", "wildlife",
                 "safari", "namib", "capital", "visa", "currency", "weather", "kalahari",
                 "skeleton coast", "caprivi", "walvis bay"]
        if any(t in msg for t in topics):
            response_types.append(("search", 90))
        
        # 8. Travel keywords - 85%
        travel = ["travel", "tour", "visit", "trip", "vacation", "holiday", 
                 "destination", "tourist", "booking", "accommodation"]
        if any(w in msg for w in travel):
            response_types.append(("search", 85))
        
        # 9. Informational requests - 85%
        info_keywords = ["information", "info", "details", "learn", "know", "find out",
                        "interested", "curious", "wondering"]
        if any(k in msg for k in info_keywords):
            response_types.append(("search", 85))
        
        # 10. Quiet chat - 30%
        if self.is_chat_quiet(chat_id, minutes=20):
            response_types.append(("conversation_starter", 30))
        
        if response_types:
            response_types.sort(key=lambda x: x[1], reverse=True)
            top = response_types[0]
            # Always respond to high-priority triggers (80%+) - INCLUDES GREETINGS
            if top[1] >= 80 or random.random() < (top[1] / 100):
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
        return self.smart.get_time_based_greeting()
    
    def get_property_posts(self):
        """Get all real estate properties"""
        properties = self.kb.get_by_category("Real Estate")
        return properties if properties else []
    
    def get_next_property(self):
        """Get next property in rotation"""
        properties = self.get_property_posts()
        if not properties:
            return None
        
        property = properties[self.property_rotation_index % len(properties)]
        self.property_rotation_index += 1
        return property
    
    def generate_response(self, message, response_type):
        """Generate Eva's response - IMPROVED INTELLIGENCE"""
        # BETTER QUERY CLEANING
        clean_msg = message.lower().strip()
        
        # Remove question marks and punctuation
        clean_msg = re.sub(r'[?!.,;:]+', ' ', clean_msg)
        
        # Remove bot mentions
        clean_msg = re.sub(r'@[^\s]*', '', clean_msg)
        
        # Remove common phrases that don't help search
        phrases_to_remove = [
            r'(hey|hello|hi)\s+(eva|bot|namibia\s*bot)',
            r'tell me about',
            r'can you tell me',
            r'i want to know',
            r'could you',
            r'would you',
            r'please'
        ]
        for phrase in phrases_to_remove:
            clean_msg = re.sub(phrase, '', clean_msg)
        
        clean_msg = clean_msg.strip()
        
        # Search knowledge base
        if response_type == "search" and clean_msg:
            results = self.kb.search(clean_msg, limit=5)
            
            if results:
                best = results[0]
                
                # More natural response introduction
                response = f"🤔 *About: {best['topic']}*\n\n"
                response += f"{best['content']}\n\n"
                
                # Show related topics if available
                if len(results) > 1:
                    response += "💡 *Related topics:*\n"
                    for i, r in enumerate(results[1:3], 1):  # Show max 2 related
                        response += f"{i}. {r['topic']}\n"
                    response += "\n"
                
                response += "ℹ️ Use /menu for more topics or ask another question!"
                return response
            else:
                # Better fallback when no results
                return (
                    "🤔 I don't have specific information about that in my knowledge base.\n\n"
                    "💡 *You can:*\n"
                    "• /menu - Browse all Namibia topics\n"
                    "• /properties - View real estate listings\n"
                    "• /topics - See all available topics\n\n"
                    "Try asking about: tourism, wildlife, culture, geography, or properties!"
                )
        
        elif response_type == "greeting":
            greeting = self.get_greeting()
            return (
                f"{greeting}! 👋\n\n"
                f"I'm Eva Geises, your Namibia expert! 🇳🇦\n\n"
                f"Ask me about tourism, wildlife, culture, real estate, or anything Namibia-related!\n\n"
                f"💡 Quick start: /menu"
            )
        
        elif response_type == "conversation_starter":
            return self.smart.get_engagement_prompt()
        
        return None

# Initialize bot
eva = EvaGeisesBot()

# =========================================================
# MENU SYSTEM
# =========================================================
class MenuSystem:
    def __init__(self, kb):
        self.kb = kb
    
    def main_menu(self):
        """Create main menu with categories"""
        keyboard = [
            [InlineKeyboardButton("🏠 Real Estate", callback_data="cat_Real Estate")],
            [InlineKeyboardButton("🏞️ Tourism", callback_data="cat_Tourism")],
            [InlineKeyboardButton("🦁 Wildlife", callback_data="cat_Wildlife")],
            [InlineKeyboardButton("👥 Culture", callback_data="cat_Culture")],
            [InlineKeyboardButton("📜 History", callback_data="cat_History")],
            [InlineKeyboardButton("🗺️ Geography", callback_data="cat_Geography")],
            [InlineKeyboardButton("ℹ️ Practical Info", callback_data="cat_Practical")],
            [InlineKeyboardButton("🚀 Fun Facts", callback_data="cat_Facts")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_submenu(self, category):
        """Create submenu with topics"""
        topics = self.kb.get_by_category(category)
        keyboard = []
        
        for i, topic in enumerate(topics[:8]):
            topic_name = topic['topic']
            if len(topic_name) > 35:
                topic_name = topic_name[:32] + "..."
            keyboard.append([InlineKeyboardButton(
                topic_name, 
                callback_data=f"topic_{category}_{i}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_back")])
        return InlineKeyboardMarkup(keyboard)
    
    def back_button(self, category=None):
        """Create back button"""
        if category:
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=f"cat_{category}")]]
        else:
            keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_back")]]
        return InlineKeyboardMarkup(keyboard)
    
    def format_category(self, category):
        """Format category overview"""
        topics = self.kb.get_by_category(category)
        
        emoji_map = {
            "Real Estate": "🏠",
            "Tourism": "🏞️",
            "History": "📜",
            "Culture": "👥",
            "Practical": "ℹ️",
            "Wildlife": "🦁",
            "Facts": "🚀",
            "Geography": "🗺️"
        }
        
        emoji = emoji_map.get(category, "📌")
        
        response = f"{emoji} *{category}*\n\n"
        response += f"📚 {len(topics)} topics available\n\n"
        response += "Select a topic below to learn more:"
        
        return response

menu = MenuSystem(eva.kb)

# =========================================================
# COMMAND HANDLERS
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    user = update.effective_user
    chat_type = update.effective_chat.type
    
    # Track user
    eva.db.add_user(user.id, user.username, user.first_name)
    
    if chat_type == "private":
        welcome = (
            f"🇳🇦 *Welcome {user.first_name}!*\n\n"
            f"I'm *Eva Geises*, your AI guide to Namibia!\n\n"
            f"🦁 *What I can help with:*\n"
            f"• Tourism & Safari information\n"
            f"• Wildlife & Nature\n"
            f"• Culture & History\n"
            f"• Real Estate listings\n"
            f"• Practical travel info\n\n"
            f"💡 *Quick Start:*\n"
            f"/menu - Browse all topics\n"
            f"/properties - View real estate\n"
            f"/help - Get help\n\n"
            f"Just ask me anything about Namibia! 🌟"
        )
    else:
        # Track group chat
        eva.db.track_chat(update.effective_chat.id, chat_type, update.effective_chat.title)
        welcome = (
            f"🇳🇦 *Hello everyone!*\n\n"
            f"I'm Eva Geises, ready to help with Namibia questions!\n\n"
            f"💡 Use /menu or just ask me anything!"
        )
    
    await update.message.reply_text(welcome, parse_mode="Markdown")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    await update.message.reply_text(
        "🇳🇦 *Explore Namibia*\n\nWhat would you like to learn about?",
        parse_mode="Markdown",
        reply_markup=menu.main_menu()
    )

async def properties_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show real estate properties"""
    properties = eva.get_property_posts()
    
    if not properties:
        await update.message.reply_text(
            "🏠 No properties currently listed.\n\nCheck back soon!"
        )
        return
    
    response = "🏠 *Available Properties in Namibia*\n\n"
    
    for i, prop in enumerate(properties, 1):
        response += f"*{i}. {prop['topic']}*\n"
        response += f"{prop['content']}\n\n"
        response += "─" * 30 + "\n\n"
    
    response += "💡 For more information, contact the agent listed in each property!"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def topics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all topics by category"""
    categories = eva.kb.get_categories()
    
    response = "📚 *All Topics by Category*\n\n"
    
    for category in sorted(categories):
        topics = eva.kb.get_by_category(category)
        response += f"*{category}* ({len(topics)})\n"
        for topic in topics[:3]:
            response += f"  • {topic['topic']}\n"
        if len(topics) > 3:
            response += f"  ... and {len(topics) - 3} more\n"
        response += "\n"
    
    response += "💡 Use /menu to explore topics interactively!"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics - Admin only"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🔒 This command is only available to administrators.")
        return
    
    user_stats = eva.db.get_user_stats(update.effective_user.id)
    total_users = len(eva.db.get_all_users())
    total_queries = eva.db.get_total_queries()
    active_chats = eva.db.get_active_chats()
    
    response = f"📊 *Bot Statistics*\n\n"
    response += f"👥 Total Users: {total_users}\n"
    response += f"💬 Total Queries: {total_queries}\n"
    response += f"🏘️ Active Groups: {len(active_chats)}\n"
    response += f"📚 Knowledge Topics: {len(eva.kb.get_all_topics())}\n\n"
    response += f"*Your Stats:*\n"
    response += f"Queries: {user_stats['query_count']}\n"
    response += f"Member since: {user_stats['joined_date'][:10] if user_stats['joined_date'] else 'Unknown'}"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    help_text = (
        "🇳🇦 *Eva Geises - Help Guide*\n\n"
        "*Commands:*\n"
        "/menu - Browse topics by category\n"
        "/properties - View real estate listings\n"
        "/topics - List all topics\n"
        "/help - Show this help\n\n"
        "*How to use:*\n"
        "• Ask questions naturally\n"
        "• Mention topics like 'Etosha', 'Sossusvlei'\n"
        "• Use /menu for organized browsing\n\n"
        "*Examples:*\n"
        "• \"What is the best time to visit Namibia?\"\n"
        "• \"Tell me about Etosha\"\n"
        "• \"Show me available properties\"\n\n"
        "Need more help? Just ask! 😊"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add knowledge - Admin only"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🔒 This command is only available to administrators.")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /add <category> <topic> <content>\n\n"
            "Example:\n/add Tourism \"Skeleton Coast\" \"The Skeleton Coast is...\""
        )
        return
    
    category = context.args[0]
    topic = context.args[1]
    content = ' '.join(context.args[2:])
    
    eva.kb.add_knowledge(topic, content, category)
    
    await update.message.reply_text(
        f"✅ Added '{topic}' to {category} category!"
    )

# =========================================================
# MESSAGE HANDLERS
# =========================================================
async def handle_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new group members"""
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        
        # Track chat
        eva.db.track_chat(
            update.effective_chat.id,
            update.effective_chat.type,
            update.effective_chat.title
        )
        
        # Track user
        eva.db.add_user(member.id, member.username, member.first_name)
        
        # Send varied welcome
        name = member.first_name or member.username or "friend"
        welcome = eva.smart.get_varied_welcome(name)
        
        await update.message.reply_text(welcome, parse_mode="Markdown")

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle group messages"""
    if not update.message or not update.message.text:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    message = update.message.text
    
    # Track chat activity
    eva.db.track_chat(chat.id, chat.type, chat.title)
    eva.db.add_user(user.id, user.username, user.first_name)
    
    # Check for spam
    is_spam, warning_level = eva.smart.check_spam(user.id, chat.id)
    if is_spam and warning_level > 0:
        warning_msg = eva.smart.get_spam_warning(warning_level, user.first_name or "friend")
        await update.message.reply_text(warning_msg, parse_mode="Markdown")
        return
    
    # Analyze if Eva should respond
    should_respond, response_type = eva.analyze_message(message, user.id, chat.id)
    
    if should_respond and response_type:
        logger.info(f"Eva responding: {message[:50]}... ({response_type})")
        eva.db.log_query(user.id, message)
        response = eva.generate_response(message, response_type)
        
        if response:
            # Natural delay before responding
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            try:
                await update.message.reply_text(
                    response,
                    parse_mode="Markdown",
                    reply_to_message_id=update.message.message_id
                )
                logger.info("✅ Response sent")
            except Exception as e:
                logger.error(f"❌ Error sending response: {e}")

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle private messages"""
    if not update.message or not update.message.text:
        return
    
    user = update.effective_user
    message = update.message.text
    
    # Track user
    eva.db.add_user(user.id, user.username, user.first_name)
    eva.db.log_query(user.id, message)
    
    # Always respond in private chats
    should_respond, response_type = eva.analyze_message(message, user.id, update.effective_chat.id)
    
    if not should_respond:
        response_type = "search"
    
    response = eva.generate_response(message, response_type)
    
    if response:
        await update.message.reply_text(response, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "🤔 I'm not sure about that. Try /menu to explore topics or /help for guidance!",
            parse_mode="Markdown"
        )

# =========================================================
# AUTOMATED JOBS
# =========================================================
async def post_daily_property(context: ContextTypes.DEFAULT_TYPE):
    """Post daily property to groups"""
    try:
        logger.info("🏠 Starting daily property post...")
        property_data = eva.get_next_property()
        
        if not property_data:
            logger.info("📭 No properties available")
            return
        
        active_chats = eva.db.get_active_chats()
        
        if not active_chats:
            logger.info("📭 No active chats for property posts")
            return
        
        message = f"🏠 *Featured Property*\n\n"
        message += f"*{property_data['topic']}*\n\n"
        message += f"{property_data['content']}\n\n"
        message += "💡 Use /properties to see all available listings!"
        
        for chat in active_chats:
            chat_id = chat['chat_id']
            
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Property posted to chat {chat_id}")
                await asyncio.sleep(3)
            except Exception as e:
                logger.error(f"❌ Failed to post property to chat {chat_id}: {e}")
                if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                    eva.db.deactivate_chat(chat_id)
        
        logger.info("✅ Daily property post complete")
    except Exception as e:
        logger.error(f"❌ Error in daily property post: {e}")

async def post_multiple_properties(context: ContextTypes.DEFAULT_TYPE):
    """Post properties at different times (10 AM, 2 PM, 6 PM)"""
    await post_daily_property(context)

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
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"❌ Failed to send greeting to chat {chat_id}: {e}")
                    if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                        eva.db.deactivate_chat(chat_id)
                        logger.info(f"🔇 Deactivated chat {chat_id}")
        
        logger.info("✅ Periodic greetings complete")
    except Exception as e:
        logger.error(f"❌ Error in periodic greetings: {e}")

async def send_engagement_content(context: ContextTypes.DEFAULT_TYPE):
    """Send engagement content (polls, questions, facts)"""
    try:
        logger.info("🎯 Starting engagement content...")
        active_chats = eva.db.get_active_chats()
        
        if not active_chats:
            logger.info("📭 No active chats for engagement")
            return
        
        engagement = eva.smart.get_engagement_prompt()
        
        for chat in active_chats:
            chat_id = chat['chat_id']
            
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=engagement,
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Engagement sent to chat {chat_id}")
                await asyncio.sleep(3)
            except Exception as e:
                logger.error(f"❌ Failed to send engagement to chat {chat_id}: {e}")
                if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                    eva.db.deactivate_chat(chat_id)
        
        logger.info("✅ Engagement content complete")
    except Exception as e:
        logger.error(f"❌ Error in engagement content: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buttons"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Main menu
    if data == "menu_back":
        await query.edit_message_text(
            "🇳🇦 *Explore Namibia*\n\nWhat would you like to learn about?",
            parse_mode="Markdown",
            reply_markup=menu.main_menu()
        )
    
    # Category selection
    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        content = menu.format_category(category)
        
        await query.edit_message_text(
            content,
            parse_mode="Markdown",
            reply_markup=menu.create_submenu(category)
        )
    
    # Topic selection
    elif data.startswith("topic_"):
        parts = data.split("_")
        if len(parts) >= 3:
            category = "_".join(parts[1:-1])
            try:
                topic_index = int(parts[-1])
            except:
                topic_index = 0
            
            topics = eva.kb.get_by_category(category)
            
            if topics and 0 <= topic_index < len(topics):
                topic = topics[topic_index]
                
                emoji_map = {
                    "Real Estate": "🏠",
                    "Tourism": "🏞️", "History": "📜", "Culture": "👥",
                    "Practical": "ℹ️", "Wildlife": "🦁", "Facts": "🚀",
                    "Geography": "🗺️"
                }
                
                emoji = emoji_map.get(category, "📌")
                
                response = f"{emoji} *{topic['topic']}*\n\n"
                response += f"{topic['content']}\n\n"
                
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
        
        await query.edit_message_text(
            "❌ Topic not found. Please try another topic.",
            parse_mode="Markdown",
            reply_markup=menu.back_button()
        )

# =========================================================
# MAIN
# =========================================================
def main():
    """Run Eva with webhook"""
    logger.info("=" * 60)
    logger.info("🇳🇦 EVA GEISES - FULL GROUP MANAGEMENT BOT")
    logger.info("=" * 60)
    logger.info(f"✅ Topics: {len(eva.kb.get_all_topics())}")
    logger.info(f"✅ Categories: {len(eva.kb.get_categories())}")
    logger.info(f"✅ Properties: {len(eva.get_property_posts())}")
    logger.info("=" * 60)
    
    # Start health check server
    run_health_server_background(port=8080)
    logger.info("🏥 Health server started on port 8080")
    
    # Build application
    try:
        from telegram.ext import JobQueue
        app = Application.builder() \
            .token(TELEGRAM_BOT_TOKEN) \
            .connect_timeout(15) \
            .read_timeout(10) \
            .write_timeout(10) \
            .build()
        has_job_queue = True
    except ImportError:
        logger.warning("⚠️ JobQueue not available")
        app = Application.builder() \
            .token(TELEGRAM_BOT_TOKEN) \
            .connect_timeout(15) \
            .read_timeout(10) \
            .write_timeout(10) \
            .build()
        has_job_queue = False
    
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
    
    # Schedule jobs
    if has_job_queue and app.job_queue:
        # Property posts 3x daily: 10 AM, 2 PM, 6 PM
        app.job_queue.run_daily(
            post_multiple_properties,
            time=datetime.strptime("10:00", "%H:%M").time(),
            name="property_post_10am"
        )
        app.job_queue.run_daily(
            post_multiple_properties,
            time=datetime.strptime("14:00", "%H:%M").time(),
            name="property_post_2pm"
        )
        app.job_queue.run_daily(
            post_multiple_properties,
            time=datetime.strptime("18:00", "%H:%M").time(),
            name="property_post_6pm"
        )
        
        # Periodic greetings every 2 hours
        app.job_queue.run_repeating(
            send_periodic_greetings,
            interval=7200,
            first=300,
            name="periodic_greetings"
        )
        
        # Engagement content every 4 hours
        app.job_queue.run_repeating(
            send_engagement_content,
            interval=14400,
            first=1800,
            name="engagement_content"
        )
        
        logger.info("📅 Property posts: 10 AM, 2 PM, 6 PM daily")
        logger.info("👋 Periodic greetings: Every 2 hours")
        logger.info("🎯 Engagement content: Every 4 hours")
    else:
        logger.warning("⚠️ Scheduled jobs disabled")
    
    logger.info("🚀 Eva is running with full group management...")
    logger.info(f"🔗 Webhook URL: {WEBHOOK_URL}")
    
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
