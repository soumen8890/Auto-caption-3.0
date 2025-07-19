# Auto Caption Telegram Bot

This bot automatically adds formatted captions to media files in your Telegram channels.

## Features
- Custom caption formatting with variables
- Support for 2-3 channels per user
- Extract metadata from files
- Easy-to-use button interface
- MongoDB database support

## Deployment

### Requirements
- Python 3.8+
- MongoDB database
- Telegram API ID and Hash
- Bot Token

### Environment Variables
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
MONGO_URI=mongodb_connection_string
OWNER_ID=your_telegram_id

### Deploy to Render
1. Fork this repository
2. Create a new Web Service on Render
3. Connect your GitHub account
4. Select your forked repository
5. Set the environment variables
6. Deploy!

## Available Variables
- `{filename}` - Original file name
- `{filesize}` - File size in readable format
- `{caption}` - Original caption
- `{language}` - Language from filename
- `{year}` - Year from filename
- `{quality}` - Quality from filename
- `{season}` - Season from filename
- `{episode}` - Episode from filename
- `{duration}` - Duration from video
- `{height}` - Video height
- `{width}` - Video width
- `{ext}` - File extension
- `{resolution}` - Video resolution
- `{mime_type}` - MIME type
- `{title}` - Audio title
- `{artist}` - Audio artist
- `{wish}` - Time-based greeting

## Commands
- `/start` - Start the bot
- `/restart` - Restart the bot
- `/setcaption` - Set custom caption format
- `/addchannel` - Add a channel for auto captioning
- `/stats` - Get bot statistics
