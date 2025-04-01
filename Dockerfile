FROM python:3.9-slim-buster

WORKDIR /app

# 合併所有系統層級的操作到一個 RUN 指令中
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libgpiod2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # 設定時區
    ln -snf /usr/share/zoneinfo/Asia/Taipei /etc/localtime && \
    echo "Asia/Taipei" > /etc/timezone

# 只複製必要檔案
COPY requirements.txt .

# 安裝 Python 套件並清理快取
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式檔案
COPY weather_time.py .

CMD ["python3", "weather_time.py"]