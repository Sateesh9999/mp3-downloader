# Start from Ubuntu
FROM ubuntu:22.04

# Prevent interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Update and install prerequisites
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    software-properties-common \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# Install Python 3.12
# -------------------------
RUN add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set python3.12 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

RUN apt-get update && apt-get install -y python3-distutils python3-setuptools
# -------------------------
# Install Node.js 24
# -------------------------
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r BE-Music-Downloader/requirements.txt

RUN npm install --prefix FE-Music-Downloader

RUN mkdir -p /app/music

CMD ["sh", "-c", "python /app/BE-Music-Downloader/app.py & npm run --prefix /app/FE-Music-Downloader dev"]