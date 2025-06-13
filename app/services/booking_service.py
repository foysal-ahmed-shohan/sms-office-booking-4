"""Booking service for handling OfficeRND bookings"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import re
import logging

from app.schemas.booking_schema import BookingSlots
from app.services.officernd_service import officernd_service
from app.utils.date_utils import parse_user_datetime, datetime_to_officernd_format, format_datetime_for_display

logger = logging.getLogger(__name__)


class BookingService:
    """Service for managing bookings with OfficeRND"""
    
    def parse_booking_datetime(self, slots: BookingSlots) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Parse booking start and end datetime from slots
        
        Returns:
            Tuple of (start_datetime, end_datetime) or (None, None) if parsing fails
        """
        # Parse start date and time
        start_dt = parse_user_datetime(
            slots.start_date or slots.date,
            slots.start_time or slots.time
        )
        
        if not start_dt:
            return None, None
        
        # Calculate end time based on duration or end_time
        if slots.end_time:
            end_dt = parse_user_datetime(
                slots.end_date or slots.start_date or slots.date,
                slots.end_time
            )
        elif slots.duration:
            # Parse duration like "1 hour", "2 hours", "30 minutes"
            duration_match = re.match(r'(\d+)\s*(hour|hr|minute|min)', slots.duration.lower())
            if duration_match:
                amount = int(duration_match.group(1))
                unit = duration_match.group(2)
                if 'hour' in unit or 'hr' in unit:
                    end_dt = start_dt + timedelta(hours=amount)
                else:
                    end_dt = start_dt + timedelta(minutes=amount)
            else:
                end_dt = start_dt + timedelta(hours=1)  # Default 1 hour
        else:
            end_dt = start_dt + timedelta(hours=1)  # Default 1 hour
        
        return start_dt, end_dt
    
    def check_and_create_booking(self, slots: BookingSlots, member_id: str) -> Dict:
        """Check availability and create booking if available
        
        Returns:
            Dict with 'success' boolean and either 'booking' data or 'error' message
        """
        # Parse datetime
        start_dt, end_dt = self.parse_booking_datetime(slots)
        
        if not start_dt or not end_dt:
            return {
                'success': False,
                'error': "Sorry, I couldn't understand the date/time format. Please try again with a clearer format."
            }
        
        # Check availability
        is_available = officernd_service.check_availability(
            resource_id=slots.resource_id,
            start_datetime=start_dt,
            end_datetime=end_dt
        )
        
        if not is_available:
            return {
                'success': False,
                'error': f"Sorry, {slots.resource_name} is not available from {format_datetime_for_display(start_dt)} to {format_datetime_for_display(end_dt)}. Please choose another date and time.",
                'conflict': True
            }
        
        # Create the booking
        booking = officernd_service.create_booking(
            start=datetime_to_officernd_format(start_dt),
            end=datetime_to_officernd_format(end_dt),
            resource_id=slots.resource_id,
            member_id=member_id
        )
        
        if not booking:
            return {
                'success': False,
                'error': "Sorry, there was an error creating your booking. Please try again."
            }
        
        logger.info(f"Booking created successfully: {booking.get('_id')} (Ref: {booking.get('reference')})")
        
        return {
            'success': True,
            'booking': booking,
            'start_dt': start_dt,
            'end_dt': end_dt
        }
    
    def format_booking_confirmation(self, slots: BookingSlots, booking: Dict, member_info: Dict) -> Tuple[str, Dict]:
        """Format booking confirmation message and IDs
        
        Returns:
            Tuple of (message, booking_ids_dict)
        """
        booking_id = booking.get('_id')
        booking_reference = booking.get('reference')
        
        # Build confirmation message
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
        
        response += f"\nYour booking reference is: {booking_reference}\n"
        response += "\nThank you for using OfficeRND booking service!"
        
        # Prepare all IDs for separate field
        booking_ids = {
            "booking_id": booking_id,
            "booking_reference": booking_reference,
            "location_id": slots.location_id,
            "resource_type_id": slots.room_type.value if slots.room_type else None,
            "resource_id": slots.resource_id,
            "resource_name": slots.resource_name,
            "start_datetime": booking.get('start'),
            "end_datetime": booking.get('end')
        }
        
        # Add member/company information
        if member_info:
            if member_info['type'] == 'member':
                booking_ids["member_id"] = member_info['id']
                booking_ids["member_name"] = member_info['name']
            else:
                booking_ids["company_id"] = member_info['id']
                booking_ids["company_name"] = member_info['name']
        
        return response, booking_ids


# Create singleton instance
booking_service = BookingService()