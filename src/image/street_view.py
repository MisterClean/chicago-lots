import os
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.location import Location

logger = logging.getLogger('chicago_lots.image')

class StreetViewError(Exception):
    """Custom exception for Street View related errors."""
    pass

class StreetViewClient:
    def __init__(self, api_key: str, image_size: str = "600x400", save_dir: str = "images"):
        """
        Initialize Street View client.
        
        Args:
            api_key: Google Maps API key
            image_size: Image dimensions (default: "600x400")
            save_dir: Directory to save images (default: "images")
        """
        self.api_key = api_key
        self.image_size = image_size
        self.save_dir = save_dir
        self.geolocator = Nominatim(user_agent="chicago_lots_bot")
        
        # Ensure save directory exists
        os.makedirs(save_dir, exist_ok=True)
        logger.info(f"Initialized StreetViewClient with save directory: {save_dir}")
        
    def get_location(self, address: str, retries: int = 3) -> Optional[Location]:
        """
        Geocode an address with retry logic.
        
        Args:
            address: Address to geocode
            retries: Number of retry attempts
            
        Returns:
            Location object if successful, None otherwise
        """
        for attempt in range(retries):
            try:
                location = self.geolocator.geocode(address)
                if location:
                    logger.debug(f"Successfully geocoded address: {address}")
                    return location
                time.sleep(1)  # Brief pause between retries
            except GeocoderTimedOut:
                logger.warning(f"Geocoding timed out for {address}, attempt {attempt + 1}/{retries}")
                time.sleep(2 ** attempt)  # Exponential backoff
            except GeocoderUnavailable as e:
                logger.error(f"Geocoding service unavailable: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error during geocoding: {e}")
                break
                
        logger.error(f"Failed to geocode address after {retries} attempts: {address}")
        return None
        
    def get_street_view_image(self, lat: float, lon: float, heading: int = None) -> Optional[bytes]:
        """
        Fetch Street View image for given coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            heading: Optional camera heading in degrees
            
        Returns:
            Image bytes if successful, None otherwise
        """
        base_url = "https://maps.googleapis.com/maps/api/streetview"
        params = {
            'size': self.image_size,
            'location': f'{lat},{lon}',
            'key': self.api_key,
            'return_error_code': True
        }
        
        if heading is not None:
            params['heading'] = heading
            
        try:
            response = requests.get(base_url, params=params)
            
            if response.status_code == 200:
                # Check if we got a valid image (not the "no image" response)
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    return response.content
                else:
                    logger.warning(f"No Street View image available for location: {lat}, {lon}")
                    return None
            else:
                logger.error(f"Street View API error: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Request failed for Street View image: {e}")
            return None
            
    def process_location(self, pin: str, address: str) -> Dict:
        """
        Process a location to get its Street View image.
        
        Args:
            pin: Property PIN
            address: Property address
            
        Returns:
            Dictionary containing process results
        """
        logger.info(f"Processing location - PIN: {pin}, Address: {address}")
        
        result = {
            'pin': pin,
            'address': address,
            'status': 'error',
            'image_path': None,
            'error': None
        }
        
        # Get coordinates
        location = self.get_location(address)
        if not location:
            result['error'] = 'Geocoding failed'
            return result
            
        # Try to get Street View image
        image_data = self.get_street_view_image(location.latitude, location.longitude)
        if not image_data:
            result['error'] = 'No Street View image available'
            return result
            
        # Save image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{pin}_{timestamp}.jpg"
        image_path = os.path.join(self.save_dir, filename)
        
        try:
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            result.update({
                'status': 'success',
                'image_path': image_path,
                'latitude': location.latitude,
                'longitude': location.longitude
            })
            logger.info(f"Successfully saved image for PIN {pin}: {image_path}")
            
        except IOError as e:
            result['error'] = f'Failed to save image: {str(e)}'
            logger.error(f"Failed to save image for PIN {pin}: {e}")
            
        return result
        
    def process_batch(self, locations: list[Dict[str, str]], rate_limit: int = 2) -> list[Dict]:
        """
        Process a batch of locations with rate limiting.
        
        Args:
            locations: List of dictionaries containing 'pin' and 'address'
            rate_limit: Seconds to wait between requests
            
        Returns:
            List of processing results
        """
        results = []
        for location in locations:
            result = self.process_location(location['pin'], location['address'])
            results.append(result)
            time.sleep(rate_limit)  # Rate limiting
            
        return results
