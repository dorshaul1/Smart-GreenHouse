FROM python:3.11-slim

# Keep Python output unbuffered and avoid .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first for better layer caching
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

# App source
COPY . .

# Default: run the GUI when starting the container manually
CMD ["python", "gui/app.py"]
