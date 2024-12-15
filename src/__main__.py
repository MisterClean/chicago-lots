import os
import time
import logging
import yaml
from datetime import datetime
from dotenv import load_dotenv

from database.pin_database import PINDatabase
from image.street_view import StreetViewClient
from social.bluesky import BlueskyClient

logger = logging.getLogger('chicago_lots.main')

def load_config():
    """Load configuration from config.yaml."""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def main():
    """Main execution function."""
    # Load environment variables and configuration
    load_dotenv()
    config = load_config()
    
    # Initialize clients
    db = PINDatabase('chicago_lots.db')
    street_view = StreetViewClient(
        api_key=os.getenv('GOOGLE_MAPS_API_KEY'),
        image_size=config['image']['size'],
        save_dir=config['image']['save_dir']
    )
    bluesky = BlueskyClient(
        handle=os.getenv('BLUESKY_HANDLE'),
        app_password=os.getenv('BLUESKY_APP_PASSWORD')
    )
    
    logger.info("Starting Chicago Lots bot")
    
    while True:
        try:
            # Get statistics
            stats = db.get_statistics()
            logger.info(f"Current statistics: {stats}")
            
            # Get next batch of unposted properties
            properties = db.get_next_unposted(config['database']['batch_size'])
            
            if not properties:
                logger.info("No more properties to process")
                time.sleep(config['social']['post_interval'])
                continue
                
            # Process each property
            for prop in properties:
                try:
                    # Get Street View image
                    image_result = street_view.process_location(
                        prop['pin'],
                        prop['address']
                    )
                    
                    if image_result['status'] == 'error':
                        logger.error(f"Failed to get image for PIN {prop['pin']}: {image_result['error']}")
                        db.record_error(prop['pin'], image_result['error'])
                        continue
                        
                    # Create post
                    post_text = bluesky.format_post(prop['pin'], prop['address'])
                    post_uri = bluesky.post(post_text, image_result['image_path'])
                    
                    if post_uri:
                        # Mark as posted
                        db.mark_posted(prop['pin'], post_uri, image_result['image_path'])
                        logger.info(f"Successfully posted PIN {prop['pin']}")
                    else:
                        db.record_error(prop['pin'], "Failed to create Bluesky post")
                        
                except Exception as e:
                    logger.error(f"Error processing PIN {prop['pin']}: {e}")
                    db.record_error(prop['pin'], str(e))
                    
                # Wait before next post
                time.sleep(config['social']['post_interval'])
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            time.sleep(60)  # Wait a minute before retrying
            
    # Cleanup
    db.close()

if __name__ == "__main__":
    main()
