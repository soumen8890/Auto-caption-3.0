import os

class Config:
    API_ID = int(os.environ.get("API_ID", "20919625"))
    API_HASH = os.environ.get("API_HASH", "40168846bf06f4ff443f0f7a4182bf8d")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://jigam96466:YpvmFQpmb9y9gzcU@cluster0.wajbn6h.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    OWNER_ID = int(os.environ.get("OWNER_ID", "6233910543"))
    
    # Default caption format
    DEFAULT_CAPTION = """{filename}
    
📁 Size: {filesize}
🎞️ Resolution: {resolution}
🎬 Duration: {duration}
"""
