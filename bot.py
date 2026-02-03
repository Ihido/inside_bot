import asyncio
import os
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from config import Config
from database import get_session, Submission
from states import ContentSubmission
from keyboards import get_main_menu, get_confirmation_keyboard, get_cancel_keyboard
from utils import is_admin

# Настройка логирования
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Создаем бота и диспетчер
bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ========== БАЗОВЫЕ КОМАНДЫ ==========

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Старт бота"""
    welcome_text = (
        "👋 Добро пожаловать в проект 'Компания изнутри'!\n\n"
        "Здесь мы собираем фото, видео и истории от сотрудников.\n"
        "Выберите тип контента который хотите отправить."
    )
    
    if await is_admin(message.from_user.id):
        await message.answer(f"{welcome_text}\n\n👨‍💼 Вы администратор", reply_markup=get_main_menu())
    else:
        await message.answer(welcome_text, reply_markup=get_main_menu())

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Панель администратора"""
    if not await is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    
    with get_session() as session:
        pending = session.query(Submission).filter_by(status='pending').count()
        approved = session.query(Submission).filter_by(status='approved').count()
        rejected = session.query(Submission).filter_by(status='rejected').count()
        total = session.query(Submission).count()
    
    commands = (
        "👨‍💼 Панель администратора\n\n"
        f"📊 Статистика:\n"
        f"• Всего отправок: {total}\n"
        f"• ⏳ Ожидают: {pending}\n"
        f"• ✅ Одобрено: {approved}\n"
        f"• ❌ Отклонено: {rejected}\n\n"
        "📋 Команды:\n"
        "/pending - ожидающие модерации\n"
        "/submissions - все отправки\n"
        "/view <ID> - просмотр отправки\n"
        "/approve <ID> - одобрить\n"
        "/reject <ID> - отклонить\n"
        "/stats - статистика"
    )
    
    await message.answer(commands)

@dp.message(Command("submissions"))
async def cmd_submissions(message: types.Message):
    """Просмотр всех отправок"""
    if not await is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    
    with get_session() as session:
        # Получаем все отправки
        submissions = session.query(Submission).order_by(
            Submission.submission_date.desc()
        ).limit(20).all()
    
    if not submissions:
        await message.answer("📭 Отправок пока нет.")
        return
    
    # Формируем список
    response = "📋 Последние 20 отправок:\n\n"
    
    for sub in submissions:
        status_emoji = {'pending': '⏳', 'approved': '✅', 'rejected': '❌'}.get(sub.status, '❓')
        content_emoji = {'photo': '📸', 'video': '🎥', 'text': '📝'}.get(sub.content_type, '📄')
        date_str = sub.submission_date.strftime('%d.%m %H:%M')
        
        # Берем первую часть информации о пользователе
        user_info_short = sub.user_info.split(',')[0] if ',' in sub.user_info else sub.user_info[:20]
        
        response += f"{status_emoji}{content_emoji} #{sub.id} - {user_info_short} ({date_str})\n"
    
    await message.answer(response)

@dp.message(Command("view"))
async def cmd_view(message: types.Message):
    """Просмотр конкретной отправки"""
    if not await is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    
    # Парсим ID из команды /view 123
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /view <ID>\nПример: /view 1")
        return
    
    try:
        submission_id = int(args[1])
    except ValueError:
        await message.answer("ID должен быть числом")
        return
    
    with get_session() as session:
        submission = session.query(Submission).filter_by(id=submission_id).first()
    
    if not submission:
        await message.answer(f"❌ Отправка #{submission_id} не найдена.")
        return
    
    # Формируем детальную информацию
    status_ru = {'pending': '⏳ Ожидает', 'approved': '✅ Одобрено', 'rejected': '❌ Отклонено'}
    
    info = (
        f"📋 Отправка #{submission.id}\n"
        f"📅 Дата: {submission.submission_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"👤 Пользователь: {submission.user_info}\n"
        f"📄 Тип: {submission.content_type}\n"
        f"📝 Описание: {submission.caption or 'Нет описания'}\n"
        f"📊 Статус: {status_ru.get(submission.status, submission.status)}\n"
        f"🆔 Telegram ID: {submission.telegram_id}"
    )
    
    if submission.admin_comment:
        info += f"\n💬 Комментарий админа: {submission.admin_comment}"
    
    await message.answer(info)

@dp.message(Command("pending"))
async def cmd_pending(message: types.Message):
    """Просмотр ожидающих модерации отправок"""
    if not await is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    
    with get_session() as session:
        # Только ожидающие модерации
        submissions = session.query(Submission).filter_by(
            status='pending'
        ).order_by(Submission.submission_date.asc()).all()
    
    if not submissions:
        await message.answer("✅ Нет отправок ожидающих модерации.")
        return
    
    response = f"⏳ Ожидают модерации ({len(submissions)}):\n\n"
    
    for sub in submissions:
        content_emoji = {'photo': '📸', 'video': '🎥', 'text': '📝'}.get(sub.content_type, '📄')
        date_str = sub.submission_date.strftime('%d.%m %H:%M')
        user_info_short = sub.user_info.split(',')[0] if ',' in sub.user_info else sub.user_info[:20]
        
        response += f"{content_emoji} #{sub.id} - {user_info_short} ({date_str})\n"
    
    response += f"\nДля просмотра: /view <ID>"
    await message.answer(response)

@dp.message(Command("approve"))
async def cmd_approve(message: types.Message):
    """Одобрить отправку"""
    if not await is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /approve <ID> [комментарий]\nПример: /approve 1 Отличное фото!")
        return
    
    try:
        submission_id = int(args[1])
    except ValueError:
        await message.answer("ID должен быть числом")
        return
    
    comment = ' '.join(args[2:]) if len(args) > 2 else None
    
    with get_session() as session:
        submission = session.query(Submission).filter_by(id=submission_id).first()
        
        if not submission:
            await message.answer(f"❌ Отправка #{submission_id} не найдена.")
            return
        
        # Обновляем статус
        submission.status = 'approved'
        if comment:
            submission.admin_comment = comment
        
        session.commit()
        
        # Уведомляем пользователя
        try:
            await bot.send_message(
                submission.telegram_id,
                f"✅ Ваша отправка #{submission_id} одобрена!\n"
                f"{'💬 Комментарий: ' + comment if comment else ''}"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя: {e}")
    
    await message.answer(f"✅ Отправка #{submission_id} одобрена.")

@dp.message(Command("reject"))
async def cmd_reject(message: types.Message):
    """Отклонить отправку"""
    if not await is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /reject <ID> [причина]\nПример: /reject 1 Низкое качество")
        return
    
    try:
        submission_id = int(args[1])
    except ValueError:
        await message.answer("ID должен быть числом")
        return
    
    reason = ' '.join(args[2:]) if len(args) > 2 else "Отклонено модератором"
    
    with get_session() as session:
        submission = session.query(Submission).filter_by(id=submission_id).first()
        
        if not submission:
            await message.answer(f"❌ Отправка #{submission_id} не найдена.")
            return
        
        # Обновляем статус
        submission.status = 'rejected'
        submission.admin_comment = reason
        
        session.commit()
        
        # Уведомляем пользователя
        try:
            await bot.send_message(
                submission.telegram_id,
                f"❌ Ваша отправка #{submission_id} отклонена.\n"
                f"📋 Причина: {reason}"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя: {e}")
    
    await message.answer(f"❌ Отправка #{submission_id} отклонена.")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Детальная статистика"""
    if not await is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    
    with get_session() as session:
        # Статистика по типам контента
        from sqlalchemy import func
        type_stats = session.query(
            Submission.content_type,
            func.count(Submission.id).label('count')
        ).group_by(Submission.content_type).all()
        
        # Последние 7 дней
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent = session.query(Submission).filter(
            Submission.submission_date >= week_ago
        ).count()
    
    response = "📈 Детальная статистика:\n\n"
    
    # По типам
    response += "📄 По типам контента:\n"
    for content_type, count in type_stats:
        emoji = {'photo': '📸', 'video': '🎥', 'text': '📝'}.get(content_type, '📄')
        response += f"  {emoji} {content_type}: {count}\n"
    
    response += f"\n📅 За последние 7 дней: {recent}\n"
    
    await message.answer(response)

# ========== ОТПРАВКА ФОТО ==========

@dp.message(F.text == "📸 Отправить фото")
async def start_photo_submission(message: types.Message, state: FSMContext):
    """Начало отправки фото"""
    await state.update_data(content_type="photo")
    
    await message.answer(
        "📋 Прежде чем отправить фото, давайте познакомимся!\n\n"
        "Расскажите о себе в формате:\n"
        f"<b>{Config.INFO_TEMPLATE}</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ContentSubmission.waiting_for_user_info)

# ========== ОТПРАВКА ВИДЕО ==========

@dp.message(F.text == "🎥 Отправить видео")
async def start_video_submission(message: types.Message, state: FSMContext):
    """Начало отправки видео"""
    await state.update_data(content_type="video")
    
    await message.answer(
        "📋 Прежде чем отправить видео, давайте познакомимся!\n\n"
        "Расскажите о себе в формате:\n"
        f"<b>{Config.INFO_TEMPLATE}</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ContentSubmission.waiting_for_user_info)

# ========== ОТПРАВКА ТЕКСТА ==========

@dp.message(F.text == "📝 Отправить текст")
async def start_text_submission(message: types.Message, state: FSMContext):
    """Начало отправки текста"""
    await state.update_data(content_type="text")
    
    await message.answer(
        "📋 Прежде чем отправить текст, давайте познакомимся!\n\n"
        "Расскажите о себе в формате:\n"
        f"<b>{Config.INFO_TEMPLATE}</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ContentSubmission.waiting_for_user_info)

# ========== ОБРАБОТКА ФОРМЫ ==========

@dp.message(ContentSubmission.waiting_for_user_info)
async def process_user_info(message: types.Message, state: FSMContext):
    """Обработка информации о себе"""
    if len(message.text.strip()) < 10:
        await message.answer("❌ Информация слишком короткая. Пожалуйста, расскажите подробнее.")
        return
    
    await state.update_data(user_info=message.text.strip())
    
    await message.answer(
        "📝 Теперь добавьте описание:\n"
        "• Что изображено/о чем текст?\n"
        "• Почему это важно показать?",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ContentSubmission.waiting_for_caption)

@dp.message(ContentSubmission.waiting_for_caption)
async def process_caption(message: types.Message, state: FSMContext):
    """Обработка описания"""
    await state.update_data(caption=message.text.strip())
    
    data = await state.get_data()
    content_type = data.get('content_type', 'photo')
    
    if content_type in ['photo', 'video']:
        media_type = "фото" if content_type == 'photo' else "видео"
        await message.answer(
            f"📸 Теперь отправьте {media_type}\n\n"
            f"⚠️ Максимальный размер: {'10 МБ' if content_type == 'photo' else '50 МБ'}",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(ContentSubmission.waiting_for_media)
    else:
        # Для текста сразу показываем превью
        await show_preview(message, state)

async def show_preview(message: types.Message, state: FSMContext):
    """Показ превью перед отправкой"""
    data = await state.get_data()
    
    content_type = data.get('content_type', 'photo')
    user_info = data.get('user_info', '')
    caption = data.get('caption', '')
    
    content_emoji = {'photo': '📸', 'video': '🎥', 'text': '📝'}.get(content_type, '📄')
    
    preview_text = (
        f"{content_emoji} <b>Превью отправки:</b>\n\n"
        f"👤 <b>О вас:</b>\n{user_info}\n\n"
        f"📝 <b>Описание:</b>\n{caption}\n\n"
        f"✅ Все верно? Отправляем на модерацию?"
    )
    
    # Если есть фото, показываем его
    if content_type == 'photo' and 'file_id' in data:
        await message.answer_photo(
            photo=data['file_id'],
            caption=preview_text,
            parse_mode="HTML",
            reply_markup=get_confirmation_keyboard()
        )
    elif content_type == 'video' and 'file_id' in data:
        await message.answer_video(
            video=data['file_id'],
            caption=preview_text,
            parse_mode="HTML",
            reply_markup=get_confirmation_keyboard()
        )
    else:
        await message.answer(
            preview_text,
            parse_mode="HTML",
            reply_markup=get_confirmation_keyboard()
        )
    
    await state.set_state(ContentSubmission.waiting_for_confirmation)

@dp.message(ContentSubmission.waiting_for_media, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    """Обработка фото"""
    photo = message.photo[-1]
    await state.update_data(file_id=photo.file_id)
    await show_preview(message, state)

@dp.message(ContentSubmission.waiting_for_media, F.video)
async def process_video(message: types.Message, state: FSMContext):
    """Обработка видео"""
    video = message.video
    await state.update_data(file_id=video.file_id)
    await show_preview(message, state)

@dp.message(ContentSubmission.waiting_for_media)
async def process_no_media(message: types.Message):
    """Если медиа не прикреплено"""
    await message.answer(
        "❌ Вы выбрали отправку фото/видео, но не прикрепили файл.\n\n"
        "Пожалуйста, отправьте файл или отмените отправку.",
        reply_markup=get_cancel_keyboard()
    )

@dp.message(ContentSubmission.waiting_for_confirmation, F.text == "✅ Да, отправить")
async def confirm_submission(message: types.Message, state: FSMContext):
    """Подтверждение отправки"""
    data = await state.get_data()
    
    with get_session() as session:
        submission = Submission(
            telegram_id=message.from_user.id,
            user_info=data['user_info'],
            content_type=data['content_type'],
            caption=data.get('caption', ''),
            status='pending'
        )
        session.add(submission)
        session.commit()
        submission_id = submission.id
    
    # Уведомляем админов
    for admin_id in Config.ADMIN_IDS:
        try:
            content_type_ru = {'photo': 'фото', 'video': 'видео', 'text': 'текст'}.get(data['content_type'], 'контент')
            await bot.send_message(
                admin_id,
                f"🆕 Новый {content_type_ru} от сотрудника:\n"
                f"👤 {data['user_info']}\n"
                f"📋 ID: {submission_id}"
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления админа {admin_id}: {e}")
    
    await message.answer(
        "✅ Отправлено на модерацию! Мы уведомим вас о результате.",
        reply_markup=get_main_menu()
    )
    await state.clear()

@dp.message(ContentSubmission.waiting_for_confirmation, F.text == "❌ Нет, отменить")
async def cancel_confirmation(message: types.Message, state: FSMContext):
    """Отмена на этапе подтверждения"""
    await state.clear()
    await message.answer(
        "❌ Отправка отменена.",
        reply_markup=get_main_menu()
    )

# ========== ПОЛЬЗОВАТЕЛЬСКИЕ КОМАНДЫ ==========

@dp.message(F.text == "📊 Мои отправки")
async def my_submissions(message: types.Message):
    """Просмотр отправок пользователя"""
    with get_session() as session:
        submissions = session.query(Submission).filter_by(
            telegram_id=message.from_user.id
        ).order_by(Submission.submission_date.desc()).limit(10).all()
    
    if not submissions:
        await message.answer("📭 У вас пока нет отправок.")
        return
    
    response = "📋 Ваши последние отправки:\n\n"
    for sub in submissions:
        status_emoji = {'pending': '⏳', 'approved': '✅', 'rejected': '❌'}.get(sub.status, '❓')
        content_emoji = {'photo': '📸', 'video': '🎥', 'text': '📝'}.get(sub.content_type, '📄')
        date_str = sub.submission_date.strftime('%d.%m.%Y')
        response += f"{status_emoji}{content_emoji} #{sub.id} - {date_str} ({sub.status})\n"
    
    await message.answer(response)

@dp.message(F.text == "ℹ️ О проекте")
async def about_project(message: types.Message):
    """Информация о проекте"""
    await message.answer(
        "🏢 <b>Проект 'Компания изнутри'</b>\n\n"
        "Цель проекта — показать реальную работу нашей компании "
        "через глаза сотрудников.\n\n"
        "<b>Что можно отправлять:</b>\n"
        "📸 Фото с рабочих мест\n"
        "🎥 Короткие видео процессов\n"
        "📝 Истории и отзывы о работе\n\n"
        "<b>Как это работает:</b>\n"
        "1. Выбираете тип контента\n"
        "2. Рассказываете о себе\n"
        "3. Добавляете описание\n"
        "4. Отправляете на модерацию\n\n"
        "Лучшие материалы будут опубликованы!",
        parse_mode="HTML"
    )

@dp.message(F.text == "🚫 Отменить отправку")
async def cancel_submission(message: types.Message, state: FSMContext):
    """Отмена отправки из любого состояния"""
    await state.clear()
    await message.answer(
        "❌ Отправка отменена.",
        reply_markup=get_main_menu()
    )

# ========== ЗАПУСК БОТА ==========

async def main():
    """Главная функция"""
    print("=" * 50)
    print("🤖 БОТ 'КОМПАНИЯ ИЗНУТРИ' ЗАПУСКАЕТСЯ")
    print("=" * 50)
    print(f"Токен: {Config.BOT_TOKEN[:20]}...")
    print(f"Админы: {Config.ADMIN_IDS}")
    print(f"База данных: {Config.DATA_DIR}\\database.db")
    print("=" * 50)
    print("Ожидание сообщений... (Ctrl+C для выхода)")
    print("\n📋 Админ команды:")
    print("/admin - панель администратора")
    print("/pending - ожидающие модерации")
    print("/view <ID> - просмотр отправки")
    print("/approve <ID> - одобрить")
    print("/reject <ID> - отклонить")
    print("=" * 50)
    
    try:
        # Оптимизированный polling
        await dp.start_polling(
            bot,
            skip_updates=True,
            allowed_updates=["message", "callback_query"],
            polling_timeout=30,
            close_bot_session=True
        )
    except KeyboardInterrupt:
        print("\n✅ Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())