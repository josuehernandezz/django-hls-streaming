FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV DJANGO_DEBUG=0

WORKDIR /app

# Install system packages (cached unless you change this block)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (cached unless requirements.txt changes)
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app last to avoid cache busting during dev
COPY ./django /app/
