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
            RoomType.HOT_DESK: ['hotdesk', 'hot desk', 'hot-desk', 'desk', 'workspace', 'workstation'],
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
        
        # Extract date and time - handle various formats
        # First check for complete datetime ranges like "Dec 5 2pm to 4pm" or "5/12/2025 1pm-3pm"
        datetime_range_patterns = [
            # Date with time range: "Dec 5 2pm to 4pm", "5/12 from 2pm to 4pm"
            r'(\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:,?\s*\d{4})?)\s+(?:from\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-|–)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
            # Numeric date with time range: "12/5/2025 2pm-4pm"
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-|–)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
            # Tomorrow/today with time range
            r'(tomorrow|today)\s+(?:from\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-|–)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)'
        ]
        
        datetime_found = False
        for pattern in datetime_range_patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                current_slots.start_date = match.group(1)
                current_slots.start_time = match.group(2)
                current_slots.end_date = match.group(1)  # Same day booking
                current_slots.end_time = match.group(3)
                # Also set old fields for compatibility
                current_slots.date = match.group(1)
                current_slots.time = match.group(2)
                datetime_found = True
                logger.info(f"Found datetime range: {match.group(1)} from {match.group(2)} to {match.group(3)}")
                break
        
        if not datetime_found:
            # Check for time ranges without date (just "2pm-4pm")
            time_range_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*[-–]\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', message_lower, re.IGNORECASE)
            if time_range_match:
                current_slots.start_time = time_range_match.group(1).strip()
                current_slots.end_time = time_range_match.group(2).strip()
                # Also set old fields
                current_slots.time = current_slots.start_time
                logger.info(f"Found time range: {current_slots.start_time} to {current_slots.end_time}")
            else:
                # Extract date separately
                date_patterns = [
                    # MM-DD-YYYY, MM/DD/YYYY, etc.
                    r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    # Written dates like "Jan 5" or "January 5th"
                    r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{1,2}(?:,?\s*\d{4})?)',
                    # Day references
                    r'(tomorrow|today|yesterday)',
                    # Weekday references
                    r'((?:next\s*)?(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*)',
                ]
                
                for pattern in date_patterns:
                    date_match = re.search(pattern, message_lower, re.IGNORECASE)
                    if date_match:
                        current_slots.date = date_match.group(1)
                        current_slots.start_date = date_match.group(1)
                        logger.info(f"Found date: {date_match.group(1)}")
                        break
                
                # Extract single time
                time_patterns = [
                    r'(\d{1,2}:\d{2}\s*(?:am|pm)?)',
                    r'(\d{1,2}\s*(?:am|pm))',
                    r'(\d{1,2})\s*o[\'\']*clock',
                    r'(noon|midnight|morning|afternoon|evening)'
                ]
                
                for pattern in time_patterns:
                    time_match = re.search(pattern, message_lower, re.IGNORECASE)
                    if time_match:
                        current_slots.time = time_match.group(0).strip()
                        current_slots.start_time = time_match.group(0).strip()
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
                # Build confirmation message
                response = "Perfect! Let me confirm your booking details:\n\n"
                
                if slots.room_type:
                    room_type_str = slots.room_type.value.replace('_', ' ').title()
                    response += f"• Space: {room_type_str} "
                
                if slots.location:
                    response += f"at our {slots.location} office\n"
                
                if slots.capacity:
                    people_str = "person" if slots.capacity == 1 else "people"
                    response += f"• Capacity: {slots.capacity} {people_str}\n"
                
                # Show date/time info
                if slots.start_date and slots.start_time and slots.end_time:
                    if slots.start_date == slots.end_date or not slots.end_date:
                        response += f"• Date & Time: {slots.start_date} from {slots.start_time} to {slots.end_time}\n"
                    else:
                        response += f"• Date & Time: From {slots.start_date} at {slots.start_time} to {slots.end_date} at {slots.end_time}\n"
                elif slots.date and slots.time:
                    response += f"• Date & Time: {slots.date} at {slots.time}"
                    if slots.duration:
                        response += f" (duration: {slots.duration})"
                    response += "\n"
                
                response += "\nIs this correct? Please reply 'yes' to confirm your booking or let me know what needs to be changed."
                
                return response
            else:
                # Ask for all missing information at once
                missing = slots.missing_slots()
                if missing:
                    return self._build_missing_info_prompt(missing, slots)
        
        elif intent == BookingIntent.CANCEL_BOOKING:
            return "I can help you cancel a booking. Please provide your booking reference or details."
        
        elif intent == BookingIntent.CHECK_AVAILABILITY:
            return "I can check availability. What type of space are you looking for and when?"
        
        elif intent == BookingIntent.LIST_BOOKINGS:
            return "You currently have no bookings. Would you like to make a new booking?"
        
        else:
            return ("I can help you book meeting rooms and workspaces. "
                   "Just tell me what you need, like 'Book a meeting room for 5 people tomorrow at 2 PM'.")
    
    def _build_missing_info_prompt(self, missing: List[str], slots: BookingSlots) -> str:
        """Build a conversational prompt for missing information"""
        try:
            from app.services.officernd_service import officernd_service
            
            # Start with a friendly opening based on what's missing
            if len(missing) >= 4:
                prompt = "I'd be happy to help you book a space! To find the perfect spot for you, could you tell me:\n\n"
            elif len(missing) == 3:
                prompt = "Great! I just need a few more details:\n\n"
            elif len(missing) == 2:
                prompt = "Almost there! I just need:\n\n"
            else:
                prompt = "Perfect! One last thing:\n\n"
            
            # Build conversational questions
            questions = []
            
            if "location" in missing:
                locations = officernd_service.get_location_suggestions()
                questions.append(f"Which office location works best for you? We have spaces in {locations}")
            
            if "room_type" in missing:
                room_types = officernd_service.get_resource_type_suggestions()
                questions.append(f"What type of space do you need? We offer {room_types}")
            
            if "capacity" in missing:
                questions.append("How many people will be joining?")
            
            if "datetime" in missing:
                questions.append("When do you need the space? Please include both start and end times (e.g., 'Dec 5, 2025 from 2pm to 4pm' or 'tomorrow 1pm-3pm')")
            elif "start_time" in missing:
                questions.append("What's your start date and time?")
            elif "end_time" in missing:
                questions.append("Until what time do you need the space?")
            
            # Join questions naturally
            if len(questions) == 1:
                prompt += questions[0]
            elif len(questions) == 2:
                prompt += f"{questions[0]}, and {questions[1].lower()}"
            else:
                prompt += "\n".join(f"- {q}" for q in questions)
            
            # Add a friendly closing with better example
            if len(missing) >= 3:
                prompt += "\n\nFeel free to tell me everything at once, like 'Atlanta, meeting room for 5 people tomorrow 2pm-4pm'"
            elif "datetime" in missing or "end_time" in missing:
                prompt += "\n\nExample: 'tomorrow from 2pm to 4pm' or 'Dec 5, 2025 1pm-3pm'"
            
            return prompt
            
        except Exception as e:
            # Fallback to simple but friendly prompt
            logger.warning(f"Failed to build dynamic prompt: {str(e)}")
            missing_formatted = [m.replace('_', ' ') for m in missing]
            return f"I'd be happy to help! Could you let me know the {', '.join(missing_formatted)}?"