# 🇳🇦 Eva Geises - Namibia Expert Telegram Bot

An intelligent Telegram bot that provides comprehensive information about Namibia, including tourism, culture, wildlife, and real estate opportunities.

## ✨ Features

- 🤖 **AI-Powered Responses** - Smart message analysis and context-aware replies
- 🏞️ **Tourism Information** - Detailed info about Namibian destinations
- 🦁 **Wildlife Knowledge** - Information about Namibia's unique wildlife
- 👥 **Cultural Insights** - Learn about Namibian cultures and traditions
- 🏠 **Real Estate Listings** - Property information in Windhoek, Omuthiya, and more
- 📊 **Interactive Menus** - Easy navigation through topics
- 🕐 **Scheduled Features** - Automated daily posts and periodic greetings
- 📈 **Analytics** - Track user queries and engagement

## 🚀 Deployment

This bot is ready to deploy on multiple platforms:

- **Render** (Free tier) - See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Railway** - Use existing `railway.json`
- **Heroku** - Procfile included
- **Fly.io** - Compatible
- **DigitalOcean App Platform** - Compatible

### Quick Start on Render

1. Fork/clone this repository
2. Sign up at [render.com](https://render.com)
3. Create new Web Service
4. Connect your GitHub repository
5. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `ADMIN_IDS` (optional)
6. Deploy!

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

## 🔧 Configuration

### Environment Variables

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321  # Optional, comma-separated
DATABASE_PATH=bot_data.db  # Optional, default path
```

### Requirements

- Python 3.11+
- python-telegram-bot[job-queue]==20.7
- python-dotenv==1.0.0
- requests==2.31.0
- rapidfuzz==3.5.2
- pandas

## 📚 Bot Commands

- `/start` - Welcome message and introduction
- `/menu` - Interactive menu with categories
- `/properties` - View real estate listings
- `/topics` - Browse all available topics
- `/stats` - View bot statistics (admin only)
- `/help` - Get help and instructions

## 🎯 Key Features

### Smart Message Analysis
The bot intelligently detects:
- Direct mentions (@eva, eva, etc.)
- Questions (what, how, where, etc.)
- Greetings (hi, hello, etc.)
- Namibia-related keywords
- Real estate inquiries
- Travel queries

### Automated Features
- **Daily Property Posts** - 10:00 AM daily
- **Periodic Greetings** - Every 2 hours
- **Smart Engagement** - Context-aware responses

### Database Tracking
- User registration and activity
- Query logging and analytics
- Chat tracking for groups
- Popular topics analysis

## 🏗️ Project Structure

```
├── main.py              # Main bot application
├── database.py          # Database operations
├── knowledge_base.py    # Knowledge base and search
├── smart_features.py    # Smart features add-on
├── requirements.txt     # Python dependencies
├── render.yaml          # Render configuration
├── railway.json         # Railway configuration
├── Procfile            # Process file for deployment
├── runtime.txt         # Python version specification
└── DEPLOYMENT_GUIDE.md # Detailed deployment instructions
```

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## 📝 License

This project is open source and available for personal and educational use.

## 👨‍💻 Author

Created for sharing knowledge about Namibia 🇳🇦

## 🆘 Support

If you encounter any issues:
1. Check the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Review Render logs
3. Verify environment variables
4. Test bot token is valid

## 🌟 Acknowledgments

- Built with python-telegram-bot library
- Powered by Render's free tier
- Inspired by the beauty of Namibia

---

**Ready to deploy?** Check out [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step instructions!
"# RenderBot" 
