"""Simple chat service without OpenAI for testing"""
import re
from typing import Dict, List, Optional
import logging
from difflib import get_close_matches
from app.schemas.booking_schema import BookingIntent, BookingSlots, RoomType, SLOT_PROMPTS, AVAILABLE_LOCATIONS, get_dynamic_slot_prompts

logger = logging.getLogger(__name__)


class SimpleChatService:
    """Simple rule-based chat service as fallback"""
    
    def extract_booking_intent(self, message: str, context: List[Dict] = None) -> BookingIntent:
        """Extract intent using simple rules"""
        message_lower = message.lower()
        
        # Check if we're in an active booking conversation
        if context and len(context) > 0:
            # Look for booking intent in recent messages
            for msg in context[-4:]:  # Check last 4 messages
                if msg.get('role') == 'assistant' and any(phrase in msg.get('content', '').lower() for phrase in 
                    ['which location', 'what type of', 'how many people', 'what date', 'what time']):
                    # Assistant was asking for booking details, so this is likely a booking response
                    return BookingIntent.BOOK_ROOM
        
        # Booking keywords
        if any(word in message_lower for word in ['book', 'reserve', 'need', 'want', 'schedule']):
            if any(word in message_lower for word in ['room', 'space', 'office', 'desk', 'meeting']):
                return BookingIntent.BOOK_ROOM
        
        # Cancel keywords
        if any(word in message_lower for word in ['cancel', 'remove', 'delete']):
            return BookingIntent.CANCEL_BOOKING
        
        # Check availability
        if any(word in message_lower for word in ['available', 'availability', 'free']):
            return BookingIntent.CHECK_AVAILABILITY
        
        # List bookings
        if any(word in message_lower for word in ['my bookings', 'show bookings', 'list bookings']):
            return BookingIntent.LIST_BOOKINGS
        
        # Check if message contains location/booking details
        locations = ['salt lake city', 'new york', 'san francisco', 'chicago', 'los angeles']
        if any(loc in message_lower for loc in locations) and context:
            # If they're mentioning a location and we have context, likely booking
            return BookingIntent.BOOK_ROOM
        
        return BookingIntent.UNKNOWN
    
    def extract_booking_slots(self, message: str, current_slots: BookingSlots) -> BookingSlots:
        """Extract booking information using patterns with fuzzy matching"""
        message_lower = message.lower()
        
        # Extract location - Try dynamic OfficeRND data first
        try:
            from app.services.officernd_service import officernd_service
            
            # Check if any word in the message matches a location
            words = message.split()
            for word in words:
                if len(word) >= 3:  # Skip very short words
                    match = officernd_service.match_location(word)
                    if match:
                        current_slots.location = match.get('name')
                        logger.info(f"Found OfficeRND location match: {current_slots.location}")
                        location_found = True
                        break
        except Exception as e:
            logger.warning(f"Failed to use OfficeRND service: {str(e)}")
        
        # Fallback to static location matching
        locations_lower = [loc.lower() for loc in AVAILABLE_LOCATIONS]
        location_found = False
        
        # First try exact matches
        for i, loc in enumerate(locations_lower):
            if loc in message_lower:
                current_slots.location = AVAILABLE_LOCATIONS[i]
                location_found = True
                logger.info(f"Found exact location match: {AVAILABLE_LOCATIONS[i]}")
                break
        
        # Check for common misspellings and variations
        if not location_found:
            location_variations = {
                'san fransisco': 'San Francisco',
                'sanfrancisco': 'San Francisco',
                'san fran': 'San Francisco',
                'salt lake sity': 'Salt Lake City',
                'saltlake city': 'Salt Lake City',
                'salt lake': 'Salt Lake City',
                'newyork': 'New York',
                'new yrok': 'New York',
                'losangeles': 'Los Angeles',
                'los angles': 'Los Angeles',
            }
            
            for variant, correct in location_variations.items():
                if variant in message_lower:
                    current_slots.location = correct
                    location_found = True
                    logger.info(f"Found location variant: '{variant}' -> '{correct}'")
                    break
        
        # If no exact match, try fuzzy matching on individual words
        if not location_found:
            words = message_lower.split()
            for word in words:
                # Check if word is long enough to be meaningful
                if len(word) >= 3:
                    # Try fuzzy matching against each location
                    for i, loc in enumerate(locations_lower):
                        loc_words = loc.split()
                        for loc_word in loc_words:
                            # Check similarity between words
                            if self._is_similar(word, loc_word, threshold=0.8):
                                current_slots.location = AVAILABLE_LOCATIONS[i]
                                location_found = True
                                logger.info(f"Found fuzzy location match: '{word}' -> '{AVAILABLE_LOCATIONS[i]}'")
                                break
                        if location_found:
                            break
                if location_found:
                    break
        
        # Also check for location abbreviations
        if not location_found:
            abbreviations = {
                'nyc': 'New York',
                'ny': 'New York',
                'sf': 'San Francisco',
                'la': 'Los Angeles',
                'chi': 'Chicago',
                'slc': 'Salt Lake City'
            }
            for abbr, full_name in abbreviations.items():
                if abbr in message_lower.split():
                    current_slots.location = full_name
                    logger.info(f"Found location abbreviation: '{abbr}' -> '{full_name}'")
                    break
        
        # Extract room type - check multiple variations
        room_type_patterns = {
            RoomType.MEETING_ROOM: ['meeting room', 'meeting space', 'meet room', 'small room'],
            RoomType.CONFERENCE_ROOM: ['conference', 'conf room', 'large meeting', 'big room'],
            RoomType.PRIVATE_OFFICE: ['office', 'private room', 'quiet room', 'private space'],
            RoomType.HOT_DESK: ['desk', 'hot desk', 'workspace', 'workstation'],
            RoomType.PHONE_BOOTH: ['phone booth', 'call room', 'phone room'],
            RoomType.EVENT_SPACE: ['event space', 'event room', 'presentation']
        }
        
        for room_type, patterns in room_type_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    current_slots.room_type = room_type
                    logger.info(f"Found room type: {room_type}")
                    break
        
        # Extract capacity - look for various patterns
        capacity_patterns = [
            r'(\d+)\s*(?:people|person|ppl|guests?)',
            r'for\s*(\d+)',
            r'party\s*of\s*(\d+)',
            r'group\s*of\s*(\d+)',
            r'(\d+)\s*(?:of us|total)'
        ]
        
        for pattern in capacity_patterns:
            capacity_match = re.search(pattern, message_lower)
            if capacity_match:
                current_slots.capacity = int(capacity_match.group(1))
                logger.info(f"Found capacity: {capacity_match.group(1)}")
                break
        
        # Extract date - handle various formats
        date_patterns = [
            # MM-DD-YYYY, MM/DD/YYYY, etc.
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            # Written dates like "Jan 5" or "January 5th"
            r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{1,2})',
            # Day references
            r'(tomorrow|today|yesterday)',
            # Weekday references
            r'((?:next\s*)?(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*)',
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, message_lower, re.IGNORECASE)
            if date_match:
                current_slots.date = date_match.group(1)
                logger.info(f"Found date: {date_match.group(1)}")
                break
        
        # Extract time - handle various formats including time ranges
        # First check for time ranges like "2pm-4pm"
        time_range_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*[-–]\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', message_lower, re.IGNORECASE)
        if time_range_match:
            start_time = time_range_match.group(1).strip()
            end_time = time_range_match.group(2).strip()
            current_slots.time = start_time
            # Calculate duration from time range
            if not current_slots.duration:
                current_slots.duration = "2 hours"  # Default, could be calculated
            logger.info(f"Found time range: {start_time} to {end_time}")
        else:
            # Single time patterns
            time_patterns = [
                r'(\d{1,2}:\d{2}\s*(?:am|pm)?)',  # Match HH:MM format first
                r'(\d{1,2}\s*(?:am|pm))',         # Then simple hour + am/pm
                r'(\d{1,2})\s*o[\'\']*clock',
                r'(noon|midnight|morning|afternoon|evening)'
            ]
            
            for pattern in time_patterns:
                time_match = re.search(pattern, message_lower, re.IGNORECASE)
                if time_match:
                    current_slots.time = time_match.group(0).strip()
                    logger.info(f"Found time: {time_match.group(0).strip()}")
                    break
        
        # Extract duration - handle various formats
        duration_patterns = {
            r'(\d+)\s*(?:hour|hr)s?': lambda m: f"{m.group(1)} hour{'s' if int(m.group(1)) > 1 else ''}",
            r'(\d+)\s*min(?:ute)?s?': lambda m: f"{m.group(1)} minutes",
            r'half\s*(?:a\s*)?day': lambda m: "half day",
            r'all\s*day': lambda m: "all day",
            r'(\d+)\s*(?:and\s*a\s*)?half\s*hours?': lambda m: f"{m.group(1)}.5 hours"
        }
        
        for pattern, formatter in duration_patterns.items():
            duration_match = re.search(pattern, message_lower, re.IGNORECASE)
            if duration_match:
                current_slots.duration = formatter(duration_match)
                logger.info(f"Found duration: {current_slots.duration}")
                break
        
        return current_slots
    
    def _is_similar(self, word1: str, word2: str, threshold: float = 0.8) -> bool:
        """Check if two words are similar using simple character matching"""
        # Handle very short words
        if len(word1) < 3 or len(word2) < 3:
            return word1 == word2
        
        # Calculate similarity ratio
        matches = sum(1 for a, b in zip(word1, word2) if a == b)
        max_len = max(len(word1), len(word2))
        ratio = matches / max_len
        
        # Also check if one word contains the other
        if word1 in word2 or word2 in word1:
            return True
        
        return ratio >= threshold
    
    def generate_response(self, 
                         message: str, 
                         intent: BookingIntent,
                         slots: BookingSlots,
                         conversation_history: List[Dict]) -> str:
        """Generate response based on intent and slots"""
        
        if intent == BookingIntent.BOOK_ROOM:
            if slots.is_complete():
                return (f"Perfect! I'll book your {slots.room_type.replace('_', ' ')} "
                       f"in {slots.location} for {slots.capacity} people "
                       f"on {slots.date} at {slots.time}. "
                       f"I'll send you a confirmation shortly.")
            else:
                # Ask for first missing slot
                missing = slots.missing_slots()
                if missing:
                    dynamic_prompts = get_dynamic_slot_prompts()
                    return dynamic_prompts.get(missing[0], f"Please provide the {missing[0]}.")
        
        elif intent == BookingIntent.CANCEL_BOOKING:
            return "I can help you cancel a booking. Please provide your booking reference or details."
        
        elif intent == BookingIntent.CHECK_AVAILABILITY:
            return "I can check availability. What type of space are you looking for and when?"
        
        elif intent == BookingIntent.LIST_BOOKINGS:
            return "You currently have no bookings. Would you like to make a new booking?"
        
        else:
            return ("I can help you book meeting rooms and workspaces. "
                   "Just tell me what you need, like 'Book a meeting room for 5 people tomorrow at 2 PM'.")