FROM python:3.9

# Install system dependencies, Chrome, ChromeDriver, and debugging tools
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libx11-6 \
    libx11-xcb1 \
    libxi6 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxtst6 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libgbm1 \
    libgtk-3-0 \
    libxshmfence1 \
    libu2f-udev \
    procps \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y \
    google-chrome-stable \
    && wget https://storage.googleapis.com/chrome-for-testing-public/136.0.7103.59/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm -rf chromedriver-linux64.zip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY crawler_api.py .
COPY imdb_crawler.py .
COPY metacritic_crawler.py .
COPY rotten_crawler.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable for ChromeDriver
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Expose port
EXPOSE 6000

# Run the FastAPI app with increased shared memory
CMD ["uvicorn", "crawler_api:app", "--host", "0.0.0.0", "--port", "6000"]
