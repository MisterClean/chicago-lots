# Chicago Lots Bot

A Python application that posts Google Street View images of Chicago property lots to Bluesky. Inspired by the "Every Lot" Twitter bots, this application systematically posts images of every property in Chicago's tax records, ordered by PIN (Property Index Number).

## Features

- Processes Chicago PIN database to get property addresses
- Fetches Google Street View images for each property
- Posts images to Bluesky with property information
- Maintains posting history and handles errors
- Configurable posting frequency to complete all lots over 30 years
- Comprehensive logging and error handling
- Database analysis tools for posting statistics

## Requirements

- Python 3.9+
- Google Maps API key (with Street View Static API enabled)
- Bluesky account with app password
- SQLite database with Chicago PIN data

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/chicago-lots.git
cd chicago-lots
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your credentials:
```env
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
BLUESKY_HANDLE=your.handle.bsky.social
BLUESKY_APP_PASSWORD=your_app_password
```

## Configuration

The application is configured through `config.yaml`. Key settings include:

```yaml
database:
  pin_table: "pin_data"
  batch_size: 10
  posts_per_day: 96  # Configured for 30-year completion

image:
  size: "600x400"
  save_dir: "images"
  rate_limit: 2

social:
  platform: "bluesky"
  post_interval: 900  # 15 minutes in seconds

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/chicago_lots.log"
```

## Database Setup

The application requires a SQLite database with Chicago PIN data. The database schema will be automatically created when you first run the application, but you'll need to populate it with PIN data.

To analyze the PIN database and calculate posting frequency:

```bash
python -m src.database.analyze_pins
```

This will show:
- Total number of properties
- Required posts per day for 30-year completion
- Estimated completion date

## Usage

Run the bot:

```bash
python -m src
```

The application will:
1. Load configuration and connect to services
2. Process properties in batches
3. Get Street View images
4. Post to Bluesky
5. Track progress and handle errors

## Project Structure

```
chicago-lots/
├── src/
│   ├── __init__.py
│   ├── __main__.py
│   ├── database/
│   │   ├── pin_database.py
│   │   └── analyze_pins.py
│   ├── image/
│   │   └── street_view.py
│   └── social/
│       └── bluesky.py
├── config.yaml
├── .env
├── .gitignore
└── README.md
```

## Logging

Logs are written to `logs/chicago_lots.log` and include:
- Property processing status
- Image fetching results
- Posting confirmations
- Errors and exceptions

## Error Handling

The application includes robust error handling:
- Failed properties are tracked in the database
- Automatic retries with exponential backoff
- Properties with multiple failures are skipped
- Comprehensive error logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the "Every Lot" Twitter bots
- Uses Google Street View Static API
- Built for the Bluesky social network
