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
from advanced_ai import AdvancedAI
from conversational_intelligence import ConversationalIntelligence
from document_rag import DocumentRAG

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

# Webhook configuration - Auto-detect from Render
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
if RENDER_EXTERNAL_URL:
    # Render provides this automatically
    WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}/webhook"
    logger.info(f"✅ Using Render auto-detected URL: {RENDER_EXTERNAL_URL}")
else:
    # Fallback to manual configuration
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://renderbot-x64y.onrender.com/webhook")
    logger.warning(f"⚠️ Using fallback webhook URL: {WEBHOOK_URL}")

PORT = int(os.environ.get("PORT", "10000"))

logger.info(f"🌐 Webhook will be: {WEBHOOK_URL}")
logger.info(f"🔌 Port: {PORT}")

# =========================================================
# EVA GEISES - NAMIBIA BOT ENGINE WITH FULL GROUP MANAGEMENT
# =========================================================
class EvaGeisesBot:
    def __init__(self):
        self.db = Database()
        self.kb = KnowledgeBase()
        self.smart = SmartFeatures()
        self.ai = AdvancedAI()  # Advanced AI features
        self.ci = ConversationalIntelligence()  # Conversational intelligence
        self.rag = DocumentRAG()  # RAG document system
        self.last_activity = {}
        self.welcomed_users = set()
        self.last_greeting = {}
        self.last_property_post = {}
        self.property_rotation_index = 0
        self.rag_initialized = False  # Track RAG initialization
        logger.info(f"🇳🇦 Eva Geises initialized with {len(self.kb.get_all_topics())} topics")
        logger.info("🤖 Advanced AI features loaded")
        logger.info("🧠 Conversational intelligence enabled")
        logger.info("📚 RAG document system initialized")
    
    async def initialize_rag(self):
        """Initialize RAG system by syncing documents from GitHub"""
        if self.rag_initialized:
            return True
        
        try:
            logger.info("📥 Starting initial RAG document sync...")
            success = await self.rag.sync_documents()
            
            if success:
                stats = self.rag.get_stats()
                logger.info(f"✅ RAG initialized: {stats['total_documents']} documents, {stats['total_chunks']} chunks")
                self.rag_initialized = True
                return True
            else:
                logger.warning("⚠️ RAG sync failed on initialization")
                return False
        except Exception as e:
            logger.error(f"❌ RAG initialization error: {e}")
            return False
    
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
    
    def generate_response(self, message, response_type, user_id=None):
        """Generate Eva's response - CONVERSATIONAL INTELLIGENCE + RAG"""
        
        # Use conversational intelligence if user_id provided
        if user_id and response_type == "search":
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
            
            # SEARCH RAG DOCUMENTS FIRST (higher priority)
            rag_results = self.rag.search_documents(clean_msg, limit=3) if clean_msg else []
            
            # Search knowledge base
            kb_results = self.kb.search(clean_msg, limit=5) if clean_msg else []
            
            # Combine results (RAG first, then KB)
            all_results = []
            
            # Add RAG results
            for rag_result in rag_results:
                all_results.append({
                    'topic': f"📄 {rag_result['filename']}",
                    'content': rag_result['text'],
                    'source': 'document',
                    'score': rag_result['score']
                })
            
            # Add KB results
            for kb_result in kb_results:
                all_results.append({
                    'topic': kb_result['topic'],
                    'content': kb_result['content'],
                    'source': 'knowledge_base',
                    'score': 50  # Default score for KB
                })
            
            # Use conversational intelligence to generate response
            intelligent_response = self.ci.generate_intelligent_response(
                message, user_id, all_results, response_type
            )
            
            return intelligent_response
        
        # Fallback to standard responses with RAG
        clean_msg = message.lower().strip()
        clean_msg = re.sub(r'[?!.,;:]+', ' ', clean_msg)
        clean_msg = re.sub(r'@[^\s]*', '', clean_msg)
        
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
        
        # Search both RAG and KB
        if response_type == "search" and clean_msg:
            rag_results = self.rag.search_documents(clean_msg, limit=2)
            kb_results = self.kb.search(clean_msg, limit=3)
            
            # Prefer RAG results if available
            if rag_results:
                best = rag_results[0]
                
                response = f"📄 *From: {best['filename']}*\n\n"
                response += f"{best['text']}\n\n"
                
                # Show source
                response += f"_Source: Document Library_\n\n"
                
                # Show related if available
                if len(rag_results) > 1:
                    response += "💡 *More in documents:* "
                    response += ", ".join([r['filename'] for r in rag_results[1:]])
                    response += "\n\n"
                
                response += "Use /documents to see all available docs! 📚"
                return response
            
            # Fallback to KB results
            elif kb_results:
                best = kb_results[0]
                
                response = f"*{best['topic']}*\n\n"
                response += f"{best['content']}\n\n"
                
                if len(kb_results) > 1:
                    response += "💡 *Related:* "
                    response += ", ".join([r['topic'] for r in kb_results[1:3]])
                    response += "\n\n"
                
                response += "Need more? Use /menu! 🇳🇦"
                return response
            
            else:
                # No results
                return (
                    "🤔 I don't have specific info on that.\n\n"
                    "Try:\n"
                    "• /documents - Browse document library\n"
                    "• /menu - Browse topics\n"
                    "• Ask about Etosha, Sossusvlei, or Wildlife"
                )
        
        elif response_type == "greeting":
            greeting = self.get_greeting()
            return (
                f"{greeting}! 👋\n\n"
                f"I'm Eva Geises, your Namibia expert! 🇳🇦\n\n"
                f"Ask me anything or use /menu!"
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
    
    def category_menu(self, category):
        """Show topics in category"""
        topics = self.kb.get_by_category(category)
        
        if not topics:
            return None
        
        keyboard = []
        
        for i, topic in enumerate(topics):
            display = topic['topic'][:40]
            callback = f"topic_{category}_{i}"
            keyboard.append([InlineKeyboardButton(display, callback_data=callback)])
        
        keyboard.append([InlineKeyboardButton("« Back", callback_data="menu_main")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def back_button(self, category=None):
        """Create back button"""
        if category:
            keyboard = [[InlineKeyboardButton("« Back to Topics", callback_data=f"cat_{category}")]]
        else:
            keyboard = [[InlineKeyboardButton("« Main Menu", callback_data="menu_main")]]
        return InlineKeyboardMarkup(keyboard)
    
    def get_category_description(self, category):
        """Get description for category"""
        topics = self.kb.get_by_category(category)
        
        if not topics:
            return f"*{category}*\n\nNo topics available in this category."
        
        emoji_map = {
            "Real Estate": "🏠",
            "Tourism": "🏞️", "History": "📜", "Culture": "👥",
            "Practical": "ℹ️", "Wildlife": "🦁", "Facts": "🚀",
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
    is_admin = update.effective_user.id in ADMIN_IDS
    
    help_text = (
        "🇳🇦 *Eva Geises - Advanced AI Assistant*\n\n"
        "🎯 *Core Commands:*\n"
        "/menu - Browse topics by category\n"
        "/properties - View real estate listings\n"
        "/topics - List all topics\n"
        "/help - Show this help\n\n"
        "🤖 *AI Features:*\n"
        "/weather - Get Namibia weather\n"
        "/news - Latest Namibia news\n"
        "/story - Random Namibia story\n"
        "/brainstorm - Get creative ideas\n"
        "/poll - Create engagement poll\n"
        "/discuss - Start discussion\n"
        "/fact - Random Namibia fact\n\n"
        "📚 *Document System:*\n"
        "/documents - Browse document library\n"
        "/docs - Same as /documents\n\n"
        "💡 *How to use:*\n"
        "Just ask questions naturally!\n"
        "Examples:\n"
        "• \"Tell me about Etosha\"\n"
        "• \"Where is Sossusvlei?\"\n"
        "• \"Show me properties\"\n"
    )
    
    if is_admin:
        help_text += (
            "\n🔧 *Admin Commands:*\n"
            "/sync_docs - Sync documents from GitHub\n"
            "/rag_stats - Show RAG statistics\n"
            "/stats - Show bot statistics\n"
            "/test_automation - Test features\n"
            "/force_post - Force content post\n"
            "/activate_group - Activate group\n"
            "/diagnose - System diagnostics\n"
        )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add me to group instruction"""
    await update.message.reply_text(
        "👥 *Add Me to Your Group!*\n\n"
        "1. Go to your group chat\n"
        "2. Click group name → Add members\n"
        "3. Search for Eva Geises\n"
        "4. Add me!\n\n"
        "I'll introduce myself and start helping! 🇳🇦",
        parse_mode="Markdown"
    )

# Advanced AI Commands
async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get Namibia weather"""
    weather = await eva.ai.get_namibia_weather()
    await update.message.reply_text(weather, parse_mode="Markdown")

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get Namibia news"""
    news = await eva.ai.get_namibia_news()
    await update.message.reply_text(news, parse_mode="Markdown")

async def story_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tell a Namibia story"""
    story = eva.ai.tell_namibia_story()
    await update.message.reply_text(story, parse_mode="Markdown")

async def brainstorm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate brainstorm ideas"""
    ideas = eva.ai.generate_brainstorm_ideas()
    await update.message.reply_text(ideas, parse_mode="Markdown")

async def poll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create an engagement poll"""
    try:
        poll_data = eva.ai.generate_poll()
        await update.message.reply_poll(
            question=poll_data["question"],
            options=poll_data["options"],
            is_anonymous=False
        )
    except Exception as e:
        logger.error(f"Poll error: {e}")
        await update.message.reply_text("❌ Sorry, couldn't create poll. This might be a private chat.")

async def discuss_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a discussion topic"""
    topic = eva.ai.generate_discussion_topic()
    await update.message.reply_text(topic, parse_mode="Markdown")

async def fact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Share a random fact"""
    fact = eva.ai.get_random_fact()
    await update.message.reply_text(fact, parse_mode="Markdown")

async def documents_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List available RAG documents"""
    docs = eva.rag.list_documents()
    
    if not docs:
        await update.message.reply_text(
            "📚 *Document Library*\n\n"
            "No documents available yet.\n\n"
            "💡 Use /sync_docs (admin) to load documents from GitHub.",
            parse_mode="Markdown"
        )
        return
    
    response = f"📚 *Document Library* ({len(docs)} documents)\n\n"
    
    for i, doc in enumerate(docs[:10], 1):
        filename = doc['filename'].replace('.pdf', '').replace('.docx', '').replace('_', ' ')
        response += f"{i}. 📄 {filename}\n"
        response += f"   _{doc['word_count']} words_\n\n"
    
    if len(docs) > 10:
        response += f"...and {len(docs) - 10} more documents\n\n"
    
    response += "💡 Just ask questions - I'll search through all documents automatically!"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def sync_docs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sync documents from GitHub - Admin only"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🔒 This command is only available to administrators.")
        return
    
    await update.message.reply_text("📥 Syncing documents from GitHub...", parse_mode="Markdown")
    
    success = await eva.rag.sync_documents()
    
    if success:
        stats = eva.rag.get_stats()
        response = (
            f"✅ *Documents Synced!*\n\n"
            f"📚 Total documents: {stats['total_documents']}\n"
            f"🔍 Searchable chunks: {stats['total_chunks']}\n"
            f"⏰ Last sync: {stats['last_sync'][:19]}\n\n"
            f"Documents are now searchable!"
        )
    else:
        response = "❌ Document sync failed. Check logs for details."
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def rag_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show RAG system statistics"""
    stats = eva.rag.get_stats()
    
    response = f"📊 *RAG System Statistics*\n\n"
    response += f"📚 Documents: {stats['total_documents']}\n"
    response += f"🔍 Chunks: {stats['total_chunks']}\n"
    response += f"⏰ Last sync: {stats['last_sync'][:19] if stats['last_sync'] != 'Never' else 'Never'}\n"
    response += f"📁 Source: GitHub\n\n"
    response += f"💡 Use /documents to see available files!"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def test_automation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test all automation features - Admin only"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🔒 This command is only available to administrators.")
        return
    
    chat_id = update.effective_chat.id
    
    # Track this chat as active
    eva.db.track_chat(chat_id, update.effective_chat.type, update.effective_chat.title or "Test Chat")
    
    await update.message.reply_text(
        "🧪 *Testing Automation Features*\n\n"
        "Triggering all automated features now...\n\n"
        "Watch for:\n"
        "1. Greeting\n"
        "2. Property post\n"
        "3. AI content (poll/story/weather/etc)\n\n"
        "⏳ Please wait...",
        parse_mode="Markdown"
    )
    
    # Test greeting
    try:
        greeting = eva.get_periodic_greeting()
        await update.message.reply_text(greeting, parse_mode="Markdown")
        await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Greeting test error: {e}")
    
    # Test property post
    try:
        property_data = eva.get_next_property()
        if property_data:
            message = f"🏠 *Featured Property*\n\n"
            message += f"*{property_data['topic']}*\n\n"
            message += f"{property_data['content']}\n\n"
            message += "💡 Use /properties to see all available listings!"
            await update.message.reply_text(message, parse_mode="Markdown")
            await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Property test error: {e}")
    
    # Test AI content
    try:
        story = eva.ai.tell_namibia_story()
        await update.message.reply_text(story, parse_mode="Markdown")
        await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Story test error: {e}")
    
    await update.message.reply_text(
        "✅ *Test Complete!*\n\n"
        "If you see greeting, property, and story above, automation is working!\n\n"
        "Automated posts will now happen:\n"
        "• Every 2 hours - Greetings\n"
        "• Every 4 hours - AI content\n"
        "• 10 AM, 2 PM, 6 PM - Properties\n\n"
        "💡 Use /force_post to manually trigger content anytime.",
        parse_mode="Markdown"
    )

async def force_post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force post content now - Admin only"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🔒 This command is only available to administrators.")
        return
    
    chat_id = update.effective_chat.id
    
    # Track chat
    eva.db.track_chat(chat_id, update.effective_chat.type, update.effective_chat.title or "Group")
    
    # Determine what to post
    args = context.args
    content_type = args[0].lower() if args else "random"
    
    try:
        if content_type == "greeting":
            greeting = eva.get_periodic_greeting()
            await update.message.reply_text(greeting, parse_mode="Markdown")
        
        elif content_type == "property":
            property_data = eva.get_next_property()
            if property_data:
                message = f"🏠 *Featured Property*\n\n"
                message += f"*{property_data['topic']}*\n\n"
                message += f"{property_data['content']}\n\n"
                message += "💡 Use /properties to see all available listings!"
                await update.message.reply_text(message, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ No properties available")
        
        elif content_type == "poll":
            poll_data = eva.ai.generate_poll()
            await context.bot.send_poll(
                chat_id=chat_id,
                question=poll_data["question"],
                options=poll_data["options"],
                is_anonymous=False
            )
        
        elif content_type == "story":
            story = eva.ai.tell_namibia_story()
            await update.message.reply_text(story, parse_mode="Markdown")
        
        elif content_type == "weather":
            weather = await eva.ai.get_namibia_weather()
            await update.message.reply_text(weather, parse_mode="Markdown")
        
        elif content_type == "news":
            news = await eva.ai.get_namibia_news()
            await update.message.reply_text(news, parse_mode="Markdown")
        
        elif content_type == "discuss":
            discussion = eva.ai.generate_discussion_topic()
            await update.message.reply_text(discussion, parse_mode="Markdown")
        
        elif content_type == "brainstorm":
            ideas = eva.ai.generate_brainstorm_ideas()
            await update.message.reply_text(ideas, parse_mode="Markdown")
        
        else:
            # Random content
            content_types = ["greeting", "property", "story", "poll", "discuss"]
            selected = random.choice(content_types)
            
            await update.message.reply_text(f"🎲 Posting random content: {selected}")
            await asyncio.sleep(1)
            
            # Recurse with selected type
            context.args = [selected]
            await force_post_command(update, context)
    
    except Exception as e:
        logger.error(f"Force post error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def activate_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activate current group for automated posts - Admin only"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🔒 This command is only available to administrators.")
        return
    
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = update.effective_chat.title or "Private Chat"
    
    eva.db.track_chat(chat_id, chat_type, chat_title)
    
    await update.message.reply_text(
        f"✅ *Group Activated!*\n\n"
        f"📊 Chat ID: `{chat_id}`\n"
        f"📋 Type: {chat_type}\n"
        f"📝 Title: {chat_title}\n\n"
        f"This group will now receive:\n"
        f"• 👋 Greetings every 2 hours\n"
        f"• 🏠 Properties 3x daily\n"
        f"• 🎯 Engagement every 4 hours\n\n"
        f"💡 Use /test_automation to verify!",
        parse_mode="Markdown"
    )

async def diagnose_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """System diagnostics - Admin only"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🔒 This command is only available to administrators.")
        return
    
    # Gather diagnostic info
    active_chats = eva.db.get_active_chats()
    rag_stats = eva.rag.get_stats()
    
    response = "🔍 *System Diagnostics*\n\n"
    response += f"*Bot Status:* ✅ Running\n"
    response += f"*Active Chats:* {len(active_chats)}\n"
    response += f"*KB Topics:* {len(eva.kb.get_all_topics())}\n"
    response += f"*Properties:* {len(eva.get_property_posts())}\n\n"
    
    response += "*RAG System:*\n"
    response += f"Documents: {rag_stats['total_documents']}\n"
    response += f"Chunks: {rag_stats['total_chunks']}\n"
    response += f"Last Sync: {rag_stats['last_sync'][:19] if rag_stats['last_sync'] != 'Never' else 'Never'}\n"
    response += f"RAG Initialized: {'✅ Yes' if eva.rag_initialized else '❌ No'}\n\n"
    
    response += "*Active Groups:*\n"
    for i, chat in enumerate(active_chats[:5], 1):
        response += f"{i}. {chat['title'][:30]} (ID: {chat['chat_id']})\n"
    
    if len(active_chats) > 5:
        response += f"...and {len(active_chats) - 5} more\n"
    
    await update.message.reply_text(response, parse_mode="Markdown")

# =========================================================
# MESSAGE HANDLERS
# =========================================================
async def handle_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new group members"""
    for member in update.message.new_chat_members:
        if member.is_bot and member.id == context.bot.id:
            # Bot was added to group
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
        response = eva.generate_response(message, response_type, user_id=user.id)
        
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
    
    response = eva.generate_response(message, response_type, user_id=user.id)
    
    if response:
        await update.message.reply_text(response, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "🤔 Not sure about that. What specific aspect of Namibia interests you? 😊",
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
                    logger.error(f"❌ Failed to send greeting to {chat_id}: {e}")
        
        logger.info("✅ Periodic greetings complete")
    except Exception as e:
        logger.error(f"❌ Error in periodic greetings: {e}")

async def send_engagement_content(context: ContextTypes.DEFAULT_TYPE):
    """Send engagement content to groups"""
    try:
        logger.info("🎯 Starting engagement content...")
        active_chats = eva.db.get_active_chats()
        
        if not active_chats:
            logger.info("📭 No active chats for engagement")
            return
        
        # Randomly select content type
        content_types = ["poll", "story", "discuss", "brainstorm"]
        selected_type = random.choice(content_types)
        
        logger.info(f"📤 Posting {selected_type} to groups")
        
        for chat in active_chats:
            chat_id = chat['chat_id']
            
            try:
                if selected_type == "poll":
                    poll_data = eva.ai.generate_poll()
                    await context.bot.send_poll(
                        chat_id=chat_id,
                        question=poll_data["question"],
                        options=poll_data["options"],
                        is_anonymous=False
                    )
                
                elif selected_type == "story":
                    story = eva.ai.tell_namibia_story()
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=story,
                        parse_mode="Markdown"
                    )
                
                elif selected_type == "discuss":
                    discussion = eva.ai.generate_discussion_topic()
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=discussion,
                        parse_mode="Markdown"
                    )
                
                elif selected_type == "brainstorm":
                    ideas = eva.ai.generate_brainstorm_ideas()
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=ideas,
                        parse_mode="Markdown"
                    )
                
                logger.info(f"✅ {selected_type} sent to chat {chat_id}")
                await asyncio.sleep(3)
            
            except Exception as e:
                logger.error(f"❌ Failed to send {selected_type} to {chat_id}: {e}")
        
        logger.info(f"✅ Engagement content ({selected_type}) complete")
    except Exception as e:
        logger.error(f"❌ Error in engagement content: {e}")

# =========================================================
# CALLBACK HANDLERS
# =========================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Main menu
    if data == "menu_main":
        await query.edit_message_text(
            "🇳🇦 *Explore Namibia*\n\nWhat would you like to learn about?",
            parse_mode="Markdown",
            reply_markup=menu.main_menu()
        )
        return
    
    # Category menu
    if data.startswith("cat_"):
        category = data[4:]
        description = menu.get_category_description(category)
        category_markup = menu.category_menu(category)
        
        if category_markup:
            await query.edit_message_text(
                description,
                parse_mode="Markdown",
                reply_markup=category_markup
            )
        else:
            await query.edit_message_text(
                f"❌ No topics found in {category}",
                parse_mode="Markdown",
                reply_markup=menu.back_button()
            )
        return
    
    # Topic detail
    if data.startswith("topic_"):
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
# STARTUP INITIALIZATION
# =========================================================
async def post_init(application: Application):
    """Run after application starts - Initialize RAG"""
    logger.info("🚀 Running post-initialization tasks...")
    
    # Initialize RAG system
    try:
        rag_success = await eva.initialize_rag()
        
        if rag_success:
            logger.info("✅ RAG system initialized and documents synced")
        else:
            logger.warning("⚠️ RAG initialization completed with warnings")
    except Exception as e:
        logger.error(f"❌ RAG initialization failed: {e}")
        logger.info("💡 Documents can still be synced manually with /sync_docs")
    
    logger.info("✅ Post-initialization complete")

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
    logger.info("📚 RAG system will initialize after bot starts")
    logger.info("=" * 60)
    
    # Extract base URL from webhook URL for self-ping
    service_url = WEBHOOK_URL.replace('/webhook', '') if WEBHOOK_URL else None
    
    # Start health check server (try enhanced version, fallback to basic)
    try:
        run_health_server_background(port=8080, service_url=service_url)
        logger.info("🏥 Enhanced health server started on port 8080")
        logger.info("🔄 Self-ping enabled - Service will stay awake!")
    except TypeError:
        # Fallback to old version without service_url
        run_health_server_background(port=8080)
        logger.info("🏥 Basic health server started on port 8080")
        logger.warning("⚠️ Update health_server.py for self-ping feature")
    
    # Build application
    try:
        from telegram.ext import JobQueue
        app = Application.builder() \
            .token(TELEGRAM_BOT_TOKEN) \
            .connect_timeout(15) \
            .read_timeout(10) \
            .write_timeout(10) \
            .post_init(post_init) \
            .build()
        has_job_queue = True
    except ImportError:
        logger.warning("⚠️ JobQueue not available")
        app = Application.builder() \
            .token(TELEGRAM_BOT_TOKEN) \
            .connect_timeout(15) \
            .read_timeout(10) \
            .write_timeout(10) \
            .post_init(post_init) \
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
    
    # Advanced AI Commands
    app.add_handler(CommandHandler('weather', weather_command))
    app.add_handler(CommandHandler('news', news_command))
    app.add_handler(CommandHandler('story', story_command))
    app.add_handler(CommandHandler('brainstorm', brainstorm_command))
    app.add_handler(CommandHandler('poll', poll_command))
    app.add_handler(CommandHandler('discuss', discuss_command))
    app.add_handler(CommandHandler('fact', fact_command))
    
    # RAG Document Commands
    app.add_handler(CommandHandler('documents', documents_command))
    app.add_handler(CommandHandler('docs', documents_command))  # Alias
    app.add_handler(CommandHandler('sync_docs', sync_docs_command))
    app.add_handler(CommandHandler('rag_stats', rag_stats_command))
    
    # Admin Testing & Control Commands
    app.add_handler(CommandHandler('test_automation', test_automation_command))
    app.add_handler(CommandHandler('force_post', force_post_command))
    app.add_handler(CommandHandler('activate_group', activate_group_command))
    app.add_handler(CommandHandler('diagnose', diagnose_command))
    
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
    logger.info(f"🔌 Listening on: 0.0.0.0:{PORT}")
    logger.info(f"📡 Webhook path: /webhook")
    logger.info(f"🏥 Health check: port 8080")
    logger.info("=" * 60)
    
    try:
        # Run webhook with improved configuration
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="/webhook",
            webhook_url=WEBHOOK_URL,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "chat_member"],
            secret_token=None  # Can add security token if needed
        )
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        logger.info("🔄 Attempting to restart webhook...")
        raise

if __name__ == "__main__":
    main()
