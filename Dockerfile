FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl

RUN curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.7/install.sh | bash - \
    && apt-get install -y nodejs

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r BE-Music-Downloader/requirements.txt

RUN npm install --prefix FE-Music-Downloader

RUN mkdir -p /app/music

CMD ["python", "BE-Music-Downloader/app.py"]

CMD ["npm", "start", "--prefix", "FE-Music-Downloader"]