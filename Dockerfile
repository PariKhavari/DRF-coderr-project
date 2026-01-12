FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projektcode + .env kopieren 
COPY . .

# Standard-Port 
EXPOSE 8000

# Django starten 
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
