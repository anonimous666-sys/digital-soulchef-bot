Денис Слепцов:
"""
Модели базы данных SQLAlchemy
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, 
    Boolean, ForeignKey, Text, Date, JSON, BigInteger,
    Table, MetaData, UniqueConstraint, CheckConstraint,
    Index, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime, date
import pytz
import re

# Базовый класс для моделей
Base = declarative_base()
metadata = MetaData()

# Вспомогательная таблица для many-to-many связи ТТК и продуктов
ttk_ingredients = Table(
    'ttk_ingredients',
    Base.metadata,
    Column('ttk_id', Integer, ForeignKey('ttk.id'), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('quantity', Float, nullable=False),
    Column('unit', String(20), default='кг'),
    Column('notes', Text, nullable=True)
)

class User(Base):
    """
    Модель пользователя системы
    """
    tablename = "users"
    
    # Основные поля
    user_id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Рабочие данные
    role = Column(String(50), default="повар")
    position = Column(String(100), nullable=True)
    workplace = Column(String(100), default="Главная кухня")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Настройки
    language = Column(String(10), default="ru")
    notifications_enabled = Column(Boolean, default=True)
    
    # Даты
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')), 
                        onupdate=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    last_active = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    
    # Связи
    arrivals = relationship("Arrival", back_populates="receiver")
    tasks_created = relationship("Task", foreign_keys="Task.created_by", back_populates="creator")
    tasks_assigned = relationship("Task", foreign_keys="Task.assigned_to", back_populates="assignee")
    ttk_created = relationship("TTK", back_populates="creator")
    akp_checks = relationship("AKP", back_populates="conductor")
    
    # Валидаторы
    @validates('phone')
    def validate_phone(self, key, phone):
        """Валидация номера телефона"""
        if phone and not re.match(r'^\+?[1-9]\d{1,14}$', phone):
            raise ValueError("Неверный формат телефона")
        return phone
    
    @validates('email')
    def validate_email(self, key, email):
        """Валидация email"""
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Неверный формат email")
        return email
    
    def __repr__(self):
        return f"<User(id={self.user_id}, username='{self.username}', role='{self.role}')>"

class Product(Base):
    """
    Модель продукта/ингредиента
    """
    tablename = "products"
    
    # Основные поля
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=True)
    barcode = Column(String(100), unique=True, nullable=True)
    
    # Категоризация
    category = Column(String(100), index=True)
    subcategory = Column(String(100), nullable=True)
    type = Column(String(50), default="продукт")  # продукт, полуфабрикат, готовая продукция
    
    # Единицы измерения
    unit = Column(String(20), default="кг")
    weight_per_unit = Column(Float, nullable=True)  # Вес одной единицы в кг

pieces_per_pack = Column(Integer, nullable=True)  # Штук в упаковке
    
    # Учёт
    min_stock = Column(Float, default=0)
    max_stock = Column(Float, default=100)
    current_stock = Column(Float, default=0)
    safety_stock = Column(Float, default=0)
    
    # Цены
    purchase_price = Column(Float, default=0)
    selling_price = Column(Float, default=0)
    avg_price = Column(Float, default=0)
    
    # Поставщик
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    supplier_code = Column(String(100), nullable=True)
    supplier_name = Column(String(200), nullable=True)
    
    # Характеристики
    shelf_life_days = Column(Integer, nullable=True)
    storage_temperature = Column(String(50), nullable=True)
    storage_conditions = Column(Text, nullable=True)
    
    # HACCP
    is_critical = Column(Boolean, default=False)
    critical_points = Column(JSON, nullable=True)
    
    # Статус
    is_active = Column(Boolean, default=True)
    
    # Даты
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')), 
                        onupdate=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    last_purchase = Column(Date, nullable=True)
    last_use = Column(Date, nullable=True)
    
    # Связи
    arrivals = relationship("Arrival", back_populates="product")
    supplier = relationship("Supplier", back_populates="products")
    ttk_ingredients = relationship("TTKIngredient", back_populates="product")
    
    # Индексы
    table_args = (
        Index('idx_product_category', 'category'),
        Index('idx_product_stock', 'current_stock'),
        UniqueConstraint('barcode', name='uq_product_barcode'),
    )
    
    # Валидаторы
    @validates('min_stock', 'max_stock', 'current_stock')
    def validate_stock(self, key, value):
        """Валидация остатков"""
        if value < 0:
            raise ValueError("Остаток не может быть отрицательным")
        return value
    
    @property
    def needs_restock(self) -> bool:
        """Нужно ли пополнение запасов"""
        return self.current_stock <= self.safety_stock
    
    @property
    def stock_status(self) -> str:
        """Статус остатков"""
        if self.current_stock <= self.safety_stock:
            return "критический"
        elif self.current_stock <= self.min_stock:
            return "низкий"
        elif self.current_stock >= self.max_stock:
            return "избыточный"
        else:
            return "нормальный"
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', stock={self.current_stock}{self.unit})>"

class Supplier(Base):
    """
    Модель поставщика
    """
    tablename = "suppliers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    inn = Column(String(12), nullable=True)
    kpp = Column(String(9), nullable=True)
    rating = Column(Float, default=5.0)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    
    # Связи
    products = relationship("Product", back_populates="supplier")
    arrivals = relationship("Arrival", back_populates="supplier_rel")
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}')>"

class Arrival(Base):
    """
    Модель прихода товара
    """
    tablename = "arrivals"
    
    id = Column(Integer, primary_key=True)
    
    # Продукт
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)  # Дублирование для истории

product_unit = Column(String(20), nullable=False)
    
    # Количественные данные
    quantity = Column(Float, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Информация о поставке
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier_name = Column(String(200), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    batch_number = Column(String(100), nullable=True)
    production_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    shelf_life_days = Column(Integer, nullable=True)
    
    # Получатель
    received_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    receiver_name = Column(String(100), nullable=True)
    
    # Статус
    status = Column(String(50), default="принят")  # ожидает, принят, отклонен, списан
    quality_check = Column(String(20), default="ожидает")  # ожидает, пройдена, не пройдена
    
    # Даты
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    checked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Связи
    product = relationship("Product", back_populates="arrivals")
    receiver = relationship("User", back_populates="arrivals")
    supplier_rel = relationship("Supplier", back_populates="arrivals")
    akp_checks = relationship("AKP", back_populates="arrival")
    
    # Валидаторы
    @validates('quantity', 'price_per_unit')
    def validate_positive(self, key, value):
        """Проверка положительных значений"""
        if value <= 0:
            raise ValueError(f"{key} должен быть больше 0")
        return value
    
    def __repr__(self):
        return f"<Arrival(id={self.id}, product='{self.product_name}', quantity={self.quantity}{self.product_unit})>"

class TTK(Base):
    """
    Модель Технико-Технологической Карты
    """
    tablename = "ttk"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    category = Column(String(100), index=True)
    
    # Выход продукта
    output_name = Column(String(200), nullable=False)
    output_weight = Column(Float, nullable=False)
    output_units = Column(String(20), default="г")
    output_count = Column(Integer, default=1)  # Количество порций
    
    # Стоимость
    cost_price = Column(Float, default=0)
    selling_price = Column(Float, default=0)
    margin = Column(Float, default=0)
    
    # Время приготовления
    prep_time_minutes = Column(Integer, default=30)
    cook_time_minutes = Column(Integer, default=60)
    total_time_minutes = Column(Integer, default=90)
    
    # Хранение
    shelf_life_hours = Column(Integer, default=24)
    storage_temp = Column(String(50), default="+2...+4°C")
    
    # Технология
    technology = Column(Text, nullable=False)
    critical_points = Column(Text, nullable=True)
    equipment = Column(JSON, nullable=True)  # Список оборудования
    
    # Ингредиенты (через отдельную таблицу)
    
    # Статус
    status = Column(String(20), default="черновик")  # черновик, активен, архив
    version = Column(Integer, default=1)
    
    # Создатель
    created_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    creator_name = Column(String(100), nullable=True)
    
    # Даты
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')), 
                        onupdate=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Связи
    creator = relationship("User", back_populates="ttk_created")
    ingredients = relationship("TTKIngredient", back_populates="ttk")
    
    # Индексы
    table_args = (
        Index('idx_ttk_category', 'category'),

Index('idx_ttk_status', 'status'),
    )
    
    @property
    def ingredient_cost(self) -> float:
        """Общая стоимость ингредиентов"""
        return sum(ing.total_cost for ing in self.ingredients)
    
    @property
    def food_cost_percentage(self) -> float:
        """Процент стоимости продуктов"""
        if self.selling_price > 0:
            return (self.cost_price / self.selling_price) * 100
        return 0
    
    def __repr__(self):
        return f"<TTK(id={self.id}, code='{self.code}', name='{self.name}')>"

class TTKIngredient(Base):
    """
    Связующая таблица для ингредиентов ТТК
    """
    tablename = "ttk_ingredients"
    
    id = Column(Integer, primary_key=True)
    ttk_id = Column(Integer, ForeignKey("ttk.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Количественные данные
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    
    # Обработка
    processing_type = Column(String(50), nullable=True)  # очистка, нарезка и т.д.
    waste_percentage = Column(Float, default=0)  # Процент отходов
    
    # Стоимость
    price_per_unit = Column(Float, default=0)
    total_cost = Column(Float, default=0)
    
    # Порядок
    order = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    
    # Связи
    ttk = relationship("TTK", back_populates="ingredients")
    product = relationship("Product", back_populates="ttk_ingredients")
    
    # Индексы
    table_args = (
        UniqueConstraint('ttk_id', 'product_id', name='uq_ttk_product'),
    )
    
    def __repr__(self):
        return f"<TTKIngredient(ttk_id={self.ttk_id}, product_id={self.product_id}, quantity={self.quantity}{self.unit})>"

class Task(Base):
    """
    Модель задачи/чек-листа
    """
    tablename = "tasks"
    
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)
    
    # Описание
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False)  # открытие, закрытие, уборка, акп, инвентаризация
    priority = Column(String(20), default="средний")  # низкий, средний, высокий, критический
    
    # Ответственные
    assigned_to = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    assignee_name = Column(String(100), nullable=True)
    created_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    creator_name = Column(String(100), nullable=True)
    
    # Сроки
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    due_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    reminder_sent = Column(Boolean, default=False)
    
    # Статус
    status = Column(String(50), default="pending")  # pending, in_progress, completed, cancelled, overdue
    completion_percentage = Column(Integer, default=0)
    
    # Чек-лист
    checklist_items = Column(JSON, nullable=True)  # Список пунктов чек-листа
    completed_items = Column(JSON, nullable=True)  # Завершенные пункты
    
    # Результат
    result_notes = Column(Text, nullable=True)
    quality_check = Column(String(20), nullable=True)  # отлично, хорошо, удовлетворительно, плохо
    photos = Column(JSON, nullable=True)  # Ссылки на фото
    
    # Связи
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="tasks_assigned")
    creator = relationship("User", foreign_keys=[created_by], back_populates="tasks_created")
    
    # Индексы
    table_args = (
        Index('idx_task_status', 'status'),
        Index('idx_task_due', 'due_at'),
        Index('idx_task_assignee', 'assigned_to'),
    )
    
    @property
    def is_overdue(self) -> bool:
        """Просрочена ли задача"""
        if self.due_at and self.status != 'completed':
            return datetime.now(pytz.timezone('Europe/Moscow')) > self.due_at
        return False

@property
    def time_remaining(self) -> str:
        """Оставшееся время"""
        if not self.due_at or self.status == 'completed':
            return "Не ограничено"
        
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        delta = self.due_at - now
        
        if delta.total_seconds() < 0:
            return "Просрочено"
        
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}д {hours}ч"
        elif hours > 0:
            return f"{hours}ч {minutes}м"
        else:
            return f"{minutes}м"
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"

class AKP(Base):
    """
    Модель Анализ Критических Пределов
    """
    tablename = "akp"
    
    id = Column(Integer, primary_key=True)
    
    # Связь с приходом
    arrival_id = Column(Integer, ForeignKey("arrivals.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Проверяемые параметры
    temperature = Column(Float, nullable=True)  # Температура при приемке
    ph_level = Column(Float, nullable=True)     # Уровень pH
    appearance = Column(String(100), nullable=True)  # Внешний вид
    smell = Column(String(100), nullable=True)  # Запах
    texture = Column(String(100), nullable=True)  # Консистенция
    
    # Весовой контроль
    declared_weight = Column(Float, nullable=False)
    actual_weight = Column(Float, nullable=False)
    deviation_percent = Column(Float, nullable=False)
    
    # Упаковка
    packaging_integrity = Column(Boolean, default=True)
    labeling_correct = Column(Boolean, default=True)
    expiry_date_correct = Column(Boolean, default=True)
    
    # Документы
    documents_present = Column(Boolean, default=True)
    certificates_present = Column(Boolean, default=True)
    
    # Проверяющий
    conducted_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    conductor_name = Column(String(100), nullable=True)
    
    # Результат
    passed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    corrective_actions = Column(Text, nullable=True)
    
    # Даты
    conducted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    
    # Связи
    arrival = relationship("Arrival", back_populates="akp_checks")
    product = relationship("Product")
    conductor = relationship("User", back_populates="akp_checks")
    
    # Валидаторы
    @validates('deviation_percent')
    def validate_deviation(self, key, value):
        """Валидация отклонения"""
        if abs(value) > 100:
            raise ValueError("Отклонение не может превышать 100%")
        return value
    
    @property
    def quality_score(self) -> int:
        """Оценка качества (0-100)"""
        score = 0
        if self.passed:
            score += 40
        if self.deviation_percent <= 5:
            score += 30
        if self.packaging_integrity and self.labeling_correct:
            score += 15
        if self.temperature and 2 <= self.temperature <= 4:
            score += 15
        return score
    
    def __repr__(self):
        return f"<AKP(id={self.id}, arrival_id={self.arrival_id}, passed={self.passed})>"

class Report(Base):
    """
    Модель отчёта
    """
    tablename = "reports"
    
    id = Column(Integer, primary_key=True)
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, inventory, waste
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Данные отчёта
    data = Column(JSON, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Статистика
    total_arrivals = Column(Integer, default=0)
    total_departures = Column(Integer, default=0)
    total_waste = Column(Float, default=0)
    total_sales = Column(Float, default=0)
    total_cost = Column(Float, default=0)
    
    # Создатель

created_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    
    # Статус
    is_final = Column(Boolean, default=False)
    
    # Даты
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    
    def __repr__(self):
        return f"<Report(id={self.id}, type='{self.report_type}', period={self.period_start}-{self.period_end})>"

class Waste(Base):
    """
    Модель списания/утилизации
    """
    tablename = "waste"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    
    # Количество
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    
    # Причина списания
    reason = Column(String(100), nullable=False)  # порча, истечение срока, брак
    category = Column(String(50), nullable=False)  # food, packaging, other
    
    # Стоимость
    cost_price = Column(Float, default=0)
    total_cost = Column(Float, default=0)
    
    # Ответственный
    recorded_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    recorder_name = Column(String(100), nullable=True)
    
    # Подтверждение
    confirmed_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Фотодоказательства
    photos = Column(JSON, nullable=True)
    
    # Даты
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    waste_date = Column(Date, default=lambda: datetime.now(pytz.timezone('Europe/Moscow')).date())
    
    # Связи
    product = relationship("Product")
    
    def __repr__(self):
        return f"<Waste(id={self.id}, product='{self.product_name}', quantity={self.quantity}{self.unit})>"
