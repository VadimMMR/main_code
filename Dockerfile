FROM dayg0555/hardware_collector_lib:latest AS hw_lib
FROM dayg0555/system-info-library:latest AS os_lib
FROM python:3.11-slim

LABEL maintainer="dayg0555@gmail.com"
LABEL description="System Information API for Grafana"
LABEL version="1.0.0"

RUN apt-get update && apt-get install -y --no-install-recommends \
    pciutils \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=hw_lib /app/hardware_collector_lib /app/hardware_collector_lib/
COPY --from=os_lib /app /app/system_info_library/

ENV PYTHONPATH="/app:${PYTHONPATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000
CMD ["python", "app.py"]