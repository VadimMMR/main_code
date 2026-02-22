FROM python:3.11-slim

LABEL maintainer="VadimMMR"
LABEL description="Test application for device_lib library"
LABEL version="1.0.0"

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    dmidecode \
    pciutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем и устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВСЮ библиотеку device_lib в рабочую директорию
COPY device_lib/ /app/device_lib/

# Копируем тестовый скрипт
COPY main.py .

# Переменные окружения для БД (если нужны)
ENV DB_HOST=ep-dawn-surf-abgw0kss-pooler.eu-west-2.aws.neon.tech
ENV DB_NAME=neondb
ENV DB_USER=neondb_owner
ENV DB_PORT=5432

CMD ["python", "main.py"]