import os
from dotenv import load_dotenv
from src.database.pin_database import PINDatabase
from src.social.bluesky import BlueskyClient

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize database
    db = PINDatabase("chicago_lots.db")
    
    # Add a test property if none exist
    test_pin = "14-21-103-001-0000"
    test_address = "123 W Test Street, Chicago, IL 60601"
    db.add_pin(test_pin, test_address, 41.8781, -87.6298)  # Example coordinates in Chicago
    print(f"Added test property: {test_address} (PIN: {test_pin})")
    
    # Get next unposted property
    properties = db.get_next_unposted(batch_size=1)
    if not properties:
        print("No unposted properties found")
        return
        
    property = properties[0]
    print(f"Found property: {property['address']} (PIN: {property['pin']})")
    
    # Initialize Bluesky client
    bluesky = BlueskyClient(
        handle=os.getenv("BLUESKY_HANDLE"),
        app_password=os.getenv("BLUESKY_PASSWORD")
    )
    
    # Format and create post
    post_text = bluesky.format_post(property['pin'], property['address'])
    print(f"\nCreating post with text:\n{post_text}")
    
    post_uri = bluesky.post(post_text)
    
    if post_uri:
        print(f"\nSuccessfully created post: {post_uri}")
        # Mark as posted in database
        db.mark_posted(property['pin'], post_uri, None)
    else:
        print("\nFailed to create post")
        db.record_error(property['pin'], "Failed to create post")
    
    db.close()

if __name__ == "__main__":
    main()
