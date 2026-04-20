FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libglib2.0-0 \
    libgomp1 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu --trusted-host download.pytorch.org \
    torch==2.5.1 torchvision==0.20.1
RUN pip install --no-cache-dir --index-url https://pypi.org/simple celery==5.5.3 redis==5.2.1
RUN pip install --no-cache-dir --index-url https://pypi.org/simple -r requirements.txt

COPY app ./app
COPY .env.example ./.env.example

RUN mkdir -p /app/data/storage /app/data/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
