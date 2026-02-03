import os
from dotenv import load_dotenv

load_dotenv()

print("=== Проверка конфигурации ===")
print(f"BOT_TOKEN существует: {'Да' if os.getenv('BOT_TOKEN') else 'Нет'}")
print(f"BOT_TOKEN длина: {len(os.getenv('BOT_TOKEN', ''))}")
print(f"ADMIN_IDS: {os.getenv('ADMIN_IDS')}")

# Проверка формата токена
token = os.getenv('BOT_TOKEN', '')
if token:
    parts = token.split(':')
    if len(parts) == 2 and parts[0].isdigit() and len(parts[1]) > 20:
        print("✅ Формат токена правильный")
    else:
        print("❌ Неправильный формат токена")