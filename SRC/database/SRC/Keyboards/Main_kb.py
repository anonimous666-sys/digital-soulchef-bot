Денис Слепцов:
"""
Главные клавиатуры бота
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# ==================== ГЛАВНЫЕ КЛАВИАТУРЫ ====================

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Главная клавиатура для обычных пользователей
    """
    builder = ReplyKeyboardBuilder()
    
    # Первый ряд
    builder.add(KeyboardButton(text="📦 Склад"))
    builder.add(KeyboardButton(text="📝 ТТК"))
    
    # Второй ряд
    builder.add(KeyboardButton(text="✅ Задачи"))
    builder.add(KeyboardButton(text="📊 Отчёты"))
    
    # Третий ряд
    builder.add(KeyboardButton(text="⚙️ АКП"))
    builder.add(KeyboardButton(text="👤 Профиль"))
    
    # Четвертый ряд (меньшие кнопки)
    builder.add(KeyboardButton(text="ℹ️ Помощь"))
    builder.add(KeyboardButton(text="📞 Поддержка"))
    
    builder.adjust(2, 2, 2, 2)
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """
    Главная клавиатура для администраторов
    """
    builder = ReplyKeyboardBuilder()
    
    # Первый ряд
    builder.add(KeyboardButton(text="📦 Склад"))
    builder.add(KeyboardButton(text="📝 ТТК"))
    
    # Второй ряд
    builder.add(KeyboardButton(text="✅ Задачи"))
    builder.add(KeyboardButton(text="📊 Отчёты"))
    
    # Третий ряд
    builder.add(KeyboardButton(text="👑 Админ-панель"))
    builder.add(KeyboardButton(text="👤 Профиль"))
    
    builder.adjust(2, 2, 2)
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)

# ==================== ИНЛАЙН КЛАВИАТУРЫ ====================

def get_main_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Главная inline клавиатура
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="📦 Склад", callback_data="menu_warehouse"),
        InlineKeyboardButton(text="📝 ТТК", callback_data="menu_ttk"),
        InlineKeyboardButton(text="✅ Задачи", callback_data="menu_tasks"),
        InlineKeyboardButton(text="📊 Отчёты", callback_data="menu_reports"),
        InlineKeyboardButton(text="⚙️ АКП", callback_data="menu_akp"),
        InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile"),
    )
    
    builder.adjust(2, 2, 2)
    
    return builder.as_markup()

def get_back_keyboard(back_to: str = "main") -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой "Назад"
    
    Args:
        back_to: Куда вернуться (main, warehouse, ttk, tasks, reports)
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_{back_to}"),
        InlineKeyboardButton(text="🏠 Главная", callback_data="back_main")
    )
    
    return builder.as_markup()

def get_confirm_keyboard(action: str, item_id: int = None) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения действия
    
    Args:
        action: Действие (delete, approve, reject, confirm)
        item_id: ID элемента (опционально)
    """
    builder = InlineKeyboardBuilder()
    
    if item_id:
        builder.add(
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{action}_{item_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{action}_{item_id}")
        )
    else:
        builder.add(
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}")
        )
    
    return builder.as_markup()

def get_pagination_keyboard(page: int, total_pages: int, 
                          action_prefix: str, item_id: int = None) -> InlineKeyboardMarkup:
    """
    Клавиатура пагинации
    
    Args:
        page: Текущая страница
        total_pages: Всего страниц
        action_prefix: Префикс для callback_data
        item_id: ID элемента (опционально)
    """
    builder = InlineKeyboardBuilder()

# Кнопки навигации
    if page > 1:
        builder.add(InlineKeyboardButton(
            text="⬅️ Предыдущая", 
            callback_data=f"{action_prefix}_page_{page-1}"
        ))
    
    builder.add(InlineKeyboardButton(
        text=f"{page}/{total_pages}", 
        callback_data="current_page"
    ))
    
    if page < total_pages:
        builder.add(InlineKeyboardButton(
            text="Следующая ➡️", 
            callback_data=f"{action_prefix}_page_{page+1}"
        ))
    
    builder.adjust(3)
    
    # Добавляем кнопку "На главную"
    row_builder = InlineKeyboardBuilder()
    row_builder.add(InlineKeyboardButton(
        text="🏠 На главную", 
        callback_data="back_main"
    ))
    
    builder.attach(row_builder)
    
    return builder.as_markup()

# ==================== КЛАВИАТУРА ВЫБОРА ====================

def get_selection_keyboard(items: list, action_prefix: str, 
                          page: int = 1, items_per_page: int = 8) -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора из списка
    
    Args:
        items: Список элементов для выбора
        action_prefix: Префикс для callback_data
        page: Текущая страница
        items_per_page: Количество элементов на странице
    """
    builder = InlineKeyboardBuilder()
    
    # Вычисляем элементы для текущей страницы
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_items = items[start_idx:end_idx]
    
    # Добавляем кнопки для элементов
    for item in page_items:
        if isinstance(item, tuple) and len(item) >= 2:
            # Если передали кортеж (id, name)
            item_id, item_name = item[0], item[1]
            builder.add(InlineKeyboardButton(
                text=item_name,
                callback_data=f"{action_prefix}_{item_id}"
            ))
        else:
            # Если передали просто строку
            builder.add(InlineKeyboardButton(
                text=str(item),
                callback_data=f"{action_prefix}_{item}"
            ))
    
    # Вычисляем количество страниц
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    
    # Добавляем пагинацию, если нужно
    if total_pages > 1:
        pagination_builder = InlineKeyboardBuilder()
        
        if page > 1:
            pagination_builder.add(InlineKeyboardButton(
                text="⬅️", 
                callback_data=f"{action_prefix}_page_{page-1}"
            ))
        
        pagination_builder.add(InlineKeyboardButton(
            text=f"{page}/{total_pages}", 
            callback_data="current_page"
        ))
        
        if page < total_pages:
            pagination_builder.add(InlineKeyboardButton(
                text="➡️", 
                callback_data=f"{action_prefix}_page_{page+1}"
            ))
        
        pagination_builder.adjust(3)
        builder.attach(pagination_builder)
    
    # Добавляем кнопку отмены
    cancel_builder = InlineKeyboardBuilder()
    cancel_builder.add(InlineKeyboardButton(
        text="❌ Отмена", 
        callback_data="cancel_selection"
    ))
    
    builder.attach(cancel_builder)
    
    # Настраиваем расположение
    builder.adjust(2)  # 2 кнопки в ряд
    
    return builder.as_markup()

# ==================== КЛАВИАТУРА ДЛЯ ФОРМ ====================

def get_form_keyboard(steps: list, current_step: int, 
                     can_skip: bool = False) -> InlineKeyboardMarkup:
    """
    Клавиатура для пошаговых форм
    
    Args:
        steps: Список шагов
        current_step: Текущий шаг
        can_skip: Можно ли пропустить шаг
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Пропустить" если можно
    if can_skip:
        builder.add(InlineKeyboardButton(
            text="⏭️ Пропустить", 
            callback_data="form_skip"
        ))
    
    # Кнопка "Назад" если не первый шаг
    if current_step > 0:
        builder.add(InlineKeyboardButton(
            text="⬅️ Назад", 
            callback_data="form_back"
        ))
    
    # Кнопка "Далее" или "Готово"

if current_step < len(steps) - 1:
        builder.add(InlineKeyboardButton(
            text="Далее ➡️", 
            callback_data="form_next"
        ))
    else:
        builder.add(InlineKeyboardButton(
            text="✅ Готово", 
            callback_data="form_done"
        ))
    
    # Кнопка отмены
    builder.add(InlineKeyboardButton(
        text="❌ Отмена", 
        callback_data="form_cancel"
    ))
    
    builder.adjust(2, 2)
    
    return builder.as_markup()

# Экспорт клавиатур
all = [
    'get_main_keyboard',
    'get_admin_keyboard',
    'get_main_inline_keyboard',
    'get_back_keyboard',
    'get_confirm_keyboard',
    'get_pagination_keyboard',
    'get_selection_keyboard',
    'get_form_keyboard',
]
