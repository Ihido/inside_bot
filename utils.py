from config import Config

async def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS