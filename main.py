import os
import re
from datetime import datetime
from typing import Dict, Optional

from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, 
    InlineKeyboardButton, CallbackQuery
)
from pymongo import MongoClient
from config import Config
import moviepy.editor as mp
from mutagen.mp4 import MP4
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from PIL import Image
import requests

# Initialize MongoDB
mongo_client = MongoClient(Config.MONGO_URI)
db = mongo_client["AutoCaptionBot"]
users_col = db["users"]
channels_col = db["channels"]

# Initialize Pyrogram Client
app = Client(
    "auto_caption_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Helper functions
def get_file_metadata(file_path: str) -> Dict:
    """Extract metadata from file"""
    metadata = {}
    
    try:
        if file_path.lower().endswith(('.mp4', '.mkv', '.webm')):
            video = mp.VideoFileClip(file_path)
            metadata["duration"] = str(datetime.timedelta(seconds=int(video.duration)))
            metadata["width"] = video.size[0]
            metadata["height"] = video.size[1]
            metadata["resolution"] = f"{video.size[0]}x{video.size[1]}"
            
            # For MP4 files
            if file_path.lower().endswith('.mp4'):
                mp4 = MP4(file_path)
                if mp4.tags is not None:
                    metadata["title"] = mp4.tags.get("\xa9nam", [""])[0]
                    metadata["artist"] = mp4.tags.get("\xa9ART", [""])[0]
            
        elif file_path.lower().endswith('.mp3'):
            audio = MP3(file_path)
            metadata["duration"] = str(datetime.timedelta(seconds=int(audio.info.length)))
            if audio.tags is not None:
                id3 = ID3(file_path)
                metadata["title"] = id3.get("TIT2", "").text[0] if "TIT2" in id3 else ""
                metadata["artist"] = id3.get("TPE1", "").text[0] if "TPE1" in id3 else ""
                
    except Exception as e:
        print(f"Error extracting metadata: {e}")
    
    return metadata

def parse_filename(filename: str) -> Dict:
    """Extract information from filename"""
    data = {
        "language": "",
        "year": "",
        "quality": "",
        "season": "",
        "episode": "",
        "ext": filename.split(".")[-1] if "." in filename else ""
    }
    
    # Common patterns
    patterns = {
        "year": r"(19|20)\d{2}",
        "quality": r"(480p|720p|1080p|2160p|4K|8K|HD|FHD|UHD)",
        "season": r"(S|s|Season|season)\s?\d{1,2}",
        "episode": r"(E|e|Episode|episode)\s?\d{1,3}",
        "language": r"(Hindi|English|Tamil|Telugu|Malayalam|Kannada|Bengali|Marathi|Gujarati|Punjabi)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, filename)
        if match:
            data[key] = match.group()
    
    return data

def get_wish() -> str:
    """Return time-based greeting"""
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "Good Morning"
    elif 12 <= hour < 17:
        return "Good Afternoon"
    elif 17 <= hour < 21:
        return "Good Evening"
    return "Good Night"

def format_caption(caption_format: str, file_info: Dict, metadata: Dict) -> str:
    """Format caption with variables"""
    filename_data = parse_filename(file_info["filename"])
    
    variables = {
        "{filename}": file_info["filename"],
        "{filesize}": file_info["filesize"],
        "{caption}": file_info.get("caption", ""),
        "{language}": filename_data["language"],
        "{year}": filename_data["year"],
        "{quality}": filename_data["quality"],
        "{season}": filename_data["season"],
        "{episode}": filename_data["episode"],
        "{duration}": metadata.get("duration", ""),
        "{height}": metadata.get("height", ""),
        "{width}": metadata.get("width", ""),
        "{ext}": filename_data["ext"],
        "{resolution}": metadata.get("resolution", ""),
        "{mime_type}": file_info.get("mime_type", ""),
        "{title}": metadata.get("title", ""),
        "{artist}": metadata.get("artist", ""),
        "{wish}": get_wish()
    }
    
    for var, value in variables.items():
        caption_format = caption_format.replace(var, str(value))
    
    return caption_format

# Bot commands
@app.on_message(filters.command(["start", "restart"]))
async def start(client: Client, message: Message):
    user_id = message.from_user.id
    user = users_col.find_one({"user_id": user_id})
    
    if not user:
        users_col.insert_one({
            "user_id": user_id,
            "caption_format": Config.DEFAULT_CAPTION,
            "channels": []
        })
    
    await message.reply_text(
        "👋 **Welcome to Auto Caption Bot**\n\n"
        "I can automatically add captions to files in your channels.\n\n"
        "📌 **Available Commands:**\n"
        "/setcaption - Set custom caption format\n"
        "/addchannel - Add channels for auto captioning\n"
        "/stats - Get bot statistics\n\n"
        "🛠️ **Variables Available:**\n"
        "• {filename} - File name\n"
        "• {filesize} - File size\n"
        "• {caption} - Original caption\n"
        "• {language} - Language from filename\n"
        "• {year} - Year from filename\n"
        "• {quality} - Quality from filename\n"
        "• {season} - Season from filename\n"
        "• {episode} - Episode from filename\n"
        "• {duration} - Duration from video\n"
        "• {height} - Video height\n"
        "• {width} - Video width\n"
        "• {ext} - File extension\n"
        "• {resolution} - Video resolution\n"
        "• {mime_type} - MIME type\n"
        "• {title} - Audio title\n"
        "• {artist} - Audio artist\n"
        "• {wish} - Time-based greeting",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Set Caption", callback_data="set_caption")],
            [InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")],
            [InlineKeyboardButton("📊 Stats", callback_data="stats")]
        ])
    )

@app.on_message(filters.command("setcaption"))
async def set_caption_command(client: Client, message: Message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        new_caption = " ".join(message.command[1:])
        users_col.update_one(
            {"user_id": user_id},
            {"$set": {"caption_format": new_caption}},
            upsert=True
        )
        await message.reply_text("✅ Caption format updated successfully!")
    else:
        await message.reply_text(
            "Please provide a caption format.\n\n"
            "Example:\n"
            "/setcaption {filename}\n\nSize: {filesize}\nQuality: {quality}"
        )

@app.on_message(filters.command("addchannel"))
async def add_channel_command(client: Client, message: Message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        channel_id = message.command[1]
        try:
            channel_id = int(channel_id)
        except ValueError:
            await message.reply_text("Invalid channel ID. Please provide a numeric ID.")
            return
        
        # Check if bot is admin in channel
        try:
            chat = await client.get_chat(channel_id)
            member = await client.get_chat_member(channel_id, "me")
            if member.status not in ["administrator", "creator"]:
                await message.reply_text("I need to be admin in the channel to add captions.")
                return
        except Exception as e:
            await message.reply_text(f"Error: {str(e)}")
            return
        
        # Add channel to user's list (max 3)
        user = users_col.find_one({"user_id": user_id})
        if user and len(user.get("channels", [])) >= 3:
            await message.reply_text("You can only add up to 3 channels.")
            return
        
        channels_col.update_one(
            {"channel_id": channel_id},
            {"$set": {"user_id": user_id}},
            upsert=True
        )
        
        users_col.update_one(
            {"user_id": user_id},
            {"$addToSet": {"channels": channel_id}},
            upsert=True
        )
        
        await message.reply_text(f"✅ Channel {chat.title} added successfully!")
    else:
        await message.reply_text(
            "Please provide a channel ID.\n\n"
            "Example:\n"
            "/addchannel -1001234567890\n\n"
            "Make sure the bot is admin in the channel."
        )

@app.on_message(filters.command("stats"))
async def stats_command(client: Client, message: Message):
    total_users = users_col.count_documents({})
    total_channels = channels_col.count_documents({})
    
    await message.reply_text(
        "📊 **Bot Statistics**\n\n"
        f"👥 Total Users: {total_users}\n"
        f"📢 Total Channels: {total_channels}"
    )

# Callback handlers
@app.on_callback_query(filters.regex("^set_caption$"))
async def set_caption_callback(client: Client, query: CallbackQuery):
    await query.message.edit_text(
        "📝 **Set Caption Format**\n\n"
        "Send me the new caption format. You can use these variables:\n\n"
        "• {filename} - File name\n"
        "• {filesize} - File size\n"
        "• {caption} - Original caption\n"
        "• {language} - Language from filename\n"
        "• {year} - Year from filename\n"
        "• {quality} - Quality from filename\n"
        "• {season} - Season from filename\n"
        "• {episode} - Episode from filename\n"
        "• {duration} - Duration from video\n"
        "• {height} - Video height\n"
        "• {width} - Video width\n"
        "• {ext} - File extension\n"
        "• {resolution} - Video resolution\n"
        "• {mime_type} - MIME type\n"
        "• {title} - Audio title\n"
        "• {artist} - Audio artist\n"
        "• {wish} - Time-based greeting\n\n"
        "Example:\n"
        "{filename}\n\nSize: {filesize}\nQuality: {quality}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
        ])
    )

@app.on_callback_query(filters.regex("^add_channel$"))
async def add_channel_callback(client: Client, query: CallbackQuery):
    await query.message.edit_text(
        "➕ **Add Channel**\n\n"
        "To add a channel:\n"
        "1. Add the bot as admin to your channel\n"
        "2. Send the channel ID in this format:\n\n"
        "/addchannel -1001234567890\n\n"
        "You can add up to 3 channels.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
        ])
    )

@app.on_callback_query(filters.regex("^stats$"))
async def stats_callback(client: Client, query: CallbackQuery):
    total_users = users_col.count_documents({})
    total_channels = channels_col.count_documents({})
    
    await query.message.edit_text(
        "📊 **Bot Statistics**\n\n"
        f"👥 Total Users: {total_users}\n"
        f"📢 Total Channels: {total_channels}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
        ])
    )

@app.on_callback_query(filters.regex("^back_to_main$"))
async def back_to_main(client: Client, query: CallbackQuery):
    await start(client, query.message)

# Auto caption handler
@app.on_message(filters.channel & filters.media)
async def auto_caption(client: Client, message: Message):
    channel_id = message.chat.id
    channel = channels_col.find_one({"channel_id": channel_id})
    
    if not channel:
        return
    
    user_id = channel["user_id"]
    user = users_col.find_one({"user_id": user_id})
    if not user:
        return
    
    caption_format = user.get("caption_format", Config.DEFAULT_CAPTION)
    
    # Get file info
    if message.video:
        media = message.video
    elif message.document:
        media = message.document
    elif message.audio:
        media = message.audio
    elif message.photo:
        media = message.photo
    else:
        return
    
    file_info = {
        "filename": media.file_name or "",
        "filesize": human_readable_size(media.file_size),
        "caption": message.caption or "",
        "mime_type": media.mime_type or ""
    }
    
    # Download file to extract metadata
    file_path = await client.download_media(message)
    metadata = get_file_metadata(file_path)
    os.remove(file_path)
    
    # Format caption
    new_caption = format_caption(caption_format, file_info, metadata)
    
    # Edit message with new caption
    try:
        await message.edit_caption(new_caption)
    except Exception as e:
        print(f"Error editing caption: {e}")

def human_readable_size(size: int) -> str:
    """Convert bytes to human readable format"""
    if not size:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

# Start the bot
if __name__ == "__main__":
    print("Bot started...")
    app.run()
