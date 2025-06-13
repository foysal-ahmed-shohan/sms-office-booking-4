"""Booking schema and intents for the chat system"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RoomType(str, Enum):
    MEETING_ROOM = "meeting_room"
    CONFERENCE_ROOM = "conference_room"
    PRIVATE_OFFICE = "private_office"
    HOT_DESK = "hot_desk"
    PHONE_BOOTH = "phone_booth"
    EVENT_SPACE = "event_space"


class BookingIntent(str, Enum):
    BOOK_ROOM = "book_room"
    CANCEL_BOOKING = "cancel_booking"
    CHECK_AVAILABILITY = "check_availability"
    LIST_BOOKINGS = "list_bookings"
    GENERAL_INFO = "general_info"
    UNKNOWN = "unknown"


class BookingSlots(BaseModel):
    """Slots to be filled for a complete booking"""
    location: Optional[str] = Field(None, description="Location or city for the booking")
    location_id: Optional[str] = Field(None, description="OfficeRND location ID")
    room_type: Optional[RoomType] = Field(None, description="Type of room needed")
    capacity: Optional[int] = Field(None, description="Number of people")
    resource_id: Optional[str] = Field(None, description="Specific resource/room ID from OfficeRND")
    resource_name: Optional[str] = Field(None, description="Name of the specific resource/room")
    start_date: Optional[str] = Field(None, description="Start date for booking")
    start_time: Optional[str] = Field(None, description="Start time for booking")
    end_date: Optional[str] = Field(None, description="End date for booking")
    end_time: Optional[str] = Field(None, description="End time for booking")
    # Keep old fields for backward compatibility
    date: Optional[str] = Field(None, description="Date for booking (deprecated)")
    time: Optional[str] = Field(None, description="Time for booking (deprecated)")
    duration: Optional[str] = Field(None, description="Duration of booking (deprecated)")
    special_requirements: Optional[str] = Field(None, description="Any special requirements")
    
    def is_complete(self) -> bool:
        """Check if all required slots are filled"""
        # Check new fields first, fallback to old ones
        has_start = (self.start_date and self.start_time) or (self.date and self.time)
        has_end = (self.end_date and self.end_time) or self.duration
        required = [self.location, self.room_type, self.capacity, has_start, has_end, self.resource_id]
        return all(required)
    
    def missing_slots(self) -> List[str]:
        """Get list of missing required slots"""
        missing = []
        if not self.location:
            missing.append("location")
        if not self.room_type:
            missing.append("room_type")
        if not self.capacity:
            missing.append("capacity")
        if not self.resource_id:
            missing.append("resource")
        
        # Check for date/time info
        has_start = (self.start_date and self.start_time) or (self.date and self.time)
        has_end = (self.end_date and self.end_time) or self.duration
        
        if not has_start and not has_end:
            missing.append("datetime")  # Ask for both start and end
        elif has_start and not has_end:
            missing.append("end_time")  # Only need end time
        elif not has_start and has_end:
            missing.append("start_time")  # Only need start time
            
        return missing
    
    def to_summary(self) -> str:
        """Generate a summary of the booking"""
        parts = []
        if self.room_type:
            parts.append(f"Room type: {self.room_type.replace('_', ' ').title()}")
        if self.location:
            parts.append(f"Location: {self.location}")
        if self.capacity:
            parts.append(f"Capacity: {self.capacity} people")
        if self.date:
            parts.append(f"Date: {self.date}")
        if self.time:
            parts.append(f"Time: {self.time}")
        if self.duration:
            parts.append(f"Duration: {self.duration}")
        return ", ".join(parts) if parts else "No booking details yet"


# Location suggestions (mock data)
AVAILABLE_LOCATIONS = [
    "Salt Lake City",
    "New York",
    "San Francisco", 
    "Chicago",
    "Los Angeles",
    "Boston",
    "Seattle",
    "Austin",
    "Denver",
    "Miami"
]


# Prompts for missing information - will be dynamically updated
SLOT_PROMPTS = {
    "location": "Which location would you like to book in?",
    "room_type": "What type of space do you need?",
    "capacity": "How many people will be using the space?",
    "resource": "Which specific room would you like?",
    "date": "What date do you need the room?",
    "time": "What time would you like to start?",
    "duration": "How long do you need the space?"
}

def get_dynamic_slot_prompts():
    """Get slot prompts with dynamic suggestions from OfficeRND"""
    try:
        from app.services.officernd_service import officernd_service
        
        # Get dynamic location suggestions
        location_suggestions = officernd_service.get_location_suggestions()
        prompts = SLOT_PROMPTS.copy()
        prompts["location"] = f"Which location would you like to book in? We have offices in: {location_suggestions}"
        
        # Get dynamic resource type suggestions
        resource_suggestions = officernd_service.get_resource_type_suggestions()
        prompts["room_type"] = f"What type of space do you need? Options: {resource_suggestions}"
        
        return prompts
    except Exception as e:
        # Fallback to static prompts if service fails
        return SLOT_PROMPTS