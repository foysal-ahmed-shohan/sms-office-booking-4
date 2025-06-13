"""Schemas package for data validation and serialization"""
from .sms_schemas import (
    SMSWebhookRequest,
    SMSWebhookResponse,
    SMSReplyData,
    TestSMSRequest,
    ConfigStatus,
    HealthCheckResponse
)

from .booking_schema import (
    RoomType,
    BookingIntent,
    BookingSlots,
    SLOT_PROMPTS,
    AVAILABLE_LOCATIONS
)

__all__ = [
    # SMS schemas
    "SMSWebhookRequest",
    "SMSWebhookResponse", 
    "SMSReplyData",
    "TestSMSRequest",
    "ConfigStatus",
    "HealthCheckResponse",
    # Booking schemas
    "RoomType",
    "BookingIntent",
    "BookingSlots",
    "SLOT_PROMPTS",
    "AVAILABLE_LOCATIONS"
]