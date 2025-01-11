FROM python:3.9-slim

# Установка необходимых пакетов и временной зоны
RUN apt-get update && \
    apt-get install -y nano tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

# Установка временной зоны через ENV
ENV TZ=${TIMEZONE}

# Создание директории приложения
WORKDIR /app

# Копирование файлов приложения
COPY ./app /app

# Копирование файла требований
COPY requirements.txt /app

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Запуск приложения
CMD ["python", "main.py"]
