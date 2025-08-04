"""
Обработчики команд и сообщений Telegram бота
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database import BotDatabase
from bot.keyboards import (
    get_main_menu, get_settings_menu, get_admin_menu,
    get_days_keyboard, get_time_keyboard, get_back_keyboard,
    get_description_keyboard, get_admin_list_keyboard, get_confirm_delete_keyboard
)

# Состояния для FSM
class AdminStates(StatesGroup):
    waiting_for_admin_id = State()
    waiting_for_description = State()

class ScheduleStates(StatesGroup):
    waiting_for_day = State()
    waiting_for_time = State()

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, db: BotDatabase):
    """Обработчик команды /start"""
    if not await db.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав доступа к этому боту.")
        return
    
    await message.answer(
        f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
        "🤖 Это бот для управления уведомлениями о новых товарах.\n"
        "Выберите действие из меню:",
        reply_markup=get_main_menu()
    )

@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: Message, db: BotDatabase):
    """Меню настроек"""
    if not await db.is_admin(message.from_user.id):
        return
    
    await message.answer(
        "⚙️ Настройки бота\n\n"
        "Выберите что хотите настроить:",
        reply_markup=get_settings_menu()
    )

@router.message(F.text == "👥 Управление админами")
async def admin_menu(message: Message, db: BotDatabase):
    """Меню управления администраторами"""
    if not await db.is_admin(message.from_user.id):
        return
    
    await message.answer(
        "👥 Управление администраторами\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu()
    )

@router.message(F.text == "🕐 Настроить расписание")
async def schedule_setup(message: Message, state: FSMContext, db: BotDatabase):
    """Настройка расписания"""
    if not await db.is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📅 Настройка расписания парсинга\n\n"
        "Выберите день недели для запуска парсинга:",
        reply_markup=get_days_keyboard()
    )
    await state.set_state(ScheduleStates.waiting_for_day)

@router.callback_query(F.data.startswith("day_"), StateFilter(ScheduleStates.waiting_for_day))
async def process_day_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора дня недели"""
    day = callback.data.split("_")[1]
    await state.update_data(selected_day=day)
    
    day_names = {
        "monday": "Понедельник",
        "tuesday": "Вторник", 
        "wednesday": "Среда",
        "thursday": "Четверг",
        "friday": "Пятница",
        "saturday": "Суббота",
        "sunday": "Воскресенье"
    }
    
    await callback.message.edit_text(
        f"📅 Выбран день: {day_names.get(day, day)}\n\n"
        "🕐 Теперь выберите время запуска:",
        reply_markup=get_time_keyboard()
    )
    await state.set_state(ScheduleStates.waiting_for_time)
    await callback.answer()

@router.callback_query(F.data.startswith("time_"), StateFilter(ScheduleStates.waiting_for_time))
async def process_time_selection(callback: CallbackQuery, state: FSMContext, db: BotDatabase, scheduler=None):
    """Обработка выбора времени"""
    time = callback.data.split("_")[1]
    data = await state.get_data()
    selected_day = data.get("selected_day")
    
    # Сохраняем настройки в базу данных
    success = await db.update_scheduler_settings(time, selected_day, callback.from_user.id)
    
    day_names = {
        "monday": "Понедельник",
        "tuesday": "Вторник",
        "wednesday": "Среда", 
        "thursday": "Четверг",
        "friday": "Пятница",
        "saturday": "Суббота",
        "sunday": "Воскресенье"
    }
    
    if success:
        await callback.message.edit_text(
            f"✅ Расписание успешно настроено!\n\n"
            f"📅 День: {day_names.get(selected_day, selected_day)}\n"
            f"🕐 Время: {time}\n\n"
            f"🔄 Планировщик перезапускается..."
        )
        
        # Перезапускаем планировщик с новыми настройками
        if scheduler:
            try:
                await scheduler.restart_scheduler()
                await callback.message.edit_text(
                    f"✅ Расписание успешно настроено!\n\n"
                    f"📅 День: {day_names.get(selected_day, selected_day)}\n"
                    f"🕐 Время: {time}\n\n"
                    f"✅ Планировщик перезапущен."
                )
            except Exception as e:
                await callback.message.edit_text(
                    f"✅ Настройки сохранены, но возникла ошибка при перезапуске планировщика.\n\n"
                    f"❌ Ошибка: {str(e)[:100]}\n\n"
                    f"Перезапустите бота для применения изменений."
                )
        
    else:
        await callback.message.edit_text(
            "❌ Ошибка при сохранении настроек. Попробуйте еще раз."
        )
    
    await state.clear()
    await callback.answer()

@router.message(F.text == "🚀 Начать парсинг")
async def start_manual_parsing(message: Message, db: BotDatabase, scheduler=None):
    """Ручной запуск разового парсинга"""
    if not await db.is_admin(message.from_user.id):
        return
    
    if scheduler:
        # Проверяем статус парсера
        if scheduler.parser_lock.is_running():
            await message.answer(
                "⚠️ Парсер уже запущен!\n\n"
                "Дождитесь завершения текущего процесса парсинга."
            )
            return
        
        await message.answer(
            "🚀 Запуск разового парсинга...\n\n"
            "⏳ Это может занять несколько минут. Вы получите уведомления о найденных товарах."
        )
        
        # Запускаем парсинг асинхронно, не блокируя основной поток
        import asyncio
        
        async def run_parsing_async():
            """Запуск парсинга асинхронно"""
            try:
                await scheduler.scheduled_parsing_job(user_id=message.from_user.id)
            except Exception as e:
                logging.error(f"Ошибка при парсинге: {e}")
                await scheduler.notification_service.send_message_to_user(
                    message.from_user.id,
                    f"❌ Ошибка при парсинге:\n\n🚨 {str(e)[:200]}"
                )
        
        # Запускаем задачу в фоне
        asyncio.create_task(run_parsing_async())
    else:
        await message.answer("❌ Планировщик недоступен. Перезапустите бота.")

@router.message(F.text == "📋 Текущие настройки")
async def current_settings(message: Message, db: BotDatabase):
    """Показать текущие настройки"""
    if not await db.is_admin(message.from_user.id):
        return
    
    schedule_time, schedule_day = await db.get_scheduler_settings()
    
    day_names = {
        "monday": "Понедельник",
        "tuesday": "Вторник",
        "wednesday": "Среда",
        "thursday": "Четверг", 
        "friday": "Пятница",
        "saturday": "Суббота",
        "sunday": "Воскресенье"
    }
    
    await message.answer(
        f"📋 Текущие настройки:\n\n"
        f"📅 День: {day_names.get(schedule_day, schedule_day)}\n"
        f"🕐 Время: {schedule_time}\n\n"
        f"⏰ Следующий запуск будет выполнен автоматически."
    )

@router.message(F.text == "➕ Добавить админа")
async def add_admin_start(message: Message, state: FSMContext, db: BotDatabase):
    """Начало процесса добавления администратора"""
    if not await db.is_admin(message.from_user.id):
        return
    
    await message.answer(
        "👤 Добавление нового администратора\n\n"
        "Отправьте ID пользователя, которого хотите сделать администратором.\n\n"
        "💡 ID можно узнать у @userinfobot",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_admin_id)

@router.message(StateFilter(AdminStates.waiting_for_admin_id))
async def process_admin_id(message: Message, state: FSMContext, db: BotDatabase):
    """Обработка ID нового администратора"""
    if message.text == "🔙 Назад":
        await state.clear()
        await admin_menu(message, db)
        return
    
    try:
        user_id = int(message.text.strip())
        
        # Проверяем, не является ли пользователь уже администратором
        if await db.is_admin(user_id):
            await message.answer("⚠️ Этот пользователь уже является администратором.")
            return
        
        # Сохраняем ID и переходим к запросу описания
        await state.update_data(admin_id=user_id)
        
        await message.answer(
            "📝 Добавьте описание для администратора (например, имя):\n\n"
            "Это поможет вам не забыть, кто это.",
            reply_markup=get_description_keyboard()
        )
        await state.set_state(AdminStates.waiting_for_description)
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат ID. Введите числовой ID пользователя.\n\n"
            "Пример: 123456789"
        )

@router.message(StateFilter(AdminStates.waiting_for_description))
async def process_admin_description(message: Message, state: FSMContext, db: BotDatabase):
    """Обработка описания администратора"""
    if message.text == "🔙 Назад":
        await state.clear()
        await admin_menu(message, db)
        return
    
    data = await state.get_data()
    user_id = data.get("admin_id")
    description = message.text.strip()
    
    # Добавляем администратора с описанием
    success = await db.add_admin(user_id, None, description, message.from_user.id)
    
    if success:
        await message.answer(
            f"✅ Администратор добавлен!\n\n"
            f"👤 ID: {user_id}\n"
            f"📝 Описание: {description}",
            reply_markup=get_admin_menu()
        )
    else:
        await message.answer(
            "❌ Ошибка при добавлении администратора. Попробуйте еще раз.",
            reply_markup=get_admin_menu()
        )
    
    await state.clear()

@router.callback_query(F.data == "skip_description")
async def skip_description(callback: CallbackQuery, state: FSMContext, db: BotDatabase):
    """Пропуск описания администратора"""
    data = await state.get_data()
    user_id = data.get("admin_id")
    
    # Добавляем администратора без описания
    success = await db.add_admin(user_id, None, None, callback.from_user.id)
    
    if success:
        await callback.message.edit_text(
            f"✅ Администратор добавлен!\n\n"
            f"👤 ID: {user_id}"
        )
        await callback.message.answer("Возвращаемся в меню управления администраторами.", reply_markup=get_admin_menu())
    else:
        await callback.message.edit_text("❌ Ошибка при добавлении администратора.")
        await callback.message.answer("Попробуйте еще раз.", reply_markup=get_admin_menu())
    
    await state.clear()
    await callback.answer()

@router.message(F.text == "📋 Список админов")
async def list_admins(message: Message, db: BotDatabase):
    """Показать список администраторов"""
    if not await db.is_admin(message.from_user.id):
        return
    
    admins = await db.get_all_admins()
    db_admins = await db.get_db_admins_with_description()
    
    if not admins:
        await message.answer("👥 Список администраторов пуст.")
        return
    
    admin_list = "👥 Список администраторов:\n\n"
    
    # Главный админ
    from bot.config import config
    admin_list += f"👑 Главный: {config.ADMIN_ID}\n\n"
    
    # Дополнительные админы
    if db_admins:
        admin_list += "👥 Дополнительные:\n"
        for user_id, username, description in db_admins:
            desc_text = f" ({description})" if description else ""
            admin_list += f"• {user_id}{desc_text}\n"
    else:
        admin_list += "👥 Дополнительных администраторов нет"
    
    await message.answer(admin_list)

@router.message(F.text == "Удалить админа")
async def delete_admin_start(message: Message, db: BotDatabase):
    """Начало процесса удаления администратора"""
    if not await db.is_admin(message.from_user.id):
        return
    
    # Получаем только дополнительных админов (главного удалить нельзя)
    db_admins = await db.get_db_admins_with_description()
    
    if not db_admins:
        await message.answer("👥 Нет дополнительных администраторов для удаления.")
        return
    
    await message.answer(
        "🗑️ Выберите администратора для удаления:",
        reply_markup=get_admin_list_keyboard(db_admins)
    )

@router.callback_query(F.data.startswith("delete_admin_"))
async def confirm_delete_admin(callback: CallbackQuery, db: BotDatabase):
    """Подтверждение удаления администратора"""
    user_id = int(callback.data.split("_")[2])
    
    # Получаем информацию об админе
    db_admins = await db.get_db_admins_with_description()
    admin_info = next((admin for admin in db_admins if admin[0] == user_id), None)
    
    if not admin_info:
        await callback.message.edit_text("❌ Администратор не найден.")
        return
    
    description = admin_info[2] if admin_info[2] else f"ID: {user_id}"
    
    await callback.message.edit_text(
        f"❓ Вы уверены, что хотите удалить администратора?\n\n"
        f"👤 {description}",
        reply_markup=get_confirm_delete_keyboard(user_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete_"))
async def execute_delete_admin(callback: CallbackQuery, db: BotDatabase):
    """Выполнение удаления администратора"""
    user_id = int(callback.data.split("_")[2])
    
    success = await db.remove_admin(user_id)
    
    if success:
        await callback.message.edit_text("✅ Администратор успешно удален!")
    else:
        await callback.message.edit_text("❌ Ошибка при удалении администратора.")
    
    await callback.message.answer("Возвращаемся в меню управления администраторами.", reply_markup=get_admin_menu())
    await callback.answer()

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete_admin(callback: CallbackQuery):
    """Отмена удаления администратора"""
    await callback.message.edit_text("❌ Удаление отменено.")
    await callback.message.answer("Возвращаемся в меню управления администраторами.", reply_markup=get_admin_menu())
    await callback.answer()

@router.callback_query(F.data == "stop_parsing")
async def stop_parsing(callback: CallbackQuery, db: BotDatabase, scheduler=None):
    """Принудительная остановка парсинга"""
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа", show_alert=True)
        return
    
    if scheduler:
        # Проверяем, действительно ли парсер работает
        if not scheduler.parser_lock.is_running():
            await callback.message.edit_text("ℹ️ Парсер уже остановлен.")
            await callback.answer()
            return
        
        # Принудительно останавливаем парсер
        success = scheduler.parser_lock.force_stop()
        
        if success:
            await callback.message.edit_text(
                "🛑 <b>Парсинг принудительно остановлен</b>\n\n"
                "✅ Процесс завершен\n"
                "🧹 Файлы сессии очищены\n"
                "📝 Статус изменен на 'stop'"
            )
            
            # Уведомляем всех админов об остановке
            try:
                admins = await db.get_all_admins()
                stop_message = f"""🛑 <b>Парсинг остановлен администратором</b>

👤 Остановил: {callback.from_user.first_name or callback.from_user.id}
⏰ Время: {datetime.now().strftime("%d.%m.%Y %H:%M")}

⚠️ Процесс был принудительно завершен"""
                
                for admin_id, _ in admins:
                    if admin_id != callback.from_user.id:  # Не отправляем тому, кто остановил
                        try:
                            await scheduler.notification_service.send_message_to_user(admin_id, stop_message)
                        except Exception:
                            pass
            except Exception as e:
                logging.error(f"Ошибка уведомления об остановке: {e}")
        else:
            await callback.message.edit_text(
                "❌ Ошибка при остановке парсинга.\n\n"
                "Попробуйте еще раз или перезапустите бота."
            )
    else:
        await callback.message.edit_text("❌ Планировщик недоступен.")
    
    await callback.answer()

@router.message(F.text == "📊 Статистика")
async def statistics(message: Message, db: BotDatabase, scheduler=None):
    """Показать статистику"""
    if not await db.is_admin(message.from_user.id):
        return
    
    # Получаем настройки расписания
    schedule_time, schedule_day = await db.get_scheduler_settings()
    
    day_names = {
        "monday": "Понедельник",
        "tuesday": "Вторник",
        "wednesday": "Среда",
        "thursday": "Четверг", 
        "friday": "Пятница",
        "saturday": "Суббота",
        "sunday": "Воскресенье"
    }
    
    # Проверяем статус парсера
    parser_status = "🔴 Остановлен"
    if scheduler and scheduler.parser_lock.is_running():
        parser_status = "🟢 Работает"
    
    await message.answer(
        f"📊 Статистика:\n\n"
        f"👥 Администраторов: {len(await db.get_all_admins())}\n"
        f"📅 Расписание: {day_names.get(schedule_day, schedule_day)} в {schedule_time}\n"
        f"⚙️ Статус парсера: {parser_status}"
    )

@router.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message, db: BotDatabase):
    """Показать справку"""
    if not await db.is_admin(message.from_user.id):
        return
    
    help_text = """
ℹ️ Справка по боту

🤖 Этот бот предназначен для управления уведомлениями о новых товарах.

📋 Основные функции:
• 🚀 Начать парсинг - запуск разового поиска товаров
• ⚙️ Настройки - настройка расписания парсинга
• 👥 Управление админами - добавление/удаление администраторов
• 📊 Статистика - просмотр статистики работы бота

🕐 Расписание:
По умолчанию парсинг запускается каждый понедельник в 10:00.
Вы можете изменить это в настройках.

📬 Уведомления:
Когда парсер находит новые товары, бот автоматически отправляет уведомления всем администраторам.

❓ Если у вас есть вопросы, обратитесь к разработчику.
    """
    
    await message.answer(help_text)

@router.message(F.text == "🔙 Назад")
async def back_to_main(message: Message, db: BotDatabase):
    """Возврат в главное меню"""
    if not await db.is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu()
    )

@router.message()
async def unknown_message(message: Message, db: BotDatabase):
    """Обработчик неизвестных сообщений"""
    if not await db.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав доступа к этому боту.")
        return
    
    await message.answer(
        "❓ Неизвестная команда. Используйте меню для навигации.",
        reply_markup=get_main_menu()
    )