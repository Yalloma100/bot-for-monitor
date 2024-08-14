# Використовуємо базовий образ з Python
FROM python:3.9-slim

# Встановлюємо змінну оточення для того, щоб Python не буферизував вивід (важливо для логування)
ENV PYTHONUNBUFFERED=1

# Створюємо робочу директорію в контейнері
WORKDIR /app

# Копіюємо requirements.txt і встановлюємо залежності
COPY requirements.txt .

RUN pip install -r requirements.txt

# Копіюємо всі файли проєкту до робочої директорії
COPY . .

# Команда для запуску вашого бота
CMD ["python", "bot.py"]
