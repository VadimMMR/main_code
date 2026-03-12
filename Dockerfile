# ==============================
# Main Code with System Information Library
# ==============================

# Используем нашу библиотеку с Docker Hub как базовый образ
FROM dayg0555/system-info-library:latest AS system-info-lib

# Базовый образ для приложения
FROM python:3.11-slim

LABEL maintainer="dayg0555@gmail.com"
LABEL description="Main application using System Information Library"
LABEL version="1.0.0"

# ------------------------------
# Установка системных зависимостей
# ------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    pciutils \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------
# Рабочая директория
# ------------------------------
WORKDIR /app

# ------------------------------
# Копирование нашей библиотеки из предыдущего образа
# ------------------------------
COPY --from=system-info-lib /app /app/system_info_library/

# ------------------------------
# Устанавливаем Python путь
# ------------------------------
ENV PYTHONPATH="/app:${PYTHONPATH}"

# ------------------------------
# Копируем зависимости и код приложения
# ------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# ------------------------------
# Проверка импорта
# ------------------------------
RUN echo "=== Проверка импорта библиотеки ===" && \
    python -c "from system_info_library.main import get_system_info; print('✅ Библиотека успешно импортируется')"

# ------------------------------
# Создание непривилегированного пользователя
# ------------------------------
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# ------------------------------
# Запуск приложения
# ------------------------------
CMD ["python", "main.py"]