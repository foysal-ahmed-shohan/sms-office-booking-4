"""Conversation manager for handling chat state and context"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime, timedelta

from app.database.models import User, ConversationState
from app.schemas.booking_schema import BookingIntent, BookingSlots, get_dynamic_slot_prompts
from app.services.chat.openai_service import OpenAIService
from app.services.chat.simple_chat_service import SimpleChatService
from app.services.officernd_service import officernd_service

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation state and context for users"""
    
    def __init__(self, db: Session):
        self.db = db
        self.chat_service = None
        
        # Try to use OpenAI service, fallback to simple service
        try:
            self.chat_service = OpenAIService()
            logger.info("OpenAI service initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI service: {str(e)}")
            logger.info("Falling back to simple chat service")
            self.chat_service = SimpleChatService()
        
        self.max_history_messages = 10  # Keep last 10 messages for context
        
    def process_message(self, user: User, message: str) -> tuple:
        """Process incoming message and generate response
        Returns: (response_text, booking_ids_dict)
        """
        try:
            # Get or create conversation state
            conv_state = self._get_or_create_conversation(user)
            
            # Add message to history BEFORE processing
            self._add_to_history(conv_state, "user", message)
            
            # Commit the history update immediately to ensure persistence
            self.db.commit()
            
            # Extract intent with conversation history
            intent = self.chat_service.extract_booking_intent(
                message, 
                conv_state.conversation_history
            )
            logger.info(f"Detected intent: {intent}")
            
            # If we have an active booking conversation and intent is unknown,
            # assume it's continuing the booking flow
            if (conv_state.current_intent == 'book_room' and 
                intent == BookingIntent.UNKNOWN and 
                conv_state.booking_data):
                intent = BookingIntent.BOOK_ROOM
                logger.info("Continuing booking flow based on conversation context")
            
            # Update conversation intent if needed
            if intent != BookingIntent.UNKNOWN:
                conv_state.current_intent = intent.value
            
            # Initialize booking IDs dict
            booking_ids = None
            
            # Handle based on intent
            if intent == BookingIntent.BOOK_ROOM or conv_state.current_intent == 'book_room':
                result = self._handle_booking_flow(conv_state, message)
                # Check if result is tuple (has IDs)
                if isinstance(result, tuple):
                    response, booking_ids = result
                else:
                    response = result
            else:
                # For other intents, generate response
                slots = BookingSlots(**(conv_state.booking_data or {}))
                response = self.chat_service.generate_response(
                    message, intent, slots, conv_state.conversation_history
                )
                
                # Reset booking data for non-booking intents
                if intent != BookingIntent.BOOK_ROOM:
                    conv_state.booking_data = {}
            
            # Add response to history
            self._add_to_history(conv_state, "assistant", response)
            
            # Update last interaction time
            conv_state.last_interaction = datetime.utcnow()
            
            # Save conversation state
            self.db.commit()
            
            return response, booking_ids
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            self.db.rollback()
            return "I apologize, but I'm having trouble processing your request. Please try again.", None
    
    def _get_or_create_conversation(self, user: User) -> ConversationState:
        """Get existing or create new conversation state"""
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.user_id == user.id
        ).first()
        
        if not conv_state:
            conv_state = ConversationState(
                user_id=user.id,
                conversation_history=[],
                booking_data={},
                state='active'
            )
            self.db.add(conv_state)
            self.db.commit()
            logger.info(f"Created new conversation state for user {user.id}")
        else:
            # Check if conversation is stale (older than 30 minutes)
            if conv_state.last_interaction:
                time_diff = datetime.utcnow() - conv_state.last_interaction.replace(tzinfo=None)
                if time_diff > timedelta(minutes=30):
                    # Reset conversation
                    conv_state.conversation_history = []
                    conv_state.booking_data = {}
                    conv_state.current_intent = None
                    logger.info(f"Reset stale conversation for user {user.id}")
        
        return conv_state
    
    def _handle_booking_flow(self, conv_state: ConversationState, message: str):
        """Handle the booking conversation flow
        Returns: response string or (response, booking_ids) tuple
        """
        # Check if we're awaiting confirmation
        if conv_state.state == 'awaiting_confirm':
            return self._handle_confirmation(conv_state, message)
        
        # Get current booking slots (excluding internal fields)
        booking_data_clean = {k: v for k, v in (conv_state.booking_data or {}).items() if not k.startswith('_')}
        current_slots = BookingSlots(**booking_data_clean)
        
        # Check if we're waiting for resource selection
        waiting_for_resource = bool(conv_state.booking_data and '_available_resources' in conv_state.booking_data)
        
        # Log what we had before extraction
        before_extraction = current_slots.dict(exclude_none=True)
        logger.info(f"Slots before extraction: {before_extraction}")
        
        # If we're waiting for resource selection, don't extract new slots
        if waiting_for_resource:
            updated_slots = current_slots
            # Important: Don't try to extract booking slots when we're expecting a resource selection
            logger.info("Waiting for resource selection - skipping slot extraction")
        else:
            # Create a copy for extraction to avoid modifying current_slots
            slots_for_extraction = BookingSlots(**booking_data_clean)
            
            # Extract information from message
            updated_slots = self.chat_service.extract_booking_slots(message, slots_for_extraction)
        
        # Log what we have after extraction
        after_extraction = updated_slots.dict(exclude_none=True)
        logger.info(f"Slots after extraction: {after_extraction}")
        
        # Check what new information was extracted
        new_info = {}
        for key, value in after_extraction.items():
            if key not in before_extraction or before_extraction[key] != value:
                new_info[key] = value
        
        if new_info:
            logger.info(f"New information extracted: {new_info}")
        
        # Handle resource selection FIRST if user is responding to resource prompt
        available_resources = conv_state.booking_data.get('_available_resources', []) if conv_state.booking_data else []
        logger.info(f"Checking for resource selection. Available resources: {len(available_resources)}, current resource_id: {updated_slots.resource_id}")
        
        if available_resources and not updated_slots.resource_id:
            logger.info(f"Attempting to match user message '{message}' to available resources")
            # Try to match user's response to available resources
            matched_resource = officernd_service.match_resource(message, available_resources)
            if matched_resource:
                updated_slots.resource_id = matched_resource.get('id')
                updated_slots.resource_name = matched_resource.get('name')
                logger.info(f"User selected resource: {updated_slots.resource_name} (ID: {updated_slots.resource_id})")
                
                # Clear the waiting flag
                waiting_for_resource = False
                
                # Remove the available resources from booking data after selection
                if '_available_resources' in conv_state.booking_data:
                    del conv_state.booking_data['_available_resources']
                
                # Update booking data immediately
                conv_state.booking_data = updated_slots.dict(exclude_none=True)
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(conv_state, 'booking_data')
                self.db.commit()
            else:
                logger.warning(f"Could not match '{message}' to any available resource")
                # Couldn't match resource, ask again
                return "I couldn't find that option. Please choose by name or number from the list above."
        
        # Validate location against OfficeRND data
        if updated_slots.location and (not current_slots.location or updated_slots.location != current_slots.location):
            matched_location = officernd_service.match_location(updated_slots.location)
            if matched_location:
                updated_slots.location = matched_location.get('name', updated_slots.location)
                updated_slots.location_id = matched_location.get('id')
                logger.info(f"Matched location to OfficeRND: '{updated_slots.location}' (ID: {updated_slots.location_id})")
            else:
                # Location not found, clear it and ask again
                location_input = updated_slots.location
                updated_slots.location = None
                return f"Sorry, we don't have an office in '{location_input}'. {get_dynamic_slot_prompts()['location']}"
        
        # Validate room type against OfficeRND data
        if updated_slots.room_type and (not current_slots.room_type or updated_slots.room_type != current_slots.room_type):
            room_type_str = updated_slots.room_type.value.replace('_', ' ')
            matched_type = officernd_service.match_resource_type(room_type_str)
            if not matched_type:
                # Room type not found, clear it and ask again
                updated_slots.room_type = None
                return f"Sorry, '{room_type_str}' is not available. {get_dynamic_slot_prompts()['room_type']}"
        
        # Check if we have location and room type but no resource yet
        if (updated_slots.location_id and updated_slots.room_type and 
            not updated_slots.resource_id):
            
            # Need to check if user provided a resource name in the message
            resource_matched = False
            
            # Get available resources for this location and room type
            room_type_map = {
                'meeting_room': 'meeting_room',
                'hot_desk': 'hotdesk',
                'private_office': 'office',
                'phone_booth': 'phone_booth',
                'conference_room': 'meeting_room',  # Map conference to meeting room
                'event_space': 'event_space'
            }
            
            officernd_room_type = room_type_map.get(updated_slots.room_type.value, updated_slots.room_type.value)
            resources = officernd_service.get_resources(
                room_type=officernd_room_type,
                location_id=updated_slots.location_id
            )
            
            logger.info(f"Retrieved {len(resources)} resources from OfficeRND")
            
            if resources:
                # Filter resources by type to match what user requested
                filtered_resources = []
                for res in resources:
                    res_type = (res.get('type') or '').lower()
                    res_name = (res.get('name') or '').lower()
                    res_desc = (res.get('description') or '').lower()
                    
                    # Check if resource is actually a phone booth based on name/description
                    is_phone_booth = ('booth' in res_name and 'board' not in res_name) or 'phone booth' in res_desc
                    
                    # Map the resource type from API to our expected types
                    if officernd_room_type == 'hotdesk' and res_type in ['hotdesk', 'hot_desk', 'desk']:
                        filtered_resources.append(res)
                    elif officernd_room_type == 'meeting_room' and res_type in ['meeting_room', 'meetingroom', 'meeting'] and not is_phone_booth:
                        # Exclude phone booths from meeting rooms
                        filtered_resources.append(res)
                    elif officernd_room_type == 'office' and (res_type in ['office', 'private_office', 'privateoffice', 'team_room'] or 'office' in res_name):
                        filtered_resources.append(res)
                    elif officernd_room_type == 'phone_booth' and (res_type in ['phone_booth', 'phonebooth', 'booth'] or is_phone_booth):
                        filtered_resources.append(res)
                    elif officernd_room_type == 'event_space' and res_type in ['event_space', 'eventspace', 'event']:
                        filtered_resources.append(res)
                
                logger.info(f"Filtered to {len(filtered_resources)} resources matching type '{officernd_room_type}'")
                
                # If no resources match the type, show what's available
                if not filtered_resources:
                    logger.warning(f"No resources found matching type '{officernd_room_type}' at {updated_slots.location}")
                    # Show what types ARE available
                    available_types = set()
                    for res in resources:
                        if res.get('type'):
                            available_types.add(res.get('type'))
                    
                    if available_types:
                        return f"Sorry, we don't have any {room_type_display} available at {updated_slots.location}. Available space types at this location: {', '.join(sorted(available_types))}. Please choose a different room type."
                    else:
                        return f"Sorry, we don't have any {room_type_display} available at {updated_slots.location}. Please try a different location or room type."
                
                if filtered_resources:
                    # Store resources in booking data for persistence
                    conv_state.booking_data = conv_state.booking_data or {}
                    conv_state.booking_data['_available_resources'] = filtered_resources
                    
                    # Don't try to auto-match resources from the initial message
                    # Always show the options to the user
                    resource_matched = False
                    
                    # Always ask user to choose from available resources
                    if not resource_matched:
                        # Format resources with images
                        room_type_display = updated_slots.room_type.value.replace('_', ' ') if updated_slots.room_type else "space"
                        resource_prompt = f"Great! Now please choose a specific {room_type_display} at {updated_slots.location}:\n\n"
                        
                        for i, res in enumerate(filtered_resources[:5], 1):  # Limit to 5 options
                            name = res.get('name', 'Unknown')
                            desc = res.get('description', '')
                            size = res.get('size', 0)
                            images = res.get('images', [])
                            
                            resource_prompt += f"{i}. {name}"
                            if desc:
                                resource_prompt += f" - {desc}"
                            if size > 0:
                                resource_prompt += f" (capacity: {size})"
                            
                            # Add image URL if available
                            if images and len(images) > 0:
                                # Convert relative URL to full URL
                                image_url = images[0]
                                if image_url.startswith('//'):
                                    image_url = f"https:{image_url}"
                                resource_prompt += f"\n   View: {image_url}"
                            
                            resource_prompt += "\n\n"
                        
                        resource_prompt += "Please tell me which one you'd like by name or number."
                        
                        # Store the prompt for later use if needed
                        self._last_resource_prompt = resource_prompt
                        
                        # Save the current state before returning
                        conv_state.booking_data = updated_slots.dict(exclude_none=True)
                        conv_state.booking_data['_available_resources'] = filtered_resources
                        
                        # Mark as modified
                        from sqlalchemy.orm.attributes import flag_modified
                        flag_modified(conv_state, 'booking_data')
                        self.db.commit()
                        
                        # Don't update booking data yet since we're waiting for resource selection
                        return resource_prompt
        
        # Before updating booking data, check if we only need resource selection
        missing_before_update = updated_slots.missing_slots()
        
        # Update booking data - create new dict to ensure SQLAlchemy detects change
        conv_state.booking_data = updated_slots.dict(exclude_none=True)
        
        # Mark as modified explicitly
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(conv_state, 'booking_data')
        
        # If we only have resource missing and we just showed the resource prompt, return it
        # BUT only if we didn't just select a resource and we're not waiting for resource selection
        if (missing_before_update == ['resource'] and 
            hasattr(self, '_last_resource_prompt') and 
            not updated_slots.resource_id and  # Only show prompt if no resource selected
            '_available_resources' not in conv_state.booking_data):  # And not already showing resources
            return self._last_resource_prompt
        
        # Generate response based on what's missing
        response = self.chat_service.generate_response(
            message,
            BookingIntent.BOOK_ROOM,
            updated_slots,
            conv_state.conversation_history
        )
        
        # If booking is complete, move to awaiting confirmation
        if updated_slots.is_complete():
            conv_state.state = 'awaiting_confirm'
            logger.info(f"All booking info collected for user {conv_state.user_id}, awaiting confirmation")
        
        return response
    
    def _handle_confirmation(self, conv_state: ConversationState, message: str) -> str:
        """Handle booking confirmation"""
        message_lower = message.lower().strip()
        
        # Check for positive confirmation
        positive_responses = ['yes', 'yeah', 'yep', 'confirm', 'correct', 'ok', 'okay', 'sure', 'approve', 'approved', 'go ahead', 'book it']
        
        if any(word in message_lower for word in positive_responses):
            # Confirmed! Process the booking
            conv_state.state = 'confirmed'
            slots = BookingSlots(**(conv_state.booking_data or {}))
            
            # Get user's phone number
            user = self.db.query(User).filter(User.id == conv_state.user_id).first()
            if not user:
                return "Error: Unable to find user information."
            
            # Check if user is an existing member or company
            member_info = officernd_service.find_member_or_company_by_phone(user.phone_number)
            
            if member_info:
                logger.info(f"Found existing {member_info['type']}: {member_info['name']} (ID: {member_info['id']})")
            else:
                # Create new member
                logger.info(f"No existing member/company found for {user.phone_number}, creating new member")
                
                # Try to extract a name from the conversation or use phone number as name
                member_name = f"Guest {user.phone_number}"
                
                # Create the member
                new_member = officernd_service.create_member(
                    name=member_name,
                    phone=user.phone_number,
                    location_id=slots.location_id,
                    description="Created via SMS booking system"
                )
                
                if new_member:
                    member_info = {
                        'type': 'member',
                        'id': new_member.get('_id'),
                        'name': new_member.get('name')
                    }
                else:
                    logger.error("Failed to create member")
                    return "Sorry, there was an error creating your member profile. Please try again."
            
            # In a real implementation, this is where we'd call OfficeRND API to create the booking
            logger.info(f"Booking confirmed for user {conv_state.user_id}: {slots.to_summary()}")
            
            # Build confirmation message
            # Generate a booking ID (in production, this would come from OfficeRND API)
            import random
            booking_id = random.randint(1000000000, 9999999999)
            
            response = f"Great! Your OfficeRND booking has been confirmed!\n\n"
            
            # Add booking details
            if slots.resource_name:
                response += f"• Room: {slots.resource_name} at {slots.location}\n"
            elif slots.room_type:
                room_type_str = slots.room_type.value.replace('_', ' ').title()
                response += f"• Space: {room_type_str} at {slots.location}\n"
            
            if slots.capacity:
                response += f"• Capacity: {slots.capacity} {'person' if slots.capacity == 1 else 'people'}\n"
            if slots.start_date and slots.start_time and slots.end_time:
                response += f"• Date & Time: {slots.start_date} from {slots.start_time} to {slots.end_time}\n"
            
            response += f"\nYour booking ID is: {booking_id}\n"
            response += "\nThank you for using OfficeRND booking service!"
            
            # Prepare all IDs for separate field
            booking_ids = {
                "booking_id": str(booking_id),
                "location_id": slots.location_id,
                "resource_type_id": slots.room_type.value if slots.room_type else None,
                "resource_id": slots.resource_id,
                "resource_name": slots.resource_name
            }
            
            # Add member/company information
            if member_info:
                if member_info['type'] == 'member':
                    booking_ids["member_id"] = member_info['id']
                    booking_ids["member_name"] = member_info['name']
                else:
                    booking_ids["company_id"] = member_info['id']
                    booking_ids["company_name"] = member_info['name']
            
            # Reset conversation for next booking
            conv_state.booking_data = {}
            conv_state.current_intent = None
            conv_state.state = 'active'
            
            return response, booking_ids
        elif any(word in message_lower for word in ['no', 'cancel', 'wrong', 'change', 'modify']):
            # User wants to change something
            conv_state.state = 'active'  # Go back to active state
            return "No problem! What would you like to change? Just tell me what needs to be different."
        else:
            # Unclear response, ask again
            return "I didn't quite catch that. Please reply 'yes' to confirm your booking or 'no' if you'd like to make changes."
    
    def _add_to_history(self, conv_state: ConversationState, role: str, content: str):
        """Add message to conversation history"""
        if not isinstance(conv_state.conversation_history, list):
            conv_state.conversation_history = []
        
        # Create a new list to ensure SQLAlchemy detects the change
        history = list(conv_state.conversation_history)
        history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last N messages
        if len(history) > self.max_history_messages:
            history = history[-self.max_history_messages:]
        
        # Assign back to trigger SQLAlchemy change detection
        conv_state.conversation_history = history
        
        # Mark the object as modified explicitly
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(conv_state, 'conversation_history')
    
    def get_conversation_summary(self, user_id: int) -> Optional[Dict]:
        """Get summary of current conversation state"""
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.user_id == user_id
        ).first()
        
        if not conv_state:
            return None
        
        slots = BookingSlots(**(conv_state.booking_data or {}))
        
        return {
            "current_intent": conv_state.current_intent,
            "state": conv_state.state,
            "booking_summary": slots.to_summary(),
            "missing_info": slots.missing_slots(),
            "last_interaction": conv_state.last_interaction.isoformat() if conv_state.last_interaction else None,
            "message_count": len(conv_state.conversation_history)
        }