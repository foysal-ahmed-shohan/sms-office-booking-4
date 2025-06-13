"""OfficeRND API integration service for dynamic locations and resource types"""
import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.config import settings
import redis
import pickle

logger = logging.getLogger(__name__)


class OfficeRNDService:
    """Service for interacting with OfficeRND APIs"""
    
    def __init__(self):
        self.client_id = settings.officernd_client_id
        self.client_secret = settings.officernd_client_secret
        self.identity_url = settings.officernd_identity_url
        self.base_url = settings.officernd_base_url
        self.org_slug = settings.officernd_org_slug
        self.scope = settings.officernd_scope
        
        # Token storage
        self._token_data = None
        self._token_expiry = None
        
        # Initialize Redis for caching
        try:
            self.redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=False)
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Redis connection established for OfficeRND caching")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory cache: {str(e)}")
            self.use_redis = False
            self._cache = {}
        
    def _get_cached_data(self, key: str, ttl: int = 3600) -> Optional[any]:
        """Get cached data from Redis or memory"""
        try:
            if self.use_redis:
                data = self.redis_client.get(key)
                if data:
                    return pickle.loads(data)
            else:
                cached = self._cache.get(key)
                if cached and cached['expiry'] > datetime.utcnow():
                    return cached['data']
        except Exception as e:
            logger.error(f"Cache retrieval error: {str(e)}")
        return None
    
    def _set_cached_data(self, key: str, data: any, ttl: int = 3600):
        """Set cached data in Redis or memory"""
        try:
            if self.use_redis:
                self.redis_client.setex(key, ttl, pickle.dumps(data))
            else:
                self._cache[key] = {
                    'data': data,
                    'expiry': datetime.utcnow() + timedelta(seconds=ttl)
                }
        except Exception as e:
            logger.error(f"Cache storage error: {str(e)}")
    
    def _get_access_token(self) -> Optional[str]:
        """Get valid access token, refreshing if necessary"""
        # Check if we have a valid token
        if self._token_data and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return self._token_data.get('access_token')
        
        # Check cache first
        cached_token = self._get_cached_data('officernd_token')
        if cached_token:
            self._token_data = cached_token['data']
            self._token_expiry = cached_token['expiry']
            return self._token_data.get('access_token')
        
        # Get new token
        try:
            logger.info("Requesting new OfficeRND access token")
            
            token_url = f"{self.identity_url}/oauth/token"
            
            data = {
                'scope': self.scope,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }
            
            headers = {
                'accept': 'application/json',
                'content-type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(token_url, data=data, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            self._token_data = token_data
            
            # Calculate expiry (slightly before actual expiry for safety)
            expires_in = token_data.get('expires_in', 3600)
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
            
            # Cache the token
            self._set_cached_data('officernd_token', {
                'data': token_data,
                'expiry': self._token_expiry
            }, expires_in - 60)
            
            logger.info(f"Successfully obtained OfficeRND token, expires in {expires_in} seconds")
            return token_data.get('access_token')
            
        except Exception as e:
            logger.error(f"Failed to get OfficeRND access token: {str(e)}")
            return None
    
    def get_locations(self) -> List[Dict]:
        """Get all available locations from OfficeRND"""
        # Check cache first
        cached_locations = self._get_cached_data('officernd_locations', ttl=3600)  # Cache for 1 hour
        if cached_locations:
            logger.debug("Returning cached locations")
            return cached_locations
        
        token = self._get_access_token()
        if not token:
            logger.error("No access token available")
            return []
        
        try:
            url = f"{self.base_url}/organizations/{self.org_slug}/locations"
            headers = {
                'accept': 'application/json',
                'authorization': f'Bearer {token}'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            locations = data.get('results', [])
            
            # Process locations to extract relevant info
            processed_locations = []
            for loc in locations:
                if loc.get('isOpen') and loc.get('isPublic'):
                    address = loc.get('address', {})
                    processed_locations.append({
                        'id': loc.get('_id'),
                        'name': loc.get('name'),
                        'city': address.get('city'),
                        'street': address.get('street'),
                        'formatted_address': address.get('formattedAddress'),
                        'country': address.get('country'),
                        'state': address.get('state'),
                        'timezone': loc.get('timezone')
                    })
            
            # Cache the results
            self._set_cached_data('officernd_locations', processed_locations, ttl=3600)
            
            logger.info(f"Retrieved {len(processed_locations)} locations from OfficeRND")
            return processed_locations
            
        except Exception as e:
            logger.error(f"Failed to get locations: {str(e)}")
            return []
    
    def get_resource_types(self) -> List[Dict]:
        """Get all available resource types (room/space types) from OfficeRND"""
        # Check cache first
        cached_types = self._get_cached_data('officernd_resource_types', ttl=3600)
        if cached_types:
            logger.debug("Returning cached resource types")
            return cached_types
        
        token = self._get_access_token()
        if not token:
            logger.error("No access token available")
            return []
        
        try:
            url = f"{self.base_url}/organizations/{self.org_slug}/resource-types"
            headers = {
                'accept': 'application/json',
                'authorization': f'Bearer {token}'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            resource_types = data.get('results', [])
            
            # Process resource types to extract bookable ones
            processed_types = []
            for rt in resource_types:
                if rt.get('canBook'):
                    processed_types.append({
                        'id': rt.get('_id'),
                        'title': rt.get('title'),
                        'type': rt.get('type'),
                        'booking_mode': rt.get('bookingMode'),
                        'icon': rt.get('icon')
                    })
            
            # Cache the results
            self._set_cached_data('officernd_resource_types', processed_types, ttl=3600)
            
            logger.info(f"Retrieved {len(processed_types)} resource types from OfficeRND")
            return processed_types
            
        except Exception as e:
            logger.error(f"Failed to get resource types: {str(e)}")
            return []
    
    def match_location(self, user_input: str) -> Optional[Dict]:
        """Match user input to available locations"""
        locations = self.get_locations()
        if not locations:
            return None
        
        user_input_lower = user_input.lower().strip()
        
        # First try exact match on city or name
        for loc in locations:
            if (loc.get('city', '').lower() == user_input_lower or 
                loc.get('name', '').lower() == user_input_lower):
                return loc
        
        # Then try partial match
        for loc in locations:
            if (user_input_lower in loc.get('city', '').lower() or
                user_input_lower in loc.get('name', '').lower() or
                user_input_lower in loc.get('street', '').lower()):
                return loc
        
        # Try fuzzy matching for common misspellings
        location_variations = {
            'nyc': 'new york',
            'ny': 'new york',
            'sf': 'san francisco',
            'la': 'los angeles',
            'atl': 'atlanta'
        }
        
        normalized = location_variations.get(user_input_lower, user_input_lower)
        if normalized != user_input_lower:
            return self.match_location(normalized)
        
        return None
    
    def match_resource_type(self, user_input: str) -> Optional[Dict]:
        """Match user input to available resource types"""
        resource_types = self.get_resource_types()
        if not resource_types:
            return None
        
        user_input_lower = user_input.lower().strip()
        
        # Log available resource types for debugging
        logger.debug(f"Matching '{user_input}' against resource types: {[rt.get('title') for rt in resource_types]}")
        
        # Normalize variations - handle spaces, hyphens, underscores
        normalized_input = user_input_lower.replace('_', ' ').replace('-', ' ')
        # Also try without spaces
        compact_input = user_input_lower.replace(' ', '').replace('_', '').replace('-', '')
        
        # First try exact match (case insensitive)
        for rt in resource_types:
            title_lower = rt.get('title', '').lower()
            title_compact = title_lower.replace(' ', '').replace('-', '')
            
            # Check various forms
            if (title_lower == user_input_lower or 
                title_lower == normalized_input or
                title_compact == compact_input):
                logger.info(f"Exact match found: '{user_input}' -> '{rt.get('title')}'")
                return rt
        
        # Mapping of common terms to resource types (expanded)
        type_mappings = {
            'meeting room': ['meeting', 'conference'],
            'conference room': ['conference', 'meeting'],
            'desk': ['desk', 'hot desk', 'hotdesk', 'dedicated desk'],
            'hot desk': ['hotdesk', 'hot desk'],
            'hotdesk': ['hotdesk', 'hot desk'],
            'office': ['office', 'private office'],
            'phone booth': ['phone', 'booth', 'call']
        }
        
        # Try mapping matches
        for key, values in type_mappings.items():
            if user_input_lower == key or normalized_input == key:
                for rt in resource_types:
                    title_lower = rt.get('title', '').lower()
                    if any(v in title_lower for v in values):
                        logger.info(f"Mapping match found: '{user_input}' -> '{rt.get('title')}'")
                        return rt
        
        # Try partial match (contains)
        for rt in resource_types:
            title_lower = rt.get('title', '').lower()
            if (user_input_lower in title_lower or 
                normalized_input in title_lower or
                title_lower in user_input_lower or
                title_lower in normalized_input):
                logger.info(f"Partial match found: '{user_input}' -> '{rt.get('title')}'")
                return rt
        
        logger.warning(f"No match found for resource type: '{user_input}'")
        return None
    
    def get_location_suggestions(self, limit: int = 5) -> str:
        """Get formatted location suggestions for chat responses"""
        locations = self.get_locations()
        if not locations:
            return "various locations"
        
        # Get unique cities
        cities = list(set(loc.get('city') for loc in locations if loc.get('city')))
        cities = cities[:limit]
        
        if len(cities) > 1:
            return f"{', '.join(cities[:-1])}, or {cities[-1]}"
        elif cities:
            return cities[0]
        else:
            return "our available locations"
    
    def get_resource_type_suggestions(self) -> str:
        """Get formatted resource type suggestions for chat responses"""
        resource_types = self.get_resource_types()
        if not resource_types:
            return "Meeting Room, Conference Room, Private Office, Hot Desk, or Phone Booth"
        
        # Get unique titles
        titles = [rt.get('title') for rt in resource_types if rt.get('title')]
        
        if len(titles) > 1:
            return f"{', '.join(titles[:-1])}, or {titles[-1]}"
        elif titles:
            return titles[0]
        else:
            return "our available spaces"


# Create singleton instance
officernd_service = OfficeRNDService()