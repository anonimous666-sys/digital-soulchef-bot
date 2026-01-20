Денис Слепцов:
"""
Обработчики для работы со складом
"""

import logging
from datetime import datetime, date
from typing import Optional, Dict, Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database.connections import get_db
from src.database.crud import product_crud, arrival_crud
from src.keyboards.warehouse_kb import (
    get_warehouse_keyboard, get_warehouse_inline_keyboard,
    get_product_categories_keyboard, get_units_keyboard
)
from src.keyboards.main_kb import get_back_keyboard, get_pagination_keyboard
from src.utils.formatters import format_product_info, format_arrival_info

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаём роутер
router = Router()

# ==================== СОСТОЯНИЯ FSM ====================

class WarehouseStates(StatesGroup):
    """Состояния для работы со складом"""
    waiting_for_product_name = State()
    waiting_for_product_category = State()
    waiting_for_product_unit = State()
    waiting_for_product_quantity = State()
    waiting_for_product_min_stock = State()
    waiting_for_product_price = State()
    
    waiting_for_arrival_product = State()
    waiting_for_arrival_quantity = State()
    waiting_for_arrival_price = State()
    waiting_for_arrival_supplier = State()
    waiting_for_arrival_batch = State()
    
    waiting_for_inventory_product = State()
    waiting_for_inventory_quantity = State()
    
    waiting_for_waste_product = State()
    waiting_for_waste_quantity = State()
    waiting_for_waste_reason = State()

# ==================== КОМАНДЫ ====================

@router.message(Command("warehouse"))
@router.message(F.text == "📦 Склад")
async def cmd_warehouse(message: Message):
    """Обработчик команды /warehouse"""
    await message.answer(
        "📦 <b>Управление складом</b>\n\n"
        "Выберите действие:",
        reply_markup=get_warehouse_inline_keyboard()
    )

@router.message(Command("stocks"))
async def cmd_stocks(message: Message):
    """Показать остатки на складе"""
    try:
        async for session in get_db():
            # Получаем все активные продукты
            result = await session.execute(
                "SELECT name, current_stock, unit, min_stock FROM products WHERE is_active = TRUE ORDER BY name"
            )
            products = result.fetchall()
            
            if not products:
                await message.answer("📦 На складе нет товаров.")
                return
            
            # Формируем сообщение
            stocks_text = "📊 <b>Остатки на складе:</b>\n\n"
            
            for product in products[:20]:  # Ограничиваем 20 товарами
                name, stock, unit, min_stock = product
                status = "⚠️" if stock <= min_stock else "✅"
                stocks_text += f"{status} <b>{name}</b>: {stock} {unit}\n"
            
            if len(products) > 20:
                stocks_text += f"\n... и ещё {len(products) - 20} товаров"
            
            await message.answer(stocks_text)
            
    except Exception as e:
        logger.error(f"Ошибка при получении остатков: {e}")
        await message.answer("❌ Ошибка при получении информации со склада.")

@router.message(Command("lowstock"))
async def cmd_low_stock(message: Message):
    """Показать товары с низким запасом"""
    try:
        async for session in get_db():
            low_stock_products = await product_crud.get_low_stock_products(session)
            
            if not low_stock_products:
                await message.answer("✅ На складе нет товаров с низким запасом.")
                return
            
            low_stock_text = "⚠️ <b>Товары с низким запасом:</b>\n\n"
            
            for product in low_stock_products:
                low_stock_text += (
                    f"• <b>{product.name}</b>\n"
                    f"  Остаток: {product.current_stock} {product.unit}\n"

f"  Минимальный: {product.min_stock} {product.unit}\n\n"
                )
            
            await message.answer(low_stock_text)
            
    except Exception as e:
        logger.error(f"Ошибка при получении низких запасов: {e}")
        await message.answer("❌ Ошибка при получении информации о низких запасах.")

# ==================== INLINE ОБРАБОТЧИКИ ====================

@router.callback_query(F.data == "warehouse_products")
async def show_products(callback: CallbackQuery):
    """Показать все продукты"""
    try:
        async for session in get_db():
            products = await product_crud.search_products(session, "", limit=50)
            
            if not products:
                await callback.message.edit_text(
                    "📦 На складе нет товаров.",
                    reply_markup=get_back_keyboard("warehouse")
                )
                return
            
            products_text = "📦 <b>Товары на складе:</b>\n\n"
            
            for i, product in enumerate(products[:10], 1):
                products_text += format_product_info(product, short=True)
            
            if len(products) > 10:
                products_text += f"\n... и ещё {len(products) - 10} товаров"
            
            await callback.message.edit_text(
                products_text,
                reply_markup=get_back_keyboard("warehouse")
            )
            
    except Exception as e:
        logger.error(f"Ошибка при показе продуктов: {e}")
        await callback.answer("❌ Ошибка при загрузке товаров")

@router.callback_query(F.data == "warehouse_arrival")
async def start_arrival(callback: CallbackQuery, state: FSMContext):
    """Начать процесс приёма товара"""
    await callback.message.edit_text(
        "📥 <b>Приём товара на склад</b>\n\n"
        "Введите название товара:",
        reply_markup=get_back_keyboard("warehouse")
    )
    await state.set_state(WarehouseStates.waiting_for_arrival_product)

@router.message(WarehouseStates.waiting_for_arrival_product)
async def process_arrival_product(message: Message, state: FSMContext):
    """Обработка названия товара для приёма"""
    product_name = message.text.strip()
    
    # Ищем товар в базе
    try:
        async for session in get_db():
            products = await product_crud.search_products(session, product_name, limit=5)
            
            if products:
                # Нашли товар, просим выбрать из списка
                await state.update_data(product_search=product_name)
                
                products_text = "🔍 <b>Найденные товары:</b>\n\n"
                for i, product in enumerate(products, 1):
                    products_text += f"{i}. {product.name} ({product.category})\n"
                
                products_text += "\nВыберите номер товара или введите новый:"
                
                await message.answer(
                    products_text,
                    reply_markup=get_back_keyboard("warehouse")
                )
            else:
                # Товар не найден, создаём новый
                await state.update_data(new_product_name=product_name)
                await message.answer(
                    f"🆕 Товар '{product_name}' не найден.\n"
                    "Введите категорию товара:",
                    reply_markup=get_back_keyboard("warehouse")
                )
                await state.set_state(WarehouseStates.waiting_for_product_category)
                
    except Exception as e:
        logger.error(f"Ошибка при поиске товара: {e}")
        await message.answer("❌ Ошибка при поиске товара.")

@router.message(WarehouseStates.waiting_for_arrival_quantity)
async def process_arrival_quantity(message: Message, state: FSMContext):
    """Обработка количества товара"""
    try:
        quantity = float(message.text.replace(',', '.'))
        
        if quantity <= 0:
            await message.answer("❌ Количество должно быть больше 0.")
            return
        
        await state.update_data(arrival_quantity=quantity)

# Получаем данные из состояния
        data = await state.get_data()
        product_name = data.get('arrival_product_name', 'товар')
        
        await message.answer(
            f"📦 Товар: <b>{product_name}</b>\n"
            f"Количество: <b>{quantity}</b>\n\n"
            "Введите цену за единицу (руб):",
            reply_markup=get_back_keyboard("warehouse")
        )
        
        await state.set_state(WarehouseStates.waiting_for_arrival_price)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")

@router.message(WarehouseStates.waiting_for_arrival_price)
async def process_arrival_price(message: Message, state: FSMContext):
    """Обработка цены товара"""
    try:
        price = float(message.text.replace(',', '.'))
        
        if price <= 0:
            await message.answer("❌ Цена должна быть больше 0.")
            return
        
        await state.update_data(arrival_price=price)
        
        # Рассчитываем общую стоимость
        data = await state.get_data()
        quantity = data.get('arrival_quantity', 0)
        total_price = quantity * price
        
        await message.answer(
            f"💰 Цена: <b>{price:.2f} руб.</b>\n"
            f"Общая стоимость: <b>{total_price:.2f} руб.</b>\n\n"
            "Введите поставщика (или '-' если не нужно):",
            reply_markup=get_back_keyboard("warehouse")
        )
        
        await state.set_state(WarehouseStates.waiting_for_arrival_supplier)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")

@router.message(WarehouseStates.waiting_for_arrival_supplier)
async def process_arrival_supplier(message: Message, state: FSMContext):
    """Обработка поставщика"""
    supplier = message.text.strip()
    if supplier == '-':
        supplier = None
    
    await state.update_data(arrival_supplier=supplier)
    
    await message.answer(
        "Введите номер партии (или '-' если не нужно):",
        reply_markup=get_back_keyboard("warehouse")
    )
    
    await state.set_state(WarehouseStates.waiting_for_arrival_batch)

@router.message(WarehouseStates.waiting_for_arrival_batch)
async def process_arrival_batch(message: Message, state: FSMContext):
    """Обработка номера партии и завершение приёма"""
    batch_number = message.text.strip()
    if batch_number == '-':
        batch_number = None
    
    # Получаем все данные
    data = await state.get_data()
    
    product_name = data.get('arrival_product_name')
    product_id = data.get('arrival_product_id')
    quantity = data.get('arrival_quantity')
    price = data.get('arrival_price')
    supplier = data.get('arrival_supplier')
    
    try:
        async for session in get_db():
            # Создаём запись о приходе
            arrival_data = {
                'product_id': product_id,
                'quantity': quantity,
                'price_per_unit': price,
                'received_by': message.from_user.id,
                'receiver_name': message.from_user.full_name,
                'supplier_name': supplier,
                'batch_number': batch_number
            }
            
            arrival = await arrival_crud.create_arrival(session, arrival_data)
            
            # Формируем сообщение об успехе
            success_text = (
                "✅ <b>Товар успешно принят!</b>\n\n"
                f"📦 Товар: <b>{product_name}</b>\n"
                f"📊 Количество: <b>{quantity}</b>\n"
                f"💰 Цена: <b>{price:.2f} руб./ед.</b>\n"
                f"💵 Общая стоимость: <b>{arrival.total_price:.2f} руб.</b>\n"
            )
            
            if supplier:
                success_text += f"🏭 Поставщик: <b>{supplier}</b>\n"
            
            if batch_number:
                success_text += f"🏷️ Партия: <b>{batch_number}</b>\n"
            
            success_text += f"\n🕐 Дата: <b>{arrival.received_at.strftime('%d.%m.%Y %H:%M')}</b>"
            
            await message.answer(
                success_text,

reply_markup=get_warehouse_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Ошибка при приёме товара: {e}")
        await message.answer(
            "❌ Ошибка при приёме товара.",
            reply_markup=get_warehouse_keyboard()
        )
    
    # Очищаем состояние
    await state.clear()

# ==================== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ====================

@router.callback_query(F.data == "warehouse_today_arrivals")
async def show_today_arrivals(callback: CallbackQuery):
    """Показать приходы за сегодня"""
    try:
        async for session in get_db():
            arrivals = await arrival_crud.get_today_arrivals(session)
            
            if not arrivals:
                await callback.message.edit_text(
                    "📅 <b>Сегодня не было приходов товара.</b>",
                    reply_markup=get_back_keyboard("warehouse")
                )
                return
            
            arrivals_text = "📥 <b>Приходы за сегодня:</b>\n\n"
            total_cost = 0
            
            for arrival in arrivals[:10]:  # Ограничиваем 10 приходами
                arrivals_text += format_arrival_info(arrival, short=True)
                total_cost += arrival.total_price
            
            arrivals_text += f"\n💵 <b>Общая стоимость: {total_cost:.2f} руб.</b>"
            
            if len(arrivals) > 10:
                arrivals_text += f"\n\n... и ещё {len(arrivals) - 10} приходов"
            
            await callback.message.edit_text(
                arrivals_text,
                reply_markup=get_back_keyboard("warehouse")
            )
            
    except Exception as e:
        logger.error(f"Ошибка при показе приходов: {e}")
        await callback.answer("❌ Ошибка при загрузке приходов")

@router.callback_query(F.data.startswith("warehouse_product_"))
async def show_product_detail(callback: CallbackQuery):
    """Показать детальную информацию о товаре"""
    try:
        product_id = int(callback.data.split("_")[-1])
        
        async for session in get_db():
            product = await product_crud.get_product(session, product_id)
            
            if not product:
                await callback.answer("Товар не найден")
                return
            
            # Формируем детальную информацию
            detail_text = format_product_info(product, detailed=True)
            
            # Получаем историю приходов
            result = await session.execute(
                "SELECT received_at, quantity, price_per_unit FROM arrivals "
                "WHERE product_id = :product_id ORDER BY received_at DESC LIMIT 5",
                {"product_id": product_id}
            )
            arrivals = result.fetchall()
            
            if arrivals:
                detail_text += "\n\n📥 <b>Последние приходы:</b>\n"
                for arrival in arrivals:
                    received_at, quantity, price = arrival
                    detail_text += (
                        f"• {received_at.strftime('%d.%m.%Y')}: "
                        f"{quantity} {product.unit} по {price:.2f} руб.\n"
                    )
            
            await callback.message.edit_text(
                detail_text,
                reply_markup=get_back_keyboard("warehouse")
            )
            
    except Exception as e:
        logger.error(f"Ошибка при показе товара: {e}")
        await callback.answer("❌ Ошибка при загрузке информации")

# Экспортируем роутер
all = ['router', 'WarehouseStates']
