# -------------------------
# Base Image: Official Python 3.12
# -------------------------
FROM python:3.12-slim

# Prevent interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# Install Node.js 24
# -------------------------
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# -------------------------
# Application Setup
# -------------------------
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r BE-Music-Downloader/requirements.txt

# Install Node.js dependencies
RUN npm install --prefix FE-Music-Downloader

# Create music directory
RUN mkdir -p /app/music

# -------------------------
# Start backend + frontend
# -------------------------
CMD ["sh", "-c", "python /app/BE-Music-Downloader/app.py & npm run --prefix /app/FE-Music-Downloader dev"]
