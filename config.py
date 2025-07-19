import os

class Config:
    API_ID = int(os.environ.get("API_ID", ""))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    MONGO_URI = os.environ.get("MONGO_URI", "")
    OWNER_ID = int(os.environ.get("OWNER_ID", 0))
    
    # Default caption format
    DEFAULT_CAPTION = """{filename}
    
📁 Size: {filesize}
🎞️ Resolution: {resolution}
🎬 Duration: {duration}
"""
