# Используем базовый образ с Python
FROM python:3.10-slim

# Устанавливаем директорию проекта
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта
COPY . .