Денис Слепцов:
# Makefile для управления проектом Цифровой Су-Шеф

.PHONY: help install dev test lint format clean build run deploy migrate backup restore docker-up docker-down docker-build docker-push docs

# Цвета для вывода
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

# Помощь
help:
 @echo "$(BLUE)Доступные команды:$(NC)"
 @echo "$(GREEN)  install     $(NC)- Установка зависимостей"
 @echo "$(GREEN)  dev         $(NC)- Установка зависимостей для разработки"
 @echo "$(GREEN)  run         $(NC)- Запуск бота в режиме разработки"
 @echo "$(GREEN)  test        $(NC)- Запуск тестов"
 @echo "$(GREEN)  lint        $(NC)- Проверка кода линтерами"
 @echo "$(GREEN)  format      $(NC)- Форматирование кода"
 @echo "$(GREEN)  clean       $(NC)- Очистка временных файлов"
 @echo "$(GREEN)  build       $(NC)- Сборка Docker образа"
 @echo "$(GREEN)  docker-up   $(NC)- Запуск контейнеров Docker"
 @echo "$(GREEN)  docker-down $(NC)- Остановка контейнеров Docker"
 @echo "$(GREEN)  deploy      $(NC)- Деплой на сервер"
 @echo "$(GREEN)  migrate     $(NC)- Применение миграций БД"
 @echo "$(GREEN)  backup      $(NC)- Создание резервной копии БД"
 @echo "$(GREEN)  restore     $(NC)- Восстановление БД из резервной копии"
 @echo "$(GREEN)  docs        $(NC)- Генерация документации"

# Установка зависимостей
install:
 @echo "$(YELLOW)Установка зависимостей...$(NC)"
 pip install --upgrade pip
 pip install -r requirements.txt

# Установка зависимостей для разработки
dev: install
 @echo "$(YELLOW)Установка зависимостей для разработки...$(NC)"
 pip install -r requirements-dev.txt

# Запуск бота
run:
 @echo "$(YELLOW)Запуск бота...$(NC)"
 python -m src.bot.main

# Тестирование
test:
 @echo "$(YELLOW)Запуск тестов...$(NC)"
 pytest tests/ -v --cov=src --cov-report=html

# Проверка кода
lint:
 @echo "$(YELLOW)Проверка кода flake8...$(NC)"
 flake8 src/ tests/
 @echo "$(YELLOW)Проверка типов mypy...$(NC)"
 mypy src/
 @echo "$(YELLOW)Проверка безопасности bandit...$(NC)"
 bandit -r src/ -ll

# Форматирование кода
format:
 @echo "$(YELLOW)Форматирование кода black...$(NC)"
 black src/ tests/
 @echo "$(YELLOW)Сортировка импортов isort...$(NC)"
 isort src/ tests/

# Очистка временных файлов
clean:
 @echo "$(YELLOW)Очистка временных файлов...$(NC)"
 find . -type d -name "__pycache__" -exec rm -rf {} +
 find . -type f -name "*.pyc" -delete
 find . -type f -name "*.pyo" -delete
 find . -type f -name "*.pyd" -delete
 find . -type f -name ".coverage" -delete
 find . -type d -name "*.egg-info" -exec rm -rf {} +
 find . -type d -name "*.egg" -exec rm -rf {} +
 find . -type d -name ".pytest_cache" -exec rm -rf {} +
 find . -type d -name ".mypy_cache" -exec rm -rf {} +
 find . -type d -name ".ruff_cache" -exec rm -rf {} +
 rm -rf build/ dist/ .eggs/ .tox/ .venv/ venv/
 rm -rf htmlcov/ coverage.xml .coverage
 rm -rf .benchmarks .hypothesis
 @echo "$(GREEN)Очистка завершена!$(NC)"

# Сборка Docker образа
build:
 @echo "$(YELLOW)Сборка Docker образа...$(NC)"
 docker build -t digital-souschef:latest .

# Запуск контейнеров Docker
docker-up:
 @echo "$(YELLOW)Запуск контейнеров Docker...$(NC)"
 docker-compose up -d

# Остановка контейнеров Docker
docker-down:
 @echo "$(YELLOW)Остановка контейнеров Docker...$(NC)"
 docker-compose down

# Перезапуск контейнеров Docker
docker-restart: docker-down docker-up

# Просмотр логов Docker
docker-logs:
 docker-compose logs -f bot

# Деплой на сервер (пример для Яндекс.Облака)
deploy:
 @echo "$(YELLOW)Деплой на Яндекс.Облако...$(NC)"
 @echo "$(RED)Реализуйте логику деплоя для вашего сервера$(NC)"
 # Пример для VM:
 # scp -r . user@server:/opt/digital-souschef
 # ssh user@server "cd /opt/digital-souschef && docker-compose up -d --build"

# Миграции БД
migrate:
 @echo "$(YELLOW)Применение миграций БД...$(NC)"
 alembic upgrade head

# Создание резервной копии БД
backup:
 @echo "$(YELLOW)Создание резервной копии БД...$(NC)"
 mkdir -p backups
 docker-compose exec -T postgres pg_dump -U souschef_user digital_souschef > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

@echo "$(GREEN)Резервная копия создана в backups/$(NC)"

# Восстановление БД из резервной копии
restore:
 @echo "$(YELLOW)Восстановление БД из резервной копии...$(NC)"
 @if [ -z "$(file)" ]; then \
  echo "$(RED)Укажите файл для восстановления: make restore file=backups/backup_20240101_120000.sql$(NC)"; \
  exit 1; \
 fi
 docker-compose exec -T postgres psql -U souschef_user -d digital_souschef < $(file)
 @echo "$(GREEN)База данных восстановлена из $(file)$(NC)"

# Генерация документации
docs:
 @echo "$(YELLOW)Генерация документации...$(NC)"
 cd docs && make html
 @echo "$(GREEN)Документация сгенерирована в docs/_build/html/$(NC)"

# Проверка здоровья системы
health:
 @echo "$(YELLOW)Проверка здоровья системы...$(NC)"
 @echo "$(BLUE)1. Docker контейнеры:$(NC)"
 @docker-compose ps
 @echo "$(BLUE)\n2. Логи бота (последние 5 строк):$(NC)"
 @docker-compose logs --tail=5 bot
 @echo "$(BLUE)\n3. Использование диска:$(NC)"
 @docker system df
 @echo "$(BLUE)\n4. Проверка БД:$(NC)"
 @docker-compose exec -T postgres pg_isready -U souschef_user

# Создание новой миграции
migration:
 @echo "$(YELLOW)Создание новой миграции...$(NC)"
 @if [ -z "$(message)" ]; then \
  echo "$(RED)Укажите описание миграции: make migration message='Add new column'$(NC)"; \
  exit 1; \
 fi
 alembic revision --autogenerate -m "$(message)"

# Обновление зависимостей
update-deps:
 @echo "$(YELLOW)Обновление зависимостей...$(NC)"
 pip install --upgrade pip
 pip install -r requirements.txt --upgrade
 pip freeze > requirements.txt

# Создание .env файла из примера
setup-env:
 @echo "$(YELLOW)Создание .env файла...$(NC)"
 @if [ -f ".env" ]; then \
  echo "$(YELLOW).env файл уже существует. Создать копию? [y/N] $(NC)"; \
  read -r response; \
  if [ "$$response" = "y" ] || [ "$$response" = "Y" ]; then \
   cp .env .env.backup; \
   echo "$(GREEN)Создана резервная копия .env.backup$(NC)"; \
  fi; \
 fi
 cp .env.example .env
 @echo "$(GREEN)Файл .env создан. Отредактируйте его перед запуском.$(NC)"

# Тестовые данные
seed:
 @echo "$(YELLOW)Загрузка тестовых данных...$(NC)"
 python scripts/seed_data.py
 @echo "$(GREEN)Тестовые данные загружены$(NC)"

# Запуск всех проверок перед коммитом
pre-commit: lint test
 @echo "$(GREEN)Все проверки пройдены!$(NC)"

# Установка pre-commit хуков
install-hooks:
 @echo "$(YELLOW)Установка pre-commit хуков...$(NC)"
 pre-commit install
 @echo "$(GREEN)Pre-commit хуки установлены$(NC)"

# Makefile для управления проектом Цифровой Су-Шеф

.PHONY: help install dev test lint format clean build run deploy migrate backup restore docker-up docker-down docker-build docker-push docs

# Цвета для вывода
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

# Помощь
help:
 @echo "$(BLUE)Доступные команды:$(NC)"
 @echo "$(GREEN)  install     $(NC)- Установка зависимостей"
 @echo "$(GREEN)  dev         $(NC)- Установка зависимостей для разработки"
 @echo "$(GREEN)  run         $(NC)- Запуск бота в режиме разработки"
 @echo "$(GREEN)  test        $(NC)- Запуск тестов"
 @echo "$(GREEN)  lint        $(NC)- Проверка кода линтерами"
 @echo "$(GREEN)  format      $(NC)- Форматирование кода"
 @echo "$(GREEN)  clean       $(NC)- Очистка временных файлов"
 @echo "$(GREEN)  build       $(NC)- Сборка Docker образа"
 @echo "$(GREEN)  docker-up   $(NC)- Запуск контейнеров Docker"
 @echo "$(GREEN)  docker-down $(NC)- Остановка контейнеров Docker"
 @echo "$(GREEN)  deploy      $(NC)- Деплой на сервер"
 @echo "$(GREEN)  migrate     $(NC)- Применение миграций БД"
 @echo "$(GREEN)  backup      $(NC)- Создание резервной копии БД"
 @echo "$(GREEN)  restore     $(NC)- Восстановление БД из резервной копии"
 @echo "$(GREEN)  docs        $(NC)- Генерация документации"

# Установка зависимостей
install:
 @echo "$(YELLOW)Установка зависимостей...$(NC)"
 pip install --upgrade pip
 pip install -r requirements.txt

# Установка зависимостей для разработки
dev: install
 @echo "$(YELLOW)Установка зависимостей для разработки...$(NC)"
 pip install -r requirements-dev.txt

# Запуск бота
run:
 @echo "$(YELLOW)Запуск бота...$(NC)"
 python -m src.bot.main

# Тестирование
test:
 @echo "$(YELLOW)Запуск тестов...$(NC)"
 pytest tests/ -v --cov=src --cov-report=html

# Проверка кода
lint:
 @echo "$(YELLOW)Проверка кода flake8...$(NC)"
 flake8 src/ tests/
 @echo "$(YELLOW)Проверка типов mypy...$(NC)"
 mypy src/
 @echo "$(YELLOW)Проверка безопасности bandit...$(NC)"
 bandit -r src/ -ll

# Форматирование кода
format:
 @echo "$(YELLOW)Форматирование кода black...$(NC)"
 black src/ tests/
 @echo "$(YELLOW)Сортировка импортов isort...$(NC)"
 isort src/ tests/

# Очистка временных файлов
clean:
 @echo "$(YELLOW)Очистка временных файлов...$(NC)"
 find . -type d -name "__pycache__" -exec rm -rf {} +
 find . -type f -name "*.pyc" -delete
 find . -type f -name "*.pyo" -delete
 find . -type f -name "*.pyd" -delete
 find . -type f -name ".coverage" -delete
 find . -type d -name "*.egg-info" -exec rm -rf {} +
 find . -type d -name "*.egg" -exec rm -rf {} +
 find . -type d -name ".pytest_cache" -exec rm -rf {} +
 find . -type d -name ".mypy_cache" -exec rm -rf {} +
 find . -type d -name ".ruff_cache" -exec rm -rf {} +
 rm -rf build/ dist/ .eggs/ .tox/ .venv/ venv/
 rm -rf htmlcov/ coverage.xml .coverage
 rm -rf .benchmarks .hypothesis
 @echo "$(GREEN)Очистка завершена!$(NC)"

# Сборка Docker образа
build:
 @echo "$(YELLOW)Сборка Docker образа...$(NC)"
 docker build -t digital-souschef:latest .

# Запуск контейнеров Docker
docker-up:
 @echo "$(YELLOW)Запуск контейнеров Docker...$(NC)"
 docker-compose up -d

# Остановка контейнеров Docker
docker-down:
 @echo "$(YELLOW)Остановка контейнеров Docker...$(NC)"
 docker-compose down

# Перезапуск контейнеров Docker
docker-restart: docker-down docker-up

# Просмотр логов Docker
docker-logs:
 docker-compose logs -f bot

# Деплой на сервер (пример для Яндекс.Облака)
deploy:
 @echo "$(YELLOW)Деплой на Яндекс.Облако...$(NC)"
 @echo "$(RED)Реализуйте логику деплоя для вашего сервера$(NC)"
 # Пример для VM:
 # scp -r . user@server:/opt/digital-souschef
 # ssh user@server "cd /opt/digital-souschef && docker-compose up -d --build"

# Миграции БД
migrate:
 @echo "$(YELLOW)Применение миграций БД...$(NC)"
 alembic upgrade head

# Создание резервной копии БД
backup:
 @echo "$(YELLOW)Создание резервной копии БД...$(NC)"
 mkdir -p backups
 docker-compose exec -T postgres pg_dump -U souschef_user digital_souschef > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

@echo "$(GREEN)Резервная копия создана в backups/$(NC)"

# Восстановление БД из резервной копии
restore:
 @echo "$(YELLOW)Восстановление БД из резервной копии...$(NC)"
 @if [ -z "$(file)" ]; then \
  echo "$(RED)Укажите файл для восстановления: make restore file=backups/backup_20240101_120000.sql$(NC)"; \
  exit 1; \
 fi
 docker-compose exec -T postgres psql -U souschef_user -d digital_souschef < $(file)
 @echo "$(GREEN)База данных восстановлена из $(file)$(NC)"

# Генерация документации
docs:
 @echo "$(YELLOW)Генерация документации...$(NC)"
 cd docs && make html
 @echo "$(GREEN)Документация сгенерирована в docs/_build/html/$(NC)"

# Проверка здоровья системы
health:
 @echo "$(YELLOW)Проверка здоровья системы...$(NC)"
 @echo "$(BLUE)1. Docker контейнеры:$(NC)"
 @docker-compose ps
 @echo "$(BLUE)\n2. Логи бота (последние 5 строк):$(NC)"
 @docker-compose logs --tail=5 bot
 @echo "$(BLUE)\n3. Использование диска:$(NC)"
 @docker system df
 @echo "$(BLUE)\n4. Проверка БД:$(NC)"
 @docker-compose exec -T postgres pg_isready -U souschef_user

# Создание новой миграции
migration:
 @echo "$(YELLOW)Создание новой миграции...$(NC)"
 @if [ -z "$(message)" ]; then \
  echo "$(RED)Укажите описание миграции: make migration message='Add new column'$(NC)"; \
  exit 1; \
 fi
 alembic revision --autogenerate -m "$(message)"

# Обновление зависимостей
update-deps:
 @echo "$(YELLOW)Обновление зависимостей...$(NC)"
 pip install --upgrade pip
 pip install -r requirements.txt --upgrade
 pip freeze > requirements.txt

# Создание .env файла из примера
setup-env:
 @echo "$(YELLOW)Создание .env файла...$(NC)"
 @if [ -f ".env" ]; then \
  echo "$(YELLOW).env файл уже существует. Создать копию? [y/N] $(NC)"; \
  read -r response; \
  if [ "$$response" = "y" ] || [ "$$response" = "Y" ]; then \
   cp .env .env.backup; \
   echo "$(GREEN)Создана резервная копия .env.backup$(NC)"; \
  fi; \
 fi
 cp .env.example .env
 @echo "$(GREEN)Файл .env создан. Отредактируйте его перед запуском.$(NC)"

# Тестовые данные
seed:
 @echo "$(YELLOW)Загрузка тестовых данных...$(NC)"
 python scripts/seed_data.py
 @echo "$(GREEN)Тестовые данные загружены$(NC)"

# Запуск всех проверок перед коммитом
pre-commit: lint test
 @echo "$(GREEN)Все проверки пройдены!$(NC)"

# Установка pre-commit хуков
install-hooks:
 @echo "$(YELLOW)Установка pre-commit хуков...$(NC)"
 pre-commit install
 @echo "$(GREEN)Pre-commit хуки установлены$(NC)"
