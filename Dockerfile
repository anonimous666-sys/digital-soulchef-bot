# Dockerfile для Цифровой Су-Шеф

# Базовый образ Python
FROM python:3.11-slim as builder

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --user -r requirements.txt

# Второй этап - финальный образ
FROM python:3.11-slim

# Установка системных зависимостей для работы
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя приложения
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Копирование зависимостей из builder
COPY --from=builder /root/.local /root/.local

# Установка переменных окружения
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая директория
WORKDIR /app

# Копирование исходного кода
COPY --chown=appuser:appuser . .

# Переключаемся на пользователя приложения
USER appuser

# Создание директорий
RUN mkdir -p /app/logs /app/static /app/static/qr_codes

# Команда запуска
CMD ["python", "-m", "src.bot.main"]
