# Первый этап: берём образ с библиотеками
FROM dayg0555/device-os-libs@sha256:f79a40dd987ca5aa17eaed0251a40fac1b997312396b7f5c1e542fec27c66cc1 AS libs

FROM python:3.11-slim

WORKDIR /app

# Копируем библиотеки из первого образа
COPY --from=libs /usr/local/lib/python3.9/site-packages/device_lib/ /app/device_lib/

# Копируем requirements и main.py
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]