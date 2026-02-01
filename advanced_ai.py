"""
Advanced AI Features for Eva Geises Bot
Includes: Web Search, Storytelling, Polls, News, Weather, Brainstorming
"""

import random
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AdvancedAI:
    """Advanced AI capabilities for Eva Geises"""
    
    def __init__(self):
        self.last_brainstorm = {}
        self.last_story = {}
        self.last_poll = {}
        self.stories_told = []
        
    async def search_web(self, query: str) -> Optional[Dict]:
        """Search the web for real-time information"""
        try:
            # Using DuckDuckGo Instant Answer API (no key needed)
            async with aiohttp.ClientSession() as session:
                url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
            return None
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return None
    
    async def get_namibia_weather(self) -> str:
        """Get current weather information for Namibia"""
        # Try multiple weather sources
        cities = ["Windhoek", "Swakopmund", "Walvis Bay"]
        weather_info = []
        
        for city in cities:
            try:
                # Using Open-Meteo API (free, no key needed)
                # Coordinates for major Namibian cities
                coords = {
                    "Windhoek": {"lat": -22.5609, "lon": 17.0658},
                    "Swakopmund": {"lat": -22.6792, "lon": 14.5272},
                    "Walvis Bay": {"lat": -22.9575, "lon": 14.5053}
                }
                
                coord = coords[city]
                url = f"https://api.open-meteo.com/v1/forecast?latitude={coord['lat']}&longitude={coord['lon']}&current_weather=true&timezone=Africa/Windhoek"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            weather = data.get('current_weather', {})
                            temp = weather.get('temperature', 'N/A')
                            windspeed = weather.get('windspeed', 'N/A')
                            weather_info.append(f"*{city}:* {temp}°C, Wind: {windspeed} km/h")
            except Exception as e:
                logger.error(f"Weather fetch error for {city}: {e}")
                continue
        
        if weather_info:
            response = "🌤️ *Namibia Weather Update*\n\n"
            response += "\n".join(weather_info)
            response += "\n\n_Live weather data of Namibia_"
            return response
        else:
            return "🌤️ *Namibia Weather*\n\nGenerally sunny with warm temperatures. Perfect safari weather! ☀️"
    
    async def get_namibia_news(self) -> str:
        """Get latest Namibia news"""
        try:
            # Search for Namibia news
            query = "Namibia+news+latest"
            result = await self.search_web(query)
            
            if result and result.get('RelatedTopics'):
                news_items = []
                for item in result['RelatedTopics'][:5]:
                    if isinstance(item, dict) and item.get('Text'):
                        news_items.append(f"• {item['Text'][:150]}...")
                
                if news_items:
                    response = "📰 *Latest Namibia News*\n\n"
                    response += "\n\n".join(news_items)
                    response += "\n\n_Updates from web search_"
                    return response
            
            # Fallback to curated news topics
            return self._get_fallback_news()
        except Exception as e:
            logger.error(f"News fetch error: {e}")
            return self._get_fallback_news()
    
    def _get_fallback_news(self) -> str:
        """Fallback news topics when web search fails"""
        topics = [
            "📰 *Namibia in Focus*\n\n🦁 Wildlife conservation efforts continue\n🏗️ Infrastructure development ongoing\n🌍 Tourism sector thriving\n💼 Economic growth initiatives\n\n_Stay updated on Namibia developments!_",
            "📰 *Namibia Updates*\n\n🇳🇦 National development projects\n🦏 Rhino conservation success\n🏖️ Coastal tourism growing\n🌾 Agricultural initiatives\n\n_Namibia moving forward!_",
            "📰 *Namibia Today*\n\n🏞️ Etosha attracting global visitors\n🏠 Real estate market active\n🌟 Cultural heritage celebrated\n🚀 Innovation in focus\n\n_The spirit of Namibia!_"
        ]
        return random.choice(topics)
    
    def generate_brainstorm_ideas(self, topic: str = "Namibia") -> str:
        """Generate creative brainstorming ideas"""
        idea_sets = {
            "general": [
                "🎯 *Brainstorming: Namibia Innovation*\n\n1. **Virtual Safari Tours** 🦁\n   • 360° experiences for global audience\n   • Live wildlife streaming\n\n2. **Eco-Tourism Hubs** 🌍\n   • Sustainable community projects\n   • Solar-powered lodges\n\n3. **Cultural Exchange Programs** 👥\n   • Himba heritage experiences\n   • Traditional craft workshops\n\n4. **Desert Adventure Sports** 🏜️\n   • Sandboarding championships\n   • Dune marathons\n\n5. **Wildlife Conservation Tech** 🦏\n   • AI-powered anti-poaching\n   • GPS tracking systems\n\n💡 *What else can we do for Namibia?*",
                
                "💭 *Creative Ideas: Namibia Development*\n\n1. **Smart Tourism App** 📱\n   • Real-time safari tracking\n   • Local guide connections\n\n2. **Namibian Food Festival** 🍽️\n   • Showcase traditional cuisine\n   • International food tourism\n\n3. **Desert Film Industry** 🎬\n   • Hollywood of Africa\n   • Natural film locations\n\n4. **Renewable Energy Hub** ⚡\n   • Solar farms in Namib\n   • Wind energy coast\n\n5. **Wildlife Photography School** 📸\n   • Train next generation\n   • Conservation awareness\n\n🚀 *Let's innovate together!*"
            ],
            "business": [
                "💼 *Business Ideas: Namibia Edition*\n\n1. **Safari Drone Tours** 🚁\n   • Aerial wildlife viewing\n   • Photography packages\n\n2. **Mobile Real Estate Platform** 🏠\n   • Easy property search\n   • Virtual tours\n\n3. **Namibian Craft Export** 🎨\n   • Himba crafts online\n   • Global marketplace\n\n4. **Adventure Tourism Packages** 🏕️\n   • Desert camping experiences\n   • Cultural immersion trips\n\n5. **Wildlife Tracking App** 📍\n   • Real-time animal locations\n   • Conservation data\n\n💰 *Entrepreneurship opportunities!*"
            ]
        }
        
        category = "business" if any(k in topic.lower() for k in ["business", "invest", "money", "entrepreneur"]) else "general"
        return random.choice(idea_sets[category])
    
    def tell_namibia_story(self) -> str:
        """Generate engaging stories about Namibia"""
        stories = [
            """📖 *The San People*

The San people (or Bushmen) are an indigenous hunter-gatherer group, one of the world's oldest momadic people with roots dating back to 100,000 years.

Primarily living in Botswana, Namibia, and surrounding nations.

The term "San" is a Khoekhoe term, but themselves they prefer to be identified as !Kung or Ju/'hoansi.

🌅 *Traditionally nomadic.*

What's your favorite Namibia story? Share with us!""",

            """📖 *The Desert Elephants' Journey*

In the Kunene region, elephants learned something extraordinary—how to survive in the desert.

These magnificent creatures trek over 70km daily, remembering every waterhole, every hidden spring. Mothers teach their calves the ancient routes, passing down knowledge through generations.

They've adapted to dig for water, eat desert plants, and withstand extreme heat. Scientists call them "desert-adapted," but locals call them "survivors."

🐘 *Nature finds a way, always.*

Have you seen Namibia's desert elephants?""",

            """📖 *The Story of the Himba People*

The Himba have lived in northern Namibia for centuries, maintaining traditions in a modern world.

Their signature red ochre paste isn't just beauty—it's protection from the harsh desert sun. Each hairstyle tells a story: marital status, age, social position.

They're semi-nomadic pastoralists, moving with their cattle, reading the land, respecting nature. When development came, they chose to preserve their culture while embracing useful technology.

👥 *Tradition and progress can walk together.*

What traditions do you value?""",

            """🏖️ *Swakopmund: Where Desert Meets Ocean*

Swakopmund is both a quiet retreat and a wild experience. Simultaneously a city of timelessness and a starting point for your wildest dreams."

Swakopmund is like a mirage between two worlds. On one side, the endless Namib Desert, shimmering under the sun like living gold.

If you’re looking for something even crazier, try sandboarding in Dune 7. From nearby Walvis Bay, cruises set off, taking you amidst playful dolphins and curious seals. You might even see a pelican joining the boat directly in search of fish.

*The Little Wonders of Namib Desert.*

Have you been in Swakopmund, tell us what was your adventure?"""
        ]
        
        # Track stories to avoid repetition
        if len(self.stories_told) >= len(stories):
            self.stories_told = []
        
        available = [s for s in stories if s not in self.stories_told]
        story = random.choice(available)
        self.stories_told.append(story)
        
        return story
    
    def generate_poll(self) -> Dict:
        """Generate engaging polls about Namibia"""
        polls = [
            {
                "question": "🦁 Which Namibian destination would you visit first?",
                "options": [
                    "Etosha National Park (Wildlife Safari)",
                    "Sossusvlei (Red Sand Dunes)",
                    "Swakopmund (Coastal Adventure)",
                    "Fish River Canyon (Hiking)",
                    "Okavango Delta (Trophy Hunting)"
                ]
            },
            {
                "question": "🏠 What type of property interests you most in Namibia?",
                "options": [
                    "City House (Windhoek)",
                    "Beach House (Swakopmund)",
                    "Safari Lodge (Near Etosha)",
                    "Farm/Ranch (Countryside)",
                    "Commercial Property"
                ]
            },
            {
                "question": "🌍 What should Namibia do to attract tourists?",
                "options": [
                    "Luxury Safari Experiences",
                    "Adventure Sports & Activities",
                    "Cultural Heritage Tours",
                    "Eco-Tourism & Conservation",
                    "Budget-Friendly Travel"
                ]
            },
            {
                "question": "🦏 Which wildlife would you most like to see in Namibia?",
                "options": [
                    "Lions & Cheetahs",
                    "Desert Elephants",
                    "Black Rhinos",
                    "Giraffes & Zebras",
                    "Marine Life (Seals, Dolphins)"
                ]
            },
            {
                "question": "🏜️ Best time to visit Namibia?",
                "options": [
                    "May-June (Early Dry Season)",
                    "July-September (Peak Safari)",
                    "October-November (Hot & Dry)",
                    "December-March (Green Season)",
                    "April (Autumn)"
                ]
            },
            {
                "question": "🍽️ Which Namibian dish would you try first?",
                "options": [
                    "Braai (BBQ)",
                    "Biltong (Dried Meat)",
                    "Kapana (Street Food)",
                    "Potjiekos (Stew)",
                    "Vetkoek (Fried Bread)"
                ]
            }
        ]
        
        return random.choice(polls)
    
    def generate_discussion_topic(self) -> str:
        """Generate engaging discussion topics"""
        topics = [
            "💭 *Discussion Topic:*\n\n**If you could spend one week anywhere in Namibia, where would you go and why?**\n\n🏞️ Etosha for wildlife?\n🏜️ Namib Desert for solitude?\n🏖️ Swakopmund for adventure?\n\nShare your dream Namibia itinerary! 👇",
            
            "💭 *Let's Discuss:*\n\n**What makes Namibia unique compared to other African countries?**\n\nThink about:\n🦁 Wildlife\n🏜️ Landscapes\n👥 Culture\n🏛️ History\n\nWhat stands out to you? 🤔",
            
            "💭 *Question for the Group:*\n\n**If you could improve ONE thing about tourism in Namibia, what would it be?**\n\n📱 Better connectivity?\n🏨 More accommodations?\n✈️ Intercity transport?\n🗺️ Better infrastructure?\n\nYour ideas matter! 💡",
            
            "💭 *Discussion Time:*\n\n**Namibia's real estate market - investment opportunity or just hype?**\n\n🏠 Property prices reasonable?\n📈 Growth potential?\n🌍 Foreign investment?\n\nInvestors, what do you think? 💼",
            
            "💭 *Hot Topic:*\n\n**Should Namibia focus more on luxury tourism or budget travel?**\n\n💎 High-end experiences\nvs\n🎒 Backpacker-friendly\n\nWhat brings more benefits? Debate! 🗣️"
        ]
        
        return random.choice(topics)
    
    def should_send_weather(self, chat_id: str) -> bool:
        """Check if weather update should be sent"""
        # Send weather once per day per chat
        key = f"weather_{chat_id}"
        last_time = self.last_brainstorm.get(key)
        
        if not last_time:
            self.last_brainstorm[key] = datetime.now()
            return True
        
        if datetime.now() - last_time > timedelta(hours=24):
            self.last_brainstorm[key] = datetime.now()
            return True
        
        return False
    
    def should_tell_story(self, chat_id: str) -> bool:
        """Check if story should be told"""
        key = f"story_{chat_id}"
        last_time = self.last_story.get(key)
        
        if not last_time:
            self.last_story[key] = datetime.now()
            return True
        
        # Tell story once every 6 hours
        if datetime.now() - last_time > timedelta(hours=6):
            self.last_story[key] = datetime.now()
            return True
        
        return False
    
    def should_send_poll(self, chat_id: str) -> bool:
        """Check if poll should be sent"""
        key = f"poll_{chat_id}"
        last_time = self.last_poll.get(key)
        
        if not last_time:
            self.last_poll[key] = datetime.now()
            return True
        
        # Send poll once every 8 hours
        if datetime.now() - last_time > timedelta(hours=8):
            self.last_poll[key] = datetime.now()
            return True
        
        return False
    
    def get_random_fact(self) -> str:
        """Get random interesting facts about Namibia"""
        facts = [
            "🌟 *Did You Know?*\n\nNamibia has the world's oldest desert - Namib Desert is 55-80 million years old! 🏜️",
            "🌟 *Fun Fact:*\n\nNamibia was the first African country to incorporate environmental protection into its constitution! 🌍",
            "🌟 *Amazing:*\n\nNamibia has more cheetahs than any other country in the world! 🐆",
            "🌟 *Did You Know?*\n\nThe Skeleton Coast has over 1,000 shipwrecks along its shores! 🚢",
            "🌟 *Incredible:*\n\nNamibia has the second-lowest population density in the world - only 3 people per km²! 👥",
            "🌟 *Fun Fact:*\n\nWelwitschia mirabilis plants in Namibia can live for over 2,000 years! 🌱",
            "🌟 *Amazing:*\n\nNamibia's sand dunes at Sossusvlei are the tallest in the world - up to 380 meters! 🏔️",
            "🌟 *Did You Know?*\n\nNamibia was the first country in the world to include protection of the environment in its constitution! 📜"
        ]
        return random.choice(facts)
