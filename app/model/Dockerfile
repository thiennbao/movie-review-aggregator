FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN python -m venv .venv
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt
RUN find /app/.venv \( -type d -a -name test -o -name tests \) -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf '{}' \+

ENV PATH="/app/.venv/bin:$PATH"

RUN python app.py
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]