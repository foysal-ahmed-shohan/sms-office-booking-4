"""OpenAI service for intelligent chat responses"""
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
import json
import logging
from app.config import settings
from app.schemas.booking_schema import BookingIntent, BookingSlots, RoomType, SLOT_PROMPTS, get_dynamic_slot_prompts

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
    
    def _get_available_locations(self) -> str:
        """Get available locations from OfficeRND or fallback"""
        try:
            from app.services.officernd_service import officernd_service
            locations = officernd_service.get_locations()
            if locations:
                location_names = [loc.get('name', '') for loc in locations if loc.get('name')]
                return ", ".join(location_names)
        except Exception as e:
            logger.warning(f"Failed to get OfficeRND locations: {str(e)}")
        
        # Fallback to static list
        return "Atlanta, New York, Dallas"
    
    def _get_available_room_types(self) -> str:
        """Get available room types from OfficeRND or fallback"""
        try:
            from app.services.officernd_service import officernd_service
            types = officernd_service.get_resource_types()
            if types:
                type_names = [rt.get('title', '') for rt in types if rt.get('title')]
                return ", ".join(type_names)
        except Exception as e:
            logger.warning(f"Failed to get OfficeRND room types: {str(e)}")
        
        # Fallback to static list
        return "Meeting room, Dedicated desk, Hotdesk"
        
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
              Available locations: {self._get_available_locations()}
            
            - room_type: Type of space needed. Available types: {self._get_available_room_types()}
              Map variations intelligently:
              * "meeting room", "meeting space", "conference room" -> "meeting_room"
              * "desk", "hot desk", "shared desk", "workspace" -> "hot_desk" or "hotdesk"
              * "dedicated desk", "personal desk" -> "desk"
              Only extract if it matches available types.
            
            - capacity: Number of people (extract any number mentioned with context like "for X people", "X person", "party of X")
            
            - start_date: Start date for booking (e.g., "Dec 5, 2025", "tomorrow", "5/12/2025")
            - start_time: Start time (e.g., "2pm", "14:00")
            - end_date: End date (usually same as start_date for single-day bookings)
            - end_time: End time (e.g., "4pm", "16:00")
            
            IMPORTANT: Look for datetime ranges like:
            * "Dec 5 from 2pm to 4pm" -> start_date: "Dec 5", start_time: "2pm", end_date: "Dec 5", end_time: "4pm"
            * "5/12/2025 1pm-3pm" -> start_date: "5/12/2025", start_time: "1pm", end_date: "5/12/2025", end_time: "3pm"
            * "tomorrow 2pm-4pm" -> start_date: "tomorrow", start_time: "2pm", end_date: "tomorrow", end_time: "4pm"
            
            Also set the deprecated fields for compatibility:
            - date: Same as start_date
            - time: Same as start_time
            - duration: Calculate from start/end if possible
            
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
            # Handle new datetime fields
            if "start_date" in extracted:
                current_slots.start_date = extracted["start_date"]
                logger.info(f"Extracted start_date: {extracted['start_date']}")
            if "start_time" in extracted:
                current_slots.start_time = extracted["start_time"]
                logger.info(f"Extracted start_time: {extracted['start_time']}")
            if "end_date" in extracted:
                current_slots.end_date = extracted["end_date"]
                logger.info(f"Extracted end_date: {extracted['end_date']}")
            if "end_time" in extracted:
                current_slots.end_time = extracted["end_time"]
                logger.info(f"Extracted end_time: {extracted['end_time']}")
                
            # Handle old fields for compatibility
            if "date" in extracted:
                current_slots.date = extracted["date"]
                if not current_slots.start_date:
                    current_slots.start_date = extracted["date"]
                logger.info(f"Extracted date: {extracted['date']}")
            if "time" in extracted:
                current_slots.time = extracted["time"]
                if not current_slots.start_time:
                    current_slots.start_time = extracted["time"]
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
            # Build a natural confirmation message
            response = "Wonderful! I've got everything I need. Let me confirm your booking:\n\n"
            
            # Format the details in a friendly way
            if slots.room_type:
                room_type_str = slots.room_type.value.replace('_', ' ').title()
                response += f"• {room_type_str} "
            
            if slots.location:
                response += f"at our {slots.location} office\n"
            
            if slots.capacity:
                people_str = "person" if slots.capacity == 1 else "people"
                response += f"• For {slots.capacity} {people_str}\n"
            
            # Show date/time info
            if slots.start_date and slots.start_time and slots.end_time:
                if slots.start_date == slots.end_date or not slots.end_date:
                    response += f"• On {slots.start_date} from {slots.start_time} to {slots.end_time}\n"
                else:
                    response += f"• From {slots.start_date} at {slots.start_time} to {slots.end_date} at {slots.end_time}\n"
            elif slots.date and slots.time:
                response += f"• On {slots.date} at {slots.time}"
                if slots.duration:
                    response += f" (duration: {slots.duration})"
                response += "\n"
            
            response += "\nI'm confirming this booking for you right now. You'll receive a confirmation message shortly with all the details!"
            
            return response
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
            # Show datetime info in a user-friendly way
            if slots.start_date and slots.start_time and slots.end_time:
                if slots.start_date == slots.end_date or not slots.end_date:
                    collected.append(f"booking: {slots.start_date} from {slots.start_time} to {slots.end_time}")
                else:
                    collected.append(f"booking: {slots.start_date} {slots.start_time} to {slots.end_date} {slots.end_time}")
            elif slots.date and slots.time:
                if slots.duration:
                    collected.append(f"booking: {slots.date} at {slots.time} for {slots.duration}")
                else:
                    collected.append(f"booking: {slots.date} at {slots.time}")
            elif slots.date:
                collected.append(f"date: {slots.date}")
            elif slots.time:
                collected.append(f"time: {slots.time}")
            
            # Build response that acknowledges what we have
            if collected:
                # Make acknowledgments more natural
                if len(collected) == 1:
                    response = f"Got it - {collected[0]}! "
                elif len(collected) == 2:
                    response = f"Perfect! I have {collected[0]} and {collected[1]}. "
                else:
                    response = "Excellent! I've noted down:\n"
                    for item in collected:
                        response += f"• {item.capitalize()}\n"
                    response += "\n"
            else:
                response = ""
            
            # Get all missing information and ask for everything at once
            response += self._build_missing_info_prompt(missing, slots)
            
            return response
    
    def _handle_unknown_intent(self, message: str) -> str:
        """Handle unknown intents with helpful guidance"""
        return ("Hi there! I'm here to help you book the perfect workspace. "
                "You can say things like 'I need a meeting room' or "
                "'Book a desk for tomorrow at 9am'. How can I assist you today?")
    
    def _handle_other_intents(self, intent: BookingIntent, message: str) -> str:
        """Handle other intents"""
        responses = {
            BookingIntent.CANCEL_BOOKING: "I can help you cancel a booking. Please provide your booking reference number or tell me which booking you'd like to cancel.",
            BookingIntent.CHECK_AVAILABILITY: "I can check availability for you. What type of space are you looking for and when do you need it?",
            BookingIntent.LIST_BOOKINGS: "Here are your current bookings:\n\n(No bookings found)\n\nWould you like to make a new booking?",
            BookingIntent.GENERAL_INFO: "I can help you book various types of workspaces including meeting rooms, conference rooms, private offices, hot desks, and phone booths. What would you like to know?"
        }
        
        return responses.get(intent, "How can I help you with your office space needs?")
    
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