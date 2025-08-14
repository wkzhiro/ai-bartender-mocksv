FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Gunicornを使用してFastAPIアプリを起動
CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:app"]