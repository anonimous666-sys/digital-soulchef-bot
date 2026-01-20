Денис Слепцов:
"""
CRUD операции для работы с базой данных
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.orm import joinedload, selectinload
import uuid

from src.database.models import (
    User, Product, Arrival, TTK, Task, AKP, 
    Report, Waste, Supplier, TTKIngredient
)

# ==================== ПОЛЬЗОВАТЕЛИ ====================

class UserCRUD:
    """CRUD операции для пользователей"""
    
    @staticmethod
    async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(session: AsyncSession, user_data: Dict[str, Any]) -> User:
        """Создать нового пользователя"""
        # Проверяем, есть ли уже пользователь
        existing = await UserCRUD.get_user_by_telegram_id(session, user_data.get('telegram_id'))
        if existing:
            return existing
        
        # Создаём нового пользователя
        user = User(
            user_id=user_data.get('user_id'),
            telegram_id=user_data.get('telegram_id', user_data.get('user_id')),
            username=user_data.get('username'),
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name'),
            phone=user_data.get('phone'),
            role=user_data.get('role', 'повар'),
            workplace=user_data.get('workplace', 'Главная кухня'),
            is_admin=user_data.get('is_admin', False),
            language=user_data.get('language', 'ru')
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return user
    
    @staticmethod
    async def update_user(session: AsyncSession, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """Обновить данные пользователя"""
        user = await UserCRUD.get_user(session, user_id)
        if not user:
            return None
        
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.now()
        await session.commit()
        await session.refresh(user)
        
        return user
    
    @staticmethod
    async def get_users_count(session: AsyncSession) -> int:
        """Получить количество пользователей"""
        result = await session.execute(
            select(func.count()).select_from(User)
        )
        return result.scalar()
    
    @staticmethod
    async def get_active_users(session: AsyncSession, days: int = 7) -> List[User]:
        """Получить активных пользователей за последние N дней"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        result = await session.execute(
            select(User)
            .where(User.last_active >= cutoff_date)
            .order_by(desc(User.last_active))
        )
        
        return result.scalars().all()
    
    @staticmethod
    async def get_admins(session: AsyncSession) -> List[User]:
        """Получить список администраторов"""
        result = await session.execute(
            select(User).where(User.is_admin == True)
        )
        return result.scalars().all()

# ==================== ПРОДУКТЫ ====================

class ProductCRUD:
    """CRUD операции для продуктов"""
    
    @staticmethod
    async def get_product(session: AsyncSession, product_id: int) -> Optional[Product]:

"""Получить продукт по ID"""
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_product_by_barcode(session: AsyncSession, barcode: str) -> Optional[Product]:
        """Получить продукт по штрих-коду"""
        result = await session.execute(
            select(Product).where(Product.barcode == barcode)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_product(session: AsyncSession, product_data: Dict[str, Any]) -> Product:
        """Создать новый продукт"""
        product = Product(
            name=product_data['name'],
            code=product_data.get('code'),
            barcode=product_data.get('barcode'),
            category=product_data.get('category'),
            unit=product_data.get('unit', 'кг'),
            min_stock=product_data.get('min_stock', 0),
            max_stock=product_data.get('max_stock', 100),
            current_stock=product_data.get('current_stock', 0),
            purchase_price=product_data.get('purchase_price', 0),
            shelf_life_days=product_data.get('shelf_life_days'),
            storage_temperature=product_data.get('storage_temperature')
        )
        
        session.add(product)
        await session.commit()
        await session.refresh(product)
        
        return product
    
    @staticmethod
    async def update_stock(session: AsyncSession, product_id: int, delta: float) -> Optional[Product]:
        """Обновить остаток продукта"""
        product = await ProductCRUD.get_product(session, product_id)
        if not product:
            return None
        
        product.current_stock += delta
        
        if product.current_stock < 0:
            product.current_stock = 0
        
        product.last_use = datetime.now().date()
        await session.commit()
        
        return product
    
    @staticmethod
    async def get_low_stock_products(session: AsyncSession) -> List[Product]:
        """Получить продукты с низким запасом"""
        result = await session.execute(
            select(Product)
            .where(
                and_(
                    Product.current_stock <= Product.safety_stock,
                    Product.is_active == True
                )
            )
            .order_by(Product.current_stock)
        )
        
        return result.scalars().all()
    
    @staticmethod
    async def get_expiring_products(session: AsyncSession, days: int = 3) -> List[Tuple[Product, date]]:
        """Получить продукты с истекающим сроком годности"""
        cutoff_date = datetime.now().date() + timedelta(days=days)
        
        # Здесь должна быть логика проверки срока годности
        # Для примера возвращаем все активные продукты
        result = await session.execute(
            select(Product)
            .where(Product.is_active == True)
            .limit(10)
        )
        
        products = result.scalars().all()
        return [(p, p.last_purchase or datetime.now().date()) for p in products]
    
    @staticmethod
    async def search_products(session: AsyncSession, query: str, limit: int = 20) -> List[Product]:
        """Поиск продуктов по названию"""
        result = await session.execute(
            select(Product)
            .where(
                or_(
                    Product.name.ilike(f"%{query}%"),
                    Product.code.ilike(f"%{query}%"),
                    Product.barcode.ilike(f"%{query}%")
                )
            )
            .limit(limit)
        )
        
        return result.scalars().all()
    
    @staticmethod
    async def get_products_count(session: AsyncSession) -> int:
        """Получить количество продуктов"""
        result = await session.execute(
            select(func.count()).select_from(Product)
        )
        return result.scalar()

# ==================== ПРИХОД ТОВАРА ====================

class ArrivalCRUD:
    """CRUD операции для прихода товара"""

@staticmethod
    async def create_arrival(session: AsyncSession, arrival_data: Dict[str, Any]) -> Arrival:
        """Создать запись о приходе товара"""
        
        # Получаем информацию о продукте
        product = await ProductCRUD.get_product(session, arrival_data['product_id'])
        if not product:
            raise ValueError(f"Продукт с ID {arrival_data['product_id']} не найден")
        
        # Рассчитываем общую стоимость
        total_price = arrival_data['quantity'] * arrival_data['price_per_unit']
        
        # Создаём запись о приходе
        arrival = Arrival(
            product_id=arrival_data['product_id'],
            product_name=product.name,
            product_unit=product.unit,
            quantity=arrival_data['quantity'],
            price_per_unit=arrival_data['price_per_unit'],
            total_price=total_price,
            supplier_id=arrival_data.get('supplier_id'),
            supplier_name=arrival_data.get('supplier_name'),
            invoice_number=arrival_data.get('invoice_number'),
            batch_number=arrival_data.get('batch_number'),
            expiry_date=arrival_data.get('expiry_date'),
            received_by=arrival_data['received_by'],
            receiver_name=arrival_data.get('receiver_name'),
            status=arrival_data.get('status', 'принят')
        )
        
        # Обновляем остатки продукта
        await ProductCRUD.update_stock(session, product.id, arrival_data['quantity'])
        
        # Обновляем среднюю цену
        if product.current_stock > 0:
            total_value = (product.current_stock * product.avg_price) + total_price
            product.avg_price = total_value / product.current_stock
        
        product.last_purchase = datetime.now().date()
        
        session.add(arrival)
        await session.commit()
        await session.refresh(arrival)
        
        return arrival
    
    @staticmethod
    async def get_today_arrivals(session: AsyncSession) -> List[Arrival]:
        """Получить приходы за сегодня"""
        today = datetime.now().date()
        
        result = await session.execute(
            select(Arrival)
            .where(func.date(Arrival.received_at) == today)
            .order_by(desc(Arrival.received_at))
            .options(joinedload(Arrival.product))
        )
        
        return result.scalars().all()
    
    @staticmethod
    async def get_arrivals_by_date(session: AsyncSession, start_date: date, end_date: date) -> List[Arrival]:
        """Получить приходы за период"""
        result = await session.execute(
            select(Arrival)
            .where(
                and_(
                    Arrival.received_at >= start_date,
                    Arrival.received_at <= end_date
                )
            )
            .order_by(desc(Arrival.received_at))
            .options(joinedload(Arrival.product))
        )
        
        return result.scalars().all()

# ==================== ТТК ====================

class TTKCRUD:
    """CRUD операции для ТТК"""
    
    @staticmethod
    async def get_ttk(session: AsyncSession, ttk_id: int) -> Optional[TTK]:
        """Получить ТТК по ID"""
        result = await session.execute(
            select(TTK)
            .where(TTK.id == ttk_id)
            .options(joinedload(TTK.ingredients).joinedload(TTKIngredient.product))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_ttk_by_code(session: AsyncSession, code: str) -> Optional[TTK]:
        """Получить ТТК по коду"""
        result = await session.execute(
            select(TTK)
            .where(TTK.code == code)
            .options(joinedload(TTK.ingredients).joinedload(TTKIngredient.product))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_ttk(session: AsyncSession, ttk_data: Dict[str, Any]) -> TTK:
        """Создать новую ТТК"""
        
        # Проверяем уникальность кода
        if ttk_data.get('code'):
            existing = await TTKCRUD.

get_ttk_by_code(session, ttk_data['code'])
            if existing:
                raise ValueError(f"ТТК с кодом '{ttk_data['code']}' уже существует")
        
        # Создаём ТТК
        ttk = TTK(
            code=ttk_data.get('code'),
            name=ttk_data['name'],
            category=ttk_data.get('category'),
            output_name=ttk_data.get('output_name', ttk_data['name']),
            output_weight=ttk_data.get('output_weight', 0),
            output_units=ttk_data.get('output_units', 'г'),
            technology=ttk_data.get('technology', ''),
            shelf_life_hours=ttk_data.get('shelf_life_hours', 24),
            created_by=ttk_data['created_by'],
            creator_name=ttk_data.get('creator_name')
        )
        
        session.add(ttk)
        await session.commit()
        await session.refresh(ttk)
        
        # Добавляем ингредиенты, если они есть
        if 'ingredients' in ttk_data:
            await TTKCRUD.add_ingredients(session, ttk.id, ttk_data['ingredients'])
        
        return ttk
    
    @staticmethod
    async def add_ingredients(session: AsyncSession, ttk_id: int, ingredients: List[Dict[str, Any]]):
        """Добавить ингредиенты в ТТК"""
        
        ttk = await TTKCRUD.get_ttk(session, ttk_id)
        if not ttk:
            raise ValueError(f"ТТК с ID {ttk_id} не найдена")
        
        for idx, ing_data in enumerate(ingredients):
            ingredient = TTKIngredient(
                ttk_id=ttk_id,
                product_id=ing_data['product_id'],
                quantity=ing_data['quantity'],
                unit=ing_data.get('unit', 'кг'),
                processing_type=ing_data.get('processing_type'),
                waste_percentage=ing_data.get('waste_percentage', 0),
                order=idx
            )
            
            # Рассчитываем стоимость
            product = await ProductCRUD.get_product(session, ing_data['product_id'])
            if product:
                ingredient.price_per_unit = product.avg_price or product.purchase_price
                ingredient.total_cost = ingredient.quantity * ingredient.price_per_unit
            
            session.add(ingredient)
        
        await session.commit()
        
        # Пересчитываем стоимость ТТК
        await TTKCRUD.calculate_cost(session, ttk_id)
    
    @staticmethod
    async def calculate_cost(session: AsyncSession, ttk_id: int):
        """Рассчитать стоимость ТТК"""
        ttk = await TTKCRUD.get_ttk(session, ttk_id)
        if not ttk:
            return
        
        # Суммируем стоимость ингредиентов
        result = await session.execute(
            select(func.sum(TTKIngredient.total_cost))
            .where(TTKIngredient.ttk_id == ttk_id)
        )
        
        total_cost = result.scalar() or 0
        ttk.cost_price = total_cost
        
        if ttk.selling_price > 0:
            ttk.margin = ((ttk.selling_price - total_cost) / ttk.selling_price) * 100
        
        await session.commit()
    
    @staticmethod
    async def search_ttk(session: AsyncSession, query: str, limit: int = 20) -> List[TTK]:
        """Поиск ТТК по названию или коду"""
        result = await session.execute(
            select(TTK)
            .where(
                or_(
                    TTK.name.ilike(f"%{query}%"),
                    TTK.code.ilike(f"%{query}%"),
                    TTK.category.ilike(f"%{query}%")
                )
            )
            .where(TTK.status == 'активен')
            .limit(limit)
        )
        
        return result.scalars().all()
    
    @staticmethod
    async def get_ttk_count(session: AsyncSession) -> int:
        """Получить количество ТТК"""
        result = await session.execute(
            select(func.count()).select_from(TTK)
        )
        return result.scalar()

# ==================== ЗАДАЧИ ====================

class TaskCRUD:
    """CRUD операции для задач"""
    
    @staticmethod
    async def create_task(session: AsyncSession, task_data: Dict[str, Any]) -> Task:

"""Создать новую задачу"""
        
        # Генерируем UUID
        task_uuid = str(uuid.uuid4())
        
        # Создаём задачу
        task = Task(
            uuid=task_uuid,
            title=task_data['title'],
            description=task_data.get('description'),
            task_type=task_data.get('task_type', 'общая'),
            priority=task_data.get('priority', 'средний'),
            assigned_to=task_data['assigned_to'],
            assignee_name=task_data.get('assignee_name'),
            created_by=task_data['created_by'],
            creator_name=task_data.get('creator_name'),
            due_at=task_data.get('due_at'),
            checklist_items=task_data.get('checklist_items'),
            status='pending'
        )
        
        session.add(task)
        await session.commit()
        await session.refresh(task)
        
        return task
    
    @staticmethod
    async def get_user_tasks(session: AsyncSession, user_id: int, 
                           status: Optional[str] = None) -> List[Task]:
        """Получить задачи пользователя"""
        query = select(Task).where(Task.assigned_to == user_id)
        
        if status:
            query = query.where(Task.status == status)
        
        query = query.order_by(desc(Task.created_at))
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_task_status(session: AsyncSession, task_id: int, 
                               status: str, notes: Optional[str] = None) -> Optional[Task]:
        """Обновить статус задачи"""
        task = await TaskCRUD.get_task(session, task_id)
        if not task:
            return None
        
        task.status = status
        task.updated_at = datetime.now()
        
        if status == 'completed':
            task.completed_at = datetime.now()
            task.completion_percentage = 100
        
        if notes:
            task.result_notes = notes
        
        await session.commit()
        await session.refresh(task)
        
        return task
    
    @staticmethod
    async def get_overdue_tasks(session: AsyncSession) -> List[Task]:
        """Получить просроченные задачи"""
        now = datetime.now()
        
        result = await session.execute(
            select(Task)
            .where(
                and_(
                    Task.due_at < now,
                    Task.status.in_(['pending', 'in_progress'])
                )
            )
            .order_by(Task.due_at)
        )
        
        return result.scalars().all()
    
    @staticmethod
    async def get_active_tasks_count(session: AsyncSession) -> int:
        """Получить количество активных задач"""
        result = await session.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.status.in_(['pending', 'in_progress']))
        )
        return result.scalar()

# ==================== ОТЧЁТЫ ====================

class ReportCRUD:
    """CRUD операции для отчётов"""
    
    @staticmethod
    async def create_daily_report(session: AsyncSession, date: date, 
                                created_by: Optional[int] = None) -> Report:
        """Создать ежедневный отчёт"""
        
        # Собираем статистику за день
        # Приходы
        arrivals_result = await session.execute(
            select(
                func.count(Arrival.id),
                func.sum(Arrival.total_price)
            )
            .where(func.date(Arrival.received_at) == date)
        )
        arrivals_count, arrivals_total = arrivals_result.first() or (0, 0)
        
        # Списания
        waste_result = await session.execute(
            select(
                func.sum(Waste.quantity),
                func.sum(Waste.total_cost)
            )
            .where(func.date(Waste.recorded_at) == date)
        )
        waste_quantity, waste_cost = waste_result.first() or (0, 0)
        
        # Создаём отчёт
        report = Report(
            report_type='daily',

period_start=date,
            period_end=date,
            data={
                'arrivals': {
                    'count': arrivals_count,
                    'total': float(arrivals_total or 0)
                },
                'waste': {
                    'quantity': float(waste_quantity or 0),
                    'cost': float(waste_cost or 0)
                }
            },
            total_arrivals=arrivals_count,
            total_waste=float(waste_quantity or 0),
            total_cost=float(waste_cost or 0),
            created_by=created_by
        )
        
        session.add(report)
        await session.commit()
        await session.refresh(report)
        
        return report

# Экспортируем экземпляры CRUD классов
user_crud = UserCRUD()
product_crud = ProductCRUD()
arrival_crud = ArrivalCRUD()
ttk_crud = TTKCRUD()
task_crud = TaskCRUD()
report_crud = ReportCRUD()
