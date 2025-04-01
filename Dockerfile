FROM python:3.9-slim

# 設定時區
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安裝系統依賴
RUN apt-get update && apt-get install -y i2c-tools

WORKDIR /app
COPY . .
RUN pip install smbus2 requests python-dotenv

CMD ["python", "weather_time.py"]