FROM python:3.9-slim

WORKDIR /app

# 安裝系統相依套件
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libgpiod2 \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt
COPY requirements.txt .

# 安裝 Python 套件
RUN pip install -r requirements.txt

# 複製程式碼
COPY . .

# 執行程式
CMD ["python3", "weather_time.py"]