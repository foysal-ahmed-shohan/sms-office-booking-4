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
    room_type: Optional[RoomType] = Field(None, description="Type of room needed")
    capacity: Optional[int] = Field(None, description="Number of people")
    date: Optional[str] = Field(None, description="Date for booking")
    time: Optional[str] = Field(None, description="Time for booking")
    duration: Optional[str] = Field(None, description="Duration of booking")
    special_requirements: Optional[str] = Field(None, description="Any special requirements")
    
    def is_complete(self) -> bool:
        """Check if all required slots are filled"""
        required = [self.location, self.room_type, self.capacity, self.date, self.time]
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
        if not self.date:
            missing.append("date")
        if not self.time:
            missing.append("time")
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


# Prompts for missing information
SLOT_PROMPTS = {
    "location": "Which location would you like to book in?",
    "room_type": "What type of space do you need?",
    "capacity": "How many people will be using the space?",
    "date": "What date do you need the room?",
    "time": "What time would you like to start?",
    "duration": "How long do you need the space?"
}