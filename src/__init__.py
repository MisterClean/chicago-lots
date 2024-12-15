import os
import yaml
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Set up logging
log_config = config['logging']
log_file = log_config['file']
os.makedirs(os.path.dirname(log_file), exist_ok=True)

formatter = logging.Formatter(log_config['format'])
handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
handler.setFormatter(formatter)

logger = logging.getLogger('chicago_lots')
logger.setLevel(getattr(logging, log_config['level']))
logger.addHandler(handler)

# Add console handler for development
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Create images directory if it doesn't exist
images_dir = config['image']['save_dir']
os.makedirs(images_dir, exist_ok=True)
