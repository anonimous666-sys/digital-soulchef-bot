#!/usr/bin/env python3
"""
Цифровой Су-Шеф - Telegram бот для автоматизации кухни
Основной модуль запуска
"""

import asyncio
import logging
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties
import redis.asyncio as redis

from src.config.settings import settings
from src.database.connections import init_db, get_db
from src.database.crud import create_user
from src.keyboards.main_kb import get_main_keyboard, get_admin_keyboard
from src.utils.logger import setup_logging

# Настройка логирования
logger = setup_logging()

# Инициализация бота и диспетчера
bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Глобальные переменные
ADMIN_IDS = settings.admin_ids

# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name
    
    try:
        async for session in get_db():
            # Проверяем, есть ли пользователь в БД
            from src.database.crud import get_user
            user = await get_user(session, user_id)
            
            if not user:
                # Регистрируем нового пользователя
                user_data = {
                    "user_id": user_id,
                    "username": username,
                    "role": "повар" if user_id not in ADMIN_IDS else "администратор",
                    "workplace": "Главная кухня"
                }
                await create_user(session, user_data)
                logger.info(f"Новый пользователь: {user_id} ({full_name})")
            
        # Приветственное сообщение
        welcome_text = f"""
👨‍🍳 <b>Добро пожаловать, {full_name}!</b>

<b>Цифровой Су-Шеф</b> - ваш помощник в автоматизации кухни:

📦 <b>Склад:</b> Учёт продуктов, приход/расход
📝 <b>ТТК:</b> Технико-технологические карты
✅ <b>Задачи:</b> Чек-листы и поручения
📊 <b>Отчёты:</b> Аналитика и контроль
⚙️ <b>АКП:</b> Контроль критических точек

Используйте меню или команды для работы.
"""
        
        if user_id in ADMIN_IDS:
            await message.answer(welcome_text, reply_markup=get_admin_keyboard())
        else:
            await message.answer(welcome_text, reply_markup=get_main_keyboard())
            
    except Exception as e:
        logger.error(f"Ошибка при старте: {e}")
        await message.answer("⚠️ Произошла ошибка при инициализации. Попробуйте позже.")

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    """Главное меню"""
    user_id = message.from_user.id
    
    if user_id in ADMIN_IDS:
        await message.answer("📋 <b>Меню администратора:</b>", reply_markup=get_admin_keyboard())
    else:
        await message.answer("📋 <b>Главное меню:</b>", reply_markup=get_main_keyboard())

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Справка по командам"""
    help_text = """
<b>Список доступных команд:</b>

🔄 <b>Основные команды:</b>
/start - Начать работу с ботом
/menu - Главное меню
/help - Эта справка
/profile - Мой профиль

📦 <b>Склад:</b>
/warehouse - Управление складом
/arrival - Приход товара
/inventory - Инвентаризация
/stocks - Остатки

📝 <b>ТТК:</b>
/ttk_list - Список ТТК
/new_ttk - Создать ТТК
/find_ttk - Поиск ТТК

✅ <b>Задачи:</b>
/tasks - Мои задачи
/new_task - Новая задача
/checklist - Чек-листы

📊 <b>Отчёты:</b>
/report_today - Отчёт за сегодня
/report_week - Отчёт за неделю
/waste - Списания

⚙️ <b>Администрирование:</b>
/users - Пользователи
/backup - Резервная копия
/logs - Логи системы

<b>Или используйте кнопки меню ↓</b>
"""
    await message.answer(help_text)

# ==================== ОБРАБОТЧИКИ МЕНЮ ====================

@dp.message(lambda message: message.text == "📦 Склад")
async def warehouse_handler(message: types.Message):
    """Обработчик кнопки 'Склад'"""
    from src.keyboards.warehouse_kb import get_warehouse_keyboard
    await message.answer("📦 <b>Управление складом:</b>", reply_markup=get_warehouse_keyboard())

@dp.message(lambda message: message.text == "📝 ТТК")
async def ttk_handler(message: types.Message):
    """Обработчик кнопки 'ТТК'"""
    from src.keyboards.ttk_kb import get_ttk_keyboard
    await message.answer("📝 <b>Технико-Технологические Карты:</b>", reply_markup=get_ttk_keyboard())

@dp.message(lambda message: message.text == "✅ Задачи")
async def tasks_handler(message: types.Message):
    """Обработчик кнопки 'Задачи'"""
    from src.keyboards.tasks_kb import get_tasks_keyboard
    await message.answer("✅ <b>Задачи и чек-листы:</b>", reply_markup=get_tasks_keyboard())

@dp.message(lambda message: message.text == "📊 Отчёты")
async def reports_handler(message: types.Message):
    """Обработчик кнопки 'Отчёты'"""
    from src.keyboards.reports_kb import get_reports_keyboard
    await message.answer("📊 <b>Отчёты и аналитика:</b>", reply_markup=get_reports_keyboard())

@dp.message(lambda message: message.text == "⚙️ АКП")
async def akp_handler(message: types.Message):
    """Обработчик кнопки 'АКП'"""
    from src.keyboards.akp_kb import get_akp_keyboard
    await message.answer("⚙️ <b>Анализ Критических Пределов:</b>", reply_markup=get_akp_keyboard())

@dp.message(lambda message: message.text == "👤 Профиль")
async def profile_handler(message: types.Message):
    """Обработчик кнопки 'Профиль'"""
    user = message.from_user
    profile_text = f"""
<b>👤 Ваш профиль:</b>

🆔 ID: <code>{user.id}</code>
👤 Имя: {user.full_name}
📱 Username: @{user.username or 'не указан'}

🕐 Регистрация: {datetime.now().strftime('%d.%m.%Y %H:%M')}
📊 Статус: {'👑 Администратор' if user.id in ADMIN_IDS else '👨‍🍳 Повар'}

<b>Доступные функции:</b>
• Управление складом
• Работа с ТТК
• Выполнение задач
• Просмотр отчётов
"""
    await message.answer(profile_text)

# ==================== АДМИН ПАНЕЛЬ ====================

@dp.message(lambda message: message.text == "👑 Админ-панель")
async def admin_panel_handler(message: types.Message):
    """Обработчик кнопки 'Админ-панель'"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет прав доступа к админ-панели.")
        return
    
    admin_text = """
<b>👑 Административная панель:</b>

📊 <b>Статистика:</b>
• Пользователей: 15
• Товаров на складе: 47
• Активных задач: 8
• ТТК в базе: 32

⚙️ <b>Управление:</b>
• Пользователи и роли
• Резервные копии
• Системные логи
• Настройки бота
"""
    from src.keyboards.admin_kb import get_admin_panel_keyboard
    await message.answer(admin_text, reply_markup=get_admin_panel_keyboard())

@dp.message(lambda message: message.text == "📊 Статистика")
async def admin_stats_handler(message: types.Message):
    """Статистика системы"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        async for session in get_db():
            from src.database.crud import (
                get_users_count, get_products_count, 
                get_active_tasks_count, get_ttk_count
            )
            
            stats_text = f"""
<b>📊 Статистика системы:</b>

👥 <b>Пользователи:</b> {await get_users_count(session)}
📦 <b>Товары на складе:</b> {await get_products_count(session)}
✅ <b>Активные задачи:</b> {await get_active_tasks_count(session)}
📝 <b>ТТК в базе:</b> {await get_ttk_count(session)}

<b>Последние действия:</b>
• Приход картофеля: 50кг (10.12.2024)
• Создана ТТК "Борщ" (10.12.2024)
• Завершена задача "Уборка" (09.12.2024)
"""
            await message.answer(stats_text)
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await message.answer("⚠️ Ошибка получения статистики")

# ==================== ЗАПУСК БОТА ====================

async def main():
    """Основная функция запуска бота"""
    try:
        # Инициализация Redis для хранения состояний
        redis_client = redis.Redis(
