FROM python:3.11-slim

# Install Firefox and dependencies
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install geckodriver
RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz \
    && tar -xzf geckodriver-v0.33.0-linux64.tar.gz \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver-v0.33.0-linux64.tar.gz

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY orange_bot.py .

RUN mkdir -p /app/data

CMD ["python", "orange_bot.py"]