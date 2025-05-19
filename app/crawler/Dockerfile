# BUILD STAGE
FROM python:3.9-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends wget unzip curl gnupg2 build-essential python3-dev libffi-dev
RUN wget https://storage.googleapis.com/chrome-for-testing-public/136.0.7103.59/linux64/chrome-linux64.zip
RUN unzip chrome-linux64.zip && mv chrome-linux64 /opt/chrome

RUN wget https://storage.googleapis.com/chrome-for-testing-public/136.0.7103.59/linux64/chromedriver-linux64.zip
RUN unzip chromedriver-linux64.zip && mv chromedriver-linux64/chromedriver /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver

WORKDIR /app
COPY . .
RUN python -m venv .venv
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt
RUN find /app/.venv \( -type d -a -name test -o -name tests \) -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf '{}' \+


# RUN STAGE
FROM python:3.9-slim

RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libnss3 libx11-6 libxrandr2 libxcomposite1 libxdamage1 libxshmfence1 libgbm1 libgtk-3-0 libasound2
RUN rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/chrome /opt/chrome
COPY --from=builder /usr/bin/chromedriver /usr/bin/chromedriver
COPY --from=builder /app /app

ENV CHROME_BIN=/opt/chrome/chrome
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PATH="/app/.venv/bin:$PATH"
ENV PATH="/opt/chrome:$PATH"

WORKDIR /app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7000"]