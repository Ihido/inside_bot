# test_database.py - тест базы данных
from database import get_session, Submission, Admin
from config import Config

print("=== ТЕСТ БАЗЫ ДАННЫХ ===")

try:
    # Получаем сессию
    session = get_session()
    print("✅ Сессия БД создана")
    
    # Пробуем выполнить запрос
    count = session.query(Submission).count()
    print(f"✅ Запрос выполнен. Записей в базе: {count}")
    
    session.close()
    print("✅ Сессия закрыта")
    
    print("\n✅ База данных работает корректно!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()