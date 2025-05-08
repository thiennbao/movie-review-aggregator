# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Sao chép toàn bộ thư mục server
COPY . .



# Cài đặt các thư viện
RUN pip install --no-cache-dir -r requirements.txt

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1

# Chạy ứng dụng với uvicorn
CMD ["uvicorn", "api.movie_api:app", "--host", "0.0.0.0", "--port", "5001"]