import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(','))) if os.getenv("ADMIN_IDS") else []
    
    MAX_PHOTO_SIZE = int(os.getenv("ALLOWED_PHOTO_SIZE", 10)) * 1024 * 1024
    MAX_VIDEO_SIZE = int(os.getenv("ALLOWED_VIDEO_SIZE", 50)) * 1024 * 1024
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    PHOTOS_DIR = os.path.join(DATA_DIR, "photos")
    VIDEOS_DIR = os.path.join(DATA_DIR, "videos")
    SUBMISSIONS_DIR = os.path.join(DATA_DIR, "submissions")
    
    for directory in [DATA_DIR, PHOTOS_DIR, VIDEOS_DIR, SUBMISSIONS_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    INFO_TEMPLATE = "Пример: Флот 3, БПО Ноябрьск, июнь 2025, мастер КИПиА Иванов И.И."