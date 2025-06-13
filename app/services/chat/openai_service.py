"""OpenAI service for intelligent chat responses"""
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
import json
import logging
from app.config import settings
from app.schemas.booking_schema import BookingIntent, BookingSlots, RoomType, SLOT_PROMPTS

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI chat integration"""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = settings.openai_model or "gpt-4"
        logger.info(f"OpenAI service initialized with model: {self.model}")
        logger.debug(f"API key starts with: {self.api_key[:8]}...")
        
    def extract_booking_intent(self, message: str, context: List[Dict] = None) -> BookingIntent:
        """Extract the user's intent from their message"""
        try:
            logger.debug(f"Extracting intent from message: {message}")
            logger.debug(f"Context history length: {len(context) if context else 0}")
            
            system_prompt = """You are an AI assistant that identifies user intents for an office booking system.
            Consider the conversation history to understand context.
            
            Classify the user's intent as one of:
            - book_room: User wants to book a meeting room, office, or workspace (or is providing information for an ongoing booking)
            - cancel_booking: User wants to cancel an existing booking
            - check_availability: User wants to check what's available
            - list_bookings: User wants to see their bookings
            - general_info: User asking about services, prices, or general information
            - unknown: Intent is unclear
            
            IMPORTANT: If the conversation history shows an ongoing booking process (assistant asking for booking details), 
            and the user provides ANY booking-related information (location, date, time, room type, capacity, etc.), 
            ALWAYS classify as book_room.
            
            Examples of book_room intent:
            - "I need a meeting room"
            - "Salt Lake City" (when in booking context)
            - "02-5-2026 date, meeting room"
            - "for 5 people tomorrow"
            - "2pm" (when in booking context)
            
            Respond with only the intent classification."""
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history for context
            if context:
                # Add last few messages from history
                for msg in context[-6:]:  # Last 6 messages for context
                    if msg.get("role") in ["user", "assistant"]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=50
            )
            
            intent_str = response.choices[0].message.content.strip().lower()
            
            # Map to enum
            intent_map = {
                "book_room": BookingIntent.BOOK_ROOM,
                "cancel_booking": BookingIntent.CANCEL_BOOKING,
                "check_availability": BookingIntent.CHECK_AVAILABILITY,
                "list_bookings": BookingIntent.LIST_BOOKINGS,
                "general_info": BookingIntent.GENERAL_INFO
            }
            
            return intent_map.get(intent_str, BookingIntent.UNKNOWN)
            
        except Exception as e:
            logger.error(f"Error extracting intent: {str(e)}", exc_info=True)
            return BookingIntent.UNKNOWN
    
    def extract_booking_slots(self, message: str, current_slots: BookingSlots) -> BookingSlots:
        """Extract booking information from user message"""
        try:
            system_prompt = f"""You are an AI assistant that extracts booking information from user messages.
            Be very intelligent about understanding variations, typos, and natural language.
            
            Extract the following information if present:
            - location: The city or location. Be smart about typos and variations:
              * "salt lake sity" -> "Salt Lake City"
              * "NYC" or "ny" -> "New York"
              * "SF" or "san fran" -> "San Francisco"
              * "LA" -> "Los Angeles"
              * "Chi town" -> "Chicago"
              Available locations: Salt Lake City, New York, San Francisco, Chicago, Los Angeles, Boston, Seattle, Austin, Denver, Miami
            
            - room_type: Type of space needed. Map variations intelligently:
              * "meeting room", "meeting space", "conference room for meetings" -> "meeting_room"
              * "conference", "conf room", "large meeting room" -> "conference_room"
              * "office", "private room", "quiet room" -> "private_office"
              * "desk", "hot desk", "shared desk", "workspace" -> "hot_desk"
              * "phone booth", "call room", "phone room" -> "phone_booth"
              * "event space", "large room", "presentation room" -> "event_space"
            
            - capacity: Number of people (extract any number mentioned with context like "for X people", "X person", "party of X")
            
            - date: Date for booking. Understand various formats:
              * "02-5-2026", "2/5/26", "Feb 5" -> Parse correctly
              * "tomorrow", "next week", "monday" -> Convert to readable format
              * Look for any date patterns
            
            - time: Start time (understand "2pm", "14:00", "2 o'clock", "afternoon" etc.)
            
            - duration: How long ("1 hr", "90 minutes", "half day", "all morning")
            
            IMPORTANT: Extract ALL information present in the message, even if multiple pieces are provided.
            For example, if user says "02-5-2026 date, meeting room", extract BOTH date AND room_type.
            
            Current booking information: {current_slots.json()}
            
            Return ONLY a valid JSON object with ALL fields found in the message.
            Be generous in your interpretation - if something looks like it might be a location, date, or room type, extract it.
            
            DO NOT include markdown formatting, code blocks, or any other text. Return only the JSON object."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                extracted = json.loads(content)
                logger.debug(f"Successfully extracted slots: {extracted}")
            except Exception as e:
                logger.warning(f"Failed to parse JSON: {content}, error: {str(e)}")
                extracted = {}
            
            # Update slots
            if "location" in extracted:
                current_slots.location = extracted["location"]
                logger.info(f"Extracted location: {extracted['location']}")
            if "room_type" in extracted:
                try:
                    current_slots.room_type = RoomType(extracted["room_type"])
                    logger.info(f"Extracted room_type: {extracted['room_type']}")
                except:
                    logger.warning(f"Invalid room_type: {extracted.get('room_type')}")
            if "capacity" in extracted:
                try:
                    current_slots.capacity = int(extracted["capacity"])
                    logger.info(f"Extracted capacity: {extracted['capacity']}")
                except:
                    logger.warning(f"Invalid capacity: {extracted.get('capacity')}")
            if "date" in extracted:
                current_slots.date = extracted["date"]
                logger.info(f"Extracted date: {extracted['date']}")
            if "time" in extracted:
                current_slots.time = extracted["time"]
                logger.info(f"Extracted time: {extracted['time']}")
            if "duration" in extracted:
                current_slots.duration = extracted["duration"]
                logger.info(f"Extracted duration: {extracted['duration']}")
                
            return current_slots
            
        except Exception as e:
            logger.error(f"Error extracting slots: {str(e)}")
            return current_slots
    
    def generate_response(self, 
                         message: str, 
                         intent: BookingIntent,
                         slots: BookingSlots,
                         conversation_history: List[Dict]) -> str:
        """Generate an intelligent response based on context"""
        try:
            if intent == BookingIntent.BOOK_ROOM:
                # Check if we just extracted new information
                if conversation_history:
                    last_assistant_msg = None
                    for msg in reversed(conversation_history):
                        if msg.get('role') == 'assistant':
                            last_assistant_msg = msg.get('content', '').lower()
                            break
                    
                    # If we just asked for something and the user provided it, acknowledge it
                    if last_assistant_msg:
                        acknowledged = False
                        if 'location' in last_assistant_msg and slots.location:
                            logger.info("User just provided location after being asked")
                            acknowledged = True
                        elif 'type of space' in last_assistant_msg and slots.room_type:
                            logger.info("User just provided room type after being asked")
                            acknowledged = True
                        elif 'how many people' in last_assistant_msg and slots.capacity:
                            logger.info("User just provided capacity after being asked")
                            acknowledged = True
                
                return self._handle_booking_response(slots)
            elif intent == BookingIntent.UNKNOWN:
                return self._handle_unknown_intent(message)
            else:
                return self._handle_other_intents(intent, message)
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'm having trouble processing your request. Could you please try again?"
    
    def _handle_booking_response(self, slots: BookingSlots) -> str:
        """Handle booking intent responses"""
        if slots.is_complete():
            # All slots filled, confirm booking
            summary = slots.to_summary()
            return f"Great! I have all the information I need. Let me confirm your booking:\n\n{summary}\n\nI'm processing your booking now. You'll receive a confirmation shortly."
        else:
            # Check what we have and what's missing
            missing = slots.missing_slots()
            collected = []
            
            if slots.location:
                collected.append(f"location: {slots.location}")
            if slots.room_type:
                collected.append(f"room type: {slots.room_type.replace('_', ' ')}")
            if slots.capacity:
                collected.append(f"capacity: {slots.capacity} people")
            if slots.date:
                collected.append(f"date: {slots.date}")
            if slots.time:
                collected.append(f"time: {slots.time}")
            
            # Build response that acknowledges what we have
            if collected:
                response = f"Thanks! I've noted: {', '.join(collected)}. "
            else:
                response = ""
            
            # Ask for the first missing slot
            if missing[0] in SLOT_PROMPTS:
                prompt = SLOT_PROMPTS[missing[0]]
                response += prompt
                
                # Add context about remaining items if more than one missing
                if len(missing) > 1:
                    other_missing = [m.replace('_', ' ') for m in missing[1:]]
                    response += f"\n\n(I'll also need: {', '.join(other_missing)})"
            else:
                response += f"I still need the {missing[0].replace('_', ' ')} for your booking."
            
            return response
    
    def _handle_unknown_intent(self, message: str) -> str:
        """Handle unknown intents with helpful guidance"""
        return ("I can help you book meeting rooms and workspaces. "
                "Just tell me what you need, like 'I want to book a meeting room' "
                "or 'I need a conference room for 10 people tomorrow at 2 PM'.")
    
    def _handle_other_intents(self, intent: BookingIntent, message: str) -> str:
        """Handle other intents"""
        responses = {
            BookingIntent.CANCEL_BOOKING: "I can help you cancel a booking. Please provide your booking reference number or tell me which booking you'd like to cancel.",
            BookingIntent.CHECK_AVAILABILITY: "I can check availability for you. What type of space are you looking for and when do you need it?",
            BookingIntent.LIST_BOOKINGS: "Here are your current bookings:\n\n(No bookings found)\n\nWould you like to make a new booking?",
            BookingIntent.GENERAL_INFO: "I can help you book various types of workspaces including meeting rooms, conference rooms, private offices, hot desks, and phone booths. What would you like to know?"
        }
        
        return responses.get(intent, "How can I help you with your office space needs?")