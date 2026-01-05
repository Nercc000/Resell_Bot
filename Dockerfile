# Base Image with Python 3.11
FROM python:3.11-slim-bookworm

# Environment Variables
ENV PYTHONUNBUFFERED=1
ENV HEADLESS=true
ENV DEBIAN_FRONTEND=noninteractive

# Work Directory
WORKDIR /app

# Install System Dependencies for Playwright & Camoufox
RUN apt-get update && apt-get install -y \
    wget \
    git \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Browsers
# Explicitly install chromium and firefox as Camoufox/Playwright might need them
RUN playwright install --with-deps chromium firefox

# Copy Project Files
# We copy everything, but .dockerignore should exclude unneeded files
COPY . .

# Expose API Port
EXPOSE 8000

# Entrypoint: Start FastAPI Server
# Using `dashboard/api/main.py` effectively, but uvicorn needs python module syntax
# Since we are in /app, and main.py spawns subprocesses relative to root, we must be careful with paths.
# dashboard/api/main.py uses "cwd=..." to spawn processes.
# Let's adjust pythonpath to include current dir.
ENV PYTHONPATH=/app

CMD ["uvicorn", "dashboard.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
