# BUILD STAGE
FROM python:3.9-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc libpq-dev libssl-dev curl

WORKDIR /app
COPY . .

RUN python -m venv .venv
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt
RUN find /app/.venv \( -type d -a -name test -o -name tests \) -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf '{}' \+

ENV PATH="/app/.venv/bin:$PATH"

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]