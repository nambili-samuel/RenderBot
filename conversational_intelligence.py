"""
Advanced Conversational Intelligence for Eva Geises
Sophisticated reasoning, emotional intelligence, and communication patterns
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class ConversationalIntelligence:
    """Advanced AI reasoning and communication patterns"""
    
    def __init__(self):
        self.conversation_history = {}  # Track context per user
        self.user_tone = {}  # Detect user communication style
        self.confidence_threshold = 0.7
        
    def analyze_user_intent(self, message: str, user_id: int) -> Dict:
        """
        Analyze user's intent, tone, and emotional state
        Returns: {intent, tone, emotion, confidence}
        """
        msg_lower = message.lower().strip()
        
        # Detect tone
        tone = self._detect_tone(msg_lower, message)
        
        # Detect emotion
        emotion = self._detect_emotion(msg_lower)
        
        # Detect intent
        intent = self._detect_intent(msg_lower)
        
        # Calculate confidence
        confidence = self._calculate_confidence(message, intent)
        
        return {
            'intent': intent,
            'tone': tone,
            'emotion': emotion,
            'confidence': confidence,
            'is_vague': self._is_vague_question(msg_lower),
            'needs_clarification': self._needs_clarification(msg_lower),
            'is_repeat': self._is_repeat_question(user_id, message),
            'engagement_level': self._assess_engagement(msg_lower)
        }
    
    def _detect_tone(self, msg_lower: str, original: str) -> str:
        """Detect user's communication tone"""
        # Enthusiastic
        if any(x in msg_lower for x in ['!', 'wow', 'amazing', 'awesome', 'love']):
            if original.count('!') >= 2 or original.isupper():
                return 'very_enthusiastic'
            return 'enthusiastic'
        
        # Casual/relaxed
        if any(x in msg_lower for x in ['lol', 'haha', 'hey', 'sup', 'cool', 'nice']):
            return 'casual'
        
        # Frustrated/impatient
        if any(x in msg_lower for x in ['why not', 'still', 'again', 'ugh', 'seriously']):
            return 'frustrated'
        
        # Uncertain/hesitant
        if any(x in msg_lower for x in ['maybe', 'hmm', 'idk', 'not sure', '...']):
            return 'uncertain'
        
        # Formal/polite
        if any(x in msg_lower for x in ['please', 'could you', 'would you', 'kindly']):
            return 'formal'
        
        return 'neutral'
    
    def _detect_emotion(self, msg_lower: str) -> str:
        """Detect emotional state"""
        # Excitement
        if any(x in msg_lower for x in ['excited', 'can\'t wait', 'amazing', 'wonderful']):
            return 'excited'
        
        # Frustration
        if any(x in msg_lower for x in ['frustrated', 'annoying', 'disappointed', 'tired of']):
            return 'frustrated'
        
        # Confusion
        if any(x in msg_lower for x in ['confused', 'don\'t understand', 'what do you mean', 'huh']):
            return 'confused'
        
        # Curiosity
        if '?' in msg_lower and any(x in msg_lower for x in ['how', 'why', 'what', 'when']):
            return 'curious'
        
        # Satisfaction
        if any(x in msg_lower for x in ['thanks', 'thank you', 'perfect', 'great', 'helped']):
            return 'satisfied'
        
        return 'neutral'
    
    def _detect_intent(self, msg_lower: str) -> str:
        """Detect what user wants"""
        # Information seeking
        if '?' in msg_lower or any(msg_lower.startswith(x) for x in ['what', 'where', 'when', 'how', 'why', 'who']):
            return 'information_seeking'
        
        # Comparison
        if any(x in msg_lower for x in ['vs', 'versus', 'compared to', 'better than', 'difference between']):
            return 'comparison'
        
        # Recommendation
        if any(x in msg_lower for x in ['recommend', 'suggest', 'best', 'should i', 'which one']):
            return 'recommendation'
        
        # Problem/issue
        if any(x in msg_lower for x in ['problem', 'issue', 'doesn\'t work', 'not working', 'help']):
            return 'problem_solving'
        
        # Casual chat
        if any(x in msg_lower for x in ['hi', 'hello', 'hey', 'what\'s up', 'how are you']):
            return 'social'
        
        # Feedback
        if any(x in msg_lower for x in ['lol', 'hmm', 'ok', 'i see', 'alright', 'got it']):
            return 'feedback'
        
        return 'general_query'
    
    def _calculate_confidence(self, message: str, intent: str) -> float:
        """Calculate bot's confidence in understanding query"""
        confidence = 0.8  # Base confidence
        
        msg_lower = message.lower()
        
        # Clear questions increase confidence
        if '?' in message and intent == 'information_seeking':
            confidence += 0.1
        
        # Vague queries decrease confidence
        if any(x in msg_lower for x in ['stuff', 'things', 'something', 'anything', 'whatever']):
            confidence -= 0.3
        
        # Very short messages decrease confidence
        if len(message.split()) <= 2:
            confidence -= 0.2
        
        # Specific location/topic names increase confidence
        namibia_terms = ['namibia', 'etosha', 'windhoek', 'sossusvlei', 'swakopmund', 'himba']
        if any(term in msg_lower for term in namibia_terms):
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _is_vague_question(self, msg_lower: str) -> bool:
        """Check if question is too vague"""
        vague_patterns = [
            'tell me about namibia',
            'what about namibia',
            'anything about',
            'everything about',
            'info about',
            'stuff about',
            'things about'
        ]
        
        # Single word questions are vague
        if len(msg_lower.split()) <= 2 and '?' in msg_lower:
            return True
        
        return any(pattern in msg_lower for pattern in vague_patterns)
    
    def _needs_clarification(self, msg_lower: str) -> bool:
        """Check if we should ask for clarification"""
        unclear_terms = ['stuff', 'things', 'something', 'it', 'there', 'that']
        
        # Check if query is ambiguous
        if any(term in msg_lower.split() for term in unclear_terms):
            return True
        
        # Multiple questions in one
        if msg_lower.count('?') > 1:
            return True
        
        return False
    
    def _is_repeat_question(self, user_id: int, message: str) -> bool:
        """Check if user is repeating a question (didn't feel answered)"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
            return False
        
        # Check last 3 messages
        recent = self.conversation_history[user_id][-3:]
        
        # Similar message = repeat
        for prev_msg in recent:
            similarity = self._calculate_similarity(prev_msg.lower(), message.lower())
            if similarity > 0.6:
                return True
        
        return False
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _assess_engagement(self, msg_lower: str) -> str:
        """Assess user's engagement level"""
        # Disengaged signals
        if any(x in msg_lower for x in ['ok', 'hmm', 'k', 'alright', 'whatever']):
            return 'low'
        
        # High engagement
        if len(msg_lower.split()) > 10 or '!' in msg_lower:
            return 'high'
        
        return 'medium'
    
    def generate_intelligent_response(self, message: str, user_id: int, 
                                     search_results: List[Dict], 
                                     response_type: str) -> str:
        """
        Generate contextually intelligent response
        Applies all reasoning frameworks and communication patterns
        """
        # Analyze user intent
        analysis = self.analyze_user_intent(message, user_id)
        
        # Track conversation
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        self.conversation_history[user_id].append(message)
        
        # Keep only last 5 messages
        if len(self.conversation_history[user_id]) > 5:
            self.conversation_history[user_id] = self.conversation_history[user_id][-5:]
        
        # Handle based on analysis
        response = self._craft_response(message, analysis, search_results, response_type)
        
        return response
    
    def _craft_response(self, message: str, analysis: Dict, 
                       search_results: List[Dict], response_type: str) -> str:
        """Craft intelligent response based on analysis"""
        
        # Handle low engagement - shorten and sharpen
        if analysis['engagement_level'] == 'low':
            return self._handle_low_engagement(message, analysis, search_results)
        
        # Handle repeat questions - user didn't feel answered
        if analysis['is_repeat']:
            return self._handle_repeat_question(message, search_results)
        
        # Handle vague questions - ask ONE clarifying question
        if analysis['is_vague']:
            return self._handle_vague_question(message)
        
        # Handle low confidence - express uncertainty
        if analysis['confidence'] < self.confidence_threshold:
            return self._handle_low_confidence(message, search_results)
        
        # Handle emotions appropriately
        if analysis['emotion'] != 'neutral':
            return self._handle_emotional_query(message, analysis, search_results)
        
        # Match user's tone
        return self._match_tone_response(message, analysis, search_results, response_type)
    
    def _handle_low_engagement(self, message: str, analysis: Dict, 
                               search_results: List[Dict]) -> str:
        """User said 'hmm', 'ok', 'k' - shorten and sharpen"""
        msg_lower = message.lower().strip()
        
        # Acknowledge and ask if they need something specific
        if msg_lower in ['ok', 'k', 'alright']:
            return "👍 Got it! Let me know if you need anything specific about Namibia - I'm here to help!"
        
        if msg_lower in ['hmm', 'hm', 'umm']:
            return "🤔 Not quite what you were looking for? What specific aspect of Namibia interests you?"
        
        if 'whatever' in msg_lower:
            return "No worries! I'm here when you need Namibia info. 🇳🇦"
        
        return "✨ Anything else about Namibia I can help with?"
    
    def _handle_repeat_question(self, message: str, search_results: List[Dict]) -> str:
        """User is repeating - they didn't feel answered"""
        if not search_results:
            return (
                "I apologize - let me try to answer more clearly.\n\n"
                "Could you rephrase what you're looking for? That way I can give you "
                "exactly the information you need about Namibia. 🎯"
            )
        
        # Give more specific answer this time
        result = search_results[0]
        response = f"Let me be more specific:\n\n"
        response += f"*{result['topic']}*\n"
        response += f"{result['content']}\n\n"
        response += "Is this what you were looking for? If not, what specific detail do you need? 🤔"
        
        return response
    
    def _handle_vague_question(self, message: str) -> str:
        """Ask ONE clarifying question for vague queries"""
        msg_lower = message.lower()
        
        if 'tell me about namibia' in msg_lower or 'what about namibia' in msg_lower:
            return (
                "Namibia is fascinating! 🇳🇦 What interests you most?\n\n"
                "• Wildlife & safaris 🦁\n"
                "• Desert landscapes 🏜️\n"
                "• Culture & people 👥\n"
                "• Travel tips ✈️\n"
                "• Real estate 🏠"
            )
        
        if 'namibia?' == msg_lower or 'tell me' in msg_lower:
            return "I'd love to help! What aspect of Namibia are you curious about? (Wildlife, places to visit, culture, properties...) 🤔"
        
        return "Could you be more specific? That helps me give you exactly what you need! 😊"
    
    def _handle_low_confidence(self, message: str, search_results: List[Dict]) -> str:
        """Express uncertainty when confidence < 0.7"""
        if search_results:
            result = search_results[0]
            return (
                f"I'm not 100% sure I understood your question correctly, but here's what might help:\n\n"
                f"*{result['topic']}*\n"
                f"{result['content']}\n\n"
                f"Is this what you were looking for? 🤔"
            )
        
        return (
            "I'm not entirely sure I understood your question. 🤔\n\n"
            "Could you rephrase it? For example:\n"
            "• \"Where is Etosha?\"\n"
            "• \"What's the best time to visit Namibia?\"\n"
            "• \"Show me properties in Windhoek\""
        )
    
    def _handle_emotional_query(self, message: str, analysis: Dict, 
                                search_results: List[Dict]) -> str:
        """Handle emotional states appropriately"""
        emotion = analysis['emotion']
        
        # Excitement - amplify, don't neutralize
        if emotion == 'excited':
            if search_results:
                result = search_results[0]
                return (
                    f"Yes! 🎉 {result['topic']} is amazing!\n\n"
                    f"{result['content']}\n\n"
                    f"You're going to love it! Want to know more? 🌟"
                )
            return "Your enthusiasm is contagious! 🎉 What about Namibia excites you most?"
        
        # Frustration - validate first, then help
        if emotion == 'frustrated':
            return (
                "I understand your frustration. 😔 Let me help you find what you need.\n\n"
                "What specific information about Namibia are you looking for? I'll get you a clear answer. 🎯"
            )
        
        # Confusion - slow down, be gentle
        if emotion == 'confused':
            return (
                "No worries - let's clear this up! 🤝\n\n"
                "What would you like to know about Namibia? Take your time, "
                "I'm here to help make it simple. 😊"
            )
        
        # Satisfaction - acknowledge and offer more
        if emotion == 'satisfied':
            return "Glad I could help! 😊 Anything else about Namibia you're curious about?"
        
        return self._match_tone_response(message, analysis, search_results, 'search')
    
    def _match_tone_response(self, message: str, analysis: Dict, 
                            search_results: List[Dict], response_type: str) -> str:
        """Match user's tone and energy"""
        tone = analysis['tone']
        
        if not search_results:
            return self._no_results_response(tone)
        
        result = search_results[0]
        
        # Very enthusiastic - match energy
        if tone == 'very_enthusiastic':
            response = f"YES! 🎉 {result['topic']}!\n\n"
            response += f"{result['content']}\n\n"
            response += "AMAZING, right?! Want to know more? 🚀"
            return response
        
        # Enthusiastic - upbeat
        if tone == 'enthusiastic':
            response = f"Great question! 😊\n\n"
            response += f"*{result['topic']}*\n{result['content']}\n\n"
            response += "Exciting stuff! Anything else? ✨"
            return response
        
        # Casual - relaxed and friendly
        if tone == 'casual':
            response = f"*{result['topic']}*\n\n"
            response += f"{result['content']}\n\n"
            response += "Cool, right? 😎"
            return response
        
        # Formal - professional
        if tone == 'formal':
            response = f"*{result['topic']}*\n\n"
            response += f"{result['content']}\n\n"
            if len(search_results) > 1:
                response += "Would you like additional information on related topics?"
            return response
        
        # Neutral - balanced
        response = f"*{result['topic']}*\n\n"
        response += f"{result['content']}\n\n"
        
        # Offer related if available
        if len(search_results) > 1:
            response += "💡 Want to know more about this topic?"
        
        return response
    
    def _no_results_response(self, tone: str) -> str:
        """Handle no results based on tone"""
        if tone == 'very_enthusiastic':
            return "Ooh, great question! 🤔 I don't have that specific info, but try /menu to explore what I do know! 🚀"
        
        if tone == 'casual':
            return "Hmm, not sure about that one 🤔 Try /menu to browse topics, or ask something else!"
        
        if tone == 'formal':
            return (
                "I apologize, but I don't have information on that specific topic at the moment. "
                "Please use /menu to explore available topics, or rephrase your question."
            )
        
        return (
            "I don't have specific information on that. 🤔\n\n"
            "Try:\n"
            "• /menu - Browse all topics\n"
            "• Ask about Etosha, Sossusvlei, or Wildlife\n"
            "• /properties - See real estate listings"
        )
    
    def get_clarification_question(self, topic: str) -> str:
        """Generate ONE good clarifying question"""
        clarifications = {
            'wildlife': "Which animals interest you most? Lions, elephants, cheetahs, or desert-adapted species? 🦁",
            'visit': "Are you asking about the best time to visit, or specific places to go? 🤔",
            'cost': "Are you asking about safari costs, accommodation, or general travel budget? 💰",
            'safari': "Which type of safari? Self-drive, guided tour, or luxury lodge experience? 🚗",
            'culture': "Which aspect of culture? The Himba people, traditional customs, or modern Namibian life? 👥",
            'property': "Are you looking to buy, rent, or invest in real estate? 🏠"
        }
        
        topic_lower = topic.lower()
        
        for key, question in clarifications.items():
            if key in topic_lower:
                return question
        
        return "What specific aspect would you like to know about? 🤔"
    
    def format_natural_response(self, content: str, query: str, source_type: str) -> str:
        """
        Format response in natural, conversational way
        
        Args:
            content: The response content to format
            query: The original user query
            source_type: Type of source (document, knowledge_base, etc)
        
        Returns:
            Formatted natural response
        """
        # Clean up content
        content = content.strip()
        
        # Remove document headers if source is document
        if source_type == "document":
            # Remove all-caps headings
            lines = content.split('\n')
            filtered_lines = []
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.isupper() and len(line_stripped.split()) > 3:
                    filtered_lines.append(line_stripped)
            content = '\n'.join(filtered_lines)
            
            # Remove specific document headings
            unwanted_starts = ["WELCOME TO", "INTRODUCTION", "TABLE OF CONTENTS", "CHAPTER", "SECTION"]
            for unwanted in unwanted_starts:
                if content.startswith(unwanted):
                    # Find the first period and start from there
                    period_idx = content.find('.')
                    if period_idx > 0:
                        content = content[period_idx + 1:].strip()
        
        # Add natural introduction based on query
        query_lower = query.lower()
        
        if "self-drive" in query_lower or "road trip" in query_lower or "drive" in query_lower:
            intro = "🚗 For self-drive adventures in Namibia:\n\n"
        elif "itinerary" in query_lower or "plan" in query_lower or "schedule" in query_lower:
            intro = "🗺️ Here's a suggested travel plan:\n\n"
        elif "weather" in query_lower or "climate" in query_lower:
            intro = "🌤️ About Namibia's weather:\n\n"
        elif "visa" in query_lower or "requirements" in query_lower or "entry" in query_lower:
            intro = "📋 Entry requirements:\n\n"
        elif "currency" in query_lower or "money" in query_lower or "cash" in query_lower:
            intro = "💰 Currency information:\n\n"
        elif "?" in query:
            # For questions, start naturally
            if query_lower.startswith('what'):
                intro = "🇳🇦 "
            elif query_lower.startswith('where'):
                intro = "📍 "
            elif query_lower.startswith('when'):
                intro = "📅 "
            elif query_lower.startswith('why'):
                intro = "🤔 "
            elif query_lower.startswith('how'):
                intro = "🔧 "
            elif query_lower.startswith('who'):
                intro = "👤 "
            elif query_lower.startswith('which'):
                intro = "🎯 "
            else:
                intro = ""
        else:
            intro = ""
        
        # Limit response length
        if len(content) > 400:
            # Find a good breaking point
            sentences = re.split(r'(?<=[.!?])\s+', content)
            limited_content = []
            char_count = 0
            
            for sentence in sentences:
                if char_count + len(sentence) < 350:
                    limited_content.append(sentence)
                    char_count += len(sentence)
                else:
                    break
            
            if limited_content:
                content = ' '.join(limited_content)
                if not content.endswith(('.', '!', '?')):
                    content += '...'
            else:
                content = content[:350] + '...'
        
        return intro + content
