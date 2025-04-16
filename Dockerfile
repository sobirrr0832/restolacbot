FROM python:3.10-slim

WORKDIR /app

# Fayllarni docker konteynerga aniq ko'chiramiz
COPY main.py /app/
COPY requirements.txt /app/

# Kerakli kutubxonalarni o'rnatamiz
RUN pip install --no-cache-dir -r requirements.txt

# Bot tokenini environment variable sifatida beramiz
ENV BOT_TOKEN="your_bot_token_here"

# Izoh tugganligini bildiradi va app ishga tushadi
CMD ["python", "/app/main.py"]
