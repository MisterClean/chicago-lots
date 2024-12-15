import os
import logging
from typing import Dict, Optional
from datetime import datetime
import json
import requests
from base64 import b64encode

logger = logging.getLogger('chicago_lots.social')

class BlueskyError(Exception):
    """Custom exception for Bluesky-related errors."""
    pass

class BlueskyClient:
    def __init__(self, handle: str, app_password: str):
        """
        Initialize Bluesky client.
        
        Args:
            handle: Bluesky handle (e.g., 'user.bsky.social')
            app_password: App-specific password
        """
        self.handle = handle
        self.app_password = app_password
        self.session = requests.Session()
        self.api_base = "https://bsky.social/xrpc"
        self.auth_token = None
        self.did = None
        
        logger.info(f"Initialized BlueskyClient for handle: {handle}")
        
    def _authenticate(self) -> bool:
        """
        Authenticate with Bluesky and get session token.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.api_base}/com.atproto.server.createSession",
                json={
                    "identifier": self.handle,
                    "password": self.app_password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('accessJwt')
                self.did = data.get('did')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                logger.info("Successfully authenticated with Bluesky")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Authentication request failed: {e}")
            return False
            
    def _upload_image(self, image_path: str) -> Optional[str]:
        """
        Upload an image to Bluesky.
        
        Args:
            image_path: Path to image file
            
        Returns:
            str: Blob reference if successful, None otherwise
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                
            # Upload blob
            response = self.session.post(
                f"{self.api_base}/com.atproto.repo.uploadBlob",
                headers={'Content-Type': 'image/jpeg'},
                data=image_data
            )
            
            if response.status_code == 200:
                blob = response.json().get('blob')
                logger.debug(f"Successfully uploaded image: {image_path}")
                return blob
            else:
                logger.error(f"Failed to upload image: {response.status_code} - {response.text}")
                return None
                
        except (IOError, requests.RequestException) as e:
            logger.error(f"Error uploading image: {e}")
            return None
            
    def post(self, text: str, image_path: Optional[str] = None) -> Optional[str]:
        """
        Create a post on Bluesky.
        
        Args:
            text: Post text content
            image_path: Optional path to image file
            
        Returns:
            str: Post URI if successful, None otherwise
        """
        if not self.auth_token and not self._authenticate():
            raise BlueskyError("Authentication failed")
            
        try:
            record = {
                "$type": "app.bsky.feed.post",
                "text": text,
                "createdAt": datetime.utcnow().isoformat() + 'Z'
            }
            
            # Add image if provided
            if image_path:
                blob = self._upload_image(image_path)
                if blob:
                    record["embed"] = {
                        "$type": "app.bsky.embed.images",
                        "images": [{
                            "alt": "Street View image of property",
                            "image": blob
                        }]
                    }
                else:
                    logger.warning("Failed to upload image, proceeding with text-only post")
                    
            response = self.session.post(
                f"{self.api_base}/com.atproto.repo.createRecord",
                json={
                    "repo": self.did,
                    "collection": "app.bsky.feed.post",
                    "record": record
                }
            )
            
            if response.status_code == 200:
                uri = response.json().get('uri')
                logger.info(f"Successfully created post: {uri}")
                return uri
            else:
                logger.error(f"Failed to create post: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error creating post: {e}")
            return None
            
    def format_post(self, pin: str, address: str) -> str:
        """
        Format post text for a property.
        
        Args:
            pin: Property PIN
            address: Property address
            
        Returns:
            str: Formatted post text
        """
        return f"{address}\nPIN: {pin}"
