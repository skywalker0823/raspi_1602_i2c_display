import smbus2
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
import board
import adafruit_dht
import json
# from influxdb_client import InfluxDBClient, Point
# from influxdb_client.client.write_api import SYNCHRONOUS

# 載入 .env 檔案
load_dotenv()

# 🛠️ I2C LCD 設定
I2C_ADDR = 0x27  # 如果 i2cdetect 顯示 0x3F，請改為 0x3F
LCD_WIDTH = 16
LCD_CHR = 1
LCD_CMD = 0
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0
LCD_BACKLIGHT = 0x08
ENABLE = 0b00000100

# 在檔案開頭的全域變數區域加入
DHT_PIN = board.D17  # DHT11 連接到 GPIO 17
dht_device = adafruit_dht.DHT11(DHT_PIN)
DISPLAY_SWITCH_TIME = 5  # 每5秒切換一次顯示

# 在 load_dotenv() 後添加
# INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
# INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', 'your_token')
# INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'home')
# INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'weather_data')

# 註解掉 InfluxDB 客戶端初始化
# influxdb_client = InfluxDBClient(
#     url=INFLUXDB_URL,
#     token=INFLUXDB_TOKEN,
#     org=INFLUXDB_ORG
# )
# write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

# ☁️ 中央氣象局 API 
API_KEY = os.getenv('CWB_API_KEY')  # 從環境變數取得 API Key
LOCATION_NAME = os.getenv('LOCATION_NAME', '臺北市')  # 從環境變數取得地點，預設值為臺北市
CWB_URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={API_KEY}&locationName={LOCATION_NAME}"

bus = smbus2.SMBus(1)

def lcd_byte(bits, mode):
    """發送一個字符到 LCD"""
    high_bits = mode | (bits & 0xF0) | LCD_BACKLIGHT
    low_bits = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT
    
    bus.write_byte(I2C_ADDR, high_bits)
    lcd_toggle_enable(high_bits)
    bus.write_byte(I2C_ADDR, low_bits)
    lcd_toggle_enable(low_bits)

def lcd_toggle_enable(bits):
    """觸發 LCD 使能信號"""
    time.sleep(0.0005)
    bus.write_byte(I2C_ADDR, (bits | ENABLE))
    time.sleep(0.0005)
    bus.write_byte(I2C_ADDR, (bits & ~ENABLE))
    time.sleep(0.0005)

# 定義天氣圖示的動態點陣圖 (每個字符是 5x8 點陣)
weather_symbols = {
    'sunny': [
        [  # 第一幀
            0b00100,
            0b10101,
            0b01110,
            0b11111,
            0b01110,
            0b10101,
            0b00100,
            0b00000
        ],
        [  # 第二幀
            0b00100,
            0b01110,
            0b11111,
            0b11111,
            0b11111,
            0b01110,
            0b00100,
            0b00000
        ]
    ],
    'cloudy': [
        [  # 第一幀
            0b00000,
            0b01110,
            0b10001,
            0b10001,
            0b11111,
            0b00000,
            0b00000,
            0b00000
        ],
        [  # 第二幀
            0b00000,
            0b00000,
            0b01110,
            0b10001,
            0b10001,
            0b11111,
            0b00000,
            0b00000
        ]
    ],
    'rainy': [
        [  # 第一幀
            0b00000,
            0b01110,
            0b10001,
            0b10001,
            0b11111,
            0b00101,
            0b01010,
            0b00000
        ],
        [  # 第二幀
            0b00000,
            0b01110,
            0b10001,
            0b10001,
            0b11111,
            0b01010,
            0b00101,
            0b00000
        ]
    ],
    'thunder': [
        [  # 第一幀
            0b00000,
            0b01110,
            0b10001,
            0b10101,
            0b11111,
            0b00100,
            0b01000,
            0b00000
        ],
        [  # 第二幀
            0b00000,
            0b01110,
            0b10001,
            0b11011,
            0b11111,
            0b01000,
            0b00100,
            0b00000
        ]
    ]
}

# 載入天氣圖示對應
with open('weather_list.json', 'r', encoding='utf-8') as f:
    weather_icons = json.load(f)

def create_custom_char(location, char_map):
    """創建自定義字符"""
    lcd_byte(0x40 | (location * 8), LCD_CMD)
    for line in char_map:
        lcd_byte(line, LCD_CHR)

def create_custom_chars(frame):
    """創建指定幀的自定義字符"""
    create_custom_char(0, weather_symbols['sunny'][frame])
    create_custom_char(1, weather_symbols['cloudy'][frame])
    create_custom_char(2, weather_symbols['rainy'][frame])
    create_custom_char(3, weather_symbols['thunder'][frame])

def lcd_init():
    """初始化 LCD 並加載自定義字符"""
    lcd_byte(0x33, LCD_CMD)
    lcd_byte(0x32, LCD_CMD)
    lcd_byte(0x06, LCD_CMD)
    lcd_byte(0x0C, LCD_CMD)
    lcd_byte(0x28, LCD_CMD)
    lcd_byte(0x01, LCD_CMD)
    time.sleep(0.005)
    create_custom_chars(0)  # 載入第一幀

def lcd_string(message, line):
    """顯示一行文字"""
    message = message.ljust(LCD_WIDTH, " ")
    lcd_byte(line, LCD_CMD)
    for char in message:
        lcd_byte(ord(char), LCD_CHR)

def get_weather():
    """獲取天氣資訊"""
    try:
        response = requests.get(CWB_URL)
        data = response.json()
        
        # 確保資料存在
        if "records" not in data or "location" not in data["records"] or len(data["records"]["location"]) == 0:
            return "API Data Error"
        
        location = data["records"]["location"][0]
        
        # 取得溫度範圍
        min_temp = None
        max_temp = None
        weather = None
        pop = None  # 降雨機率
        
        # 遍歷所有天氣元素
        for element in location["weatherElement"]:
            if element["elementName"] == "MinT":
                min_temp = element["time"][0]["parameter"]["parameterName"]
            elif element["elementName"] == "MaxT":
                max_temp = element["time"][0]["parameter"]["parameterName"]
            elif element["elementName"] == "Wx":
                weather = element["time"][0]["parameter"]["parameterName"]
            elif element["elementName"] == "PoP":  # 新增降雨機率的處理
                pop = element["time"][0]["parameter"]["parameterName"]
        
        # 如果有取得溫度和天氣狀況
        if min_temp and max_temp and weather:
            temp = f"{min_temp}-{max_temp}"
            icon_num, weather_text = weather_icons.get(weather, (None, "Unknown"))
            
            # 如果有降雨機率且天氣和降雨有關,則顯示機率
            rain_related = ["小雨", "中雨", "大雨", "雷陣雨", "局部陣雨", "陰短暫雨"]
            if pop and weather in rain_related:
                weather_text = f"{weather_text}{pop}%"
                
            if icon_num is not None:
                return f"{temp}C {chr(icon_num)} {weather_text}"
            return f"{temp}C {weather_text}"
        else:
            return "Data Missing"
    except Exception as e:
        print(f"Error: {e}")
        return "Weather Err"

def test_api():
    """測試氣象API回傳的資料結構"""
    try:
        response = requests.get(CWB_URL)
        data = response.json()
        print("API 回應狀態:", response.status_code)
        
        if "records" in data and "location" in data["records"]:
            location = data["records"]["location"][0]
            print("地點:", location["locationName"])
            
            # 列出所有氣象元素
            print("\n可用的氣象元素:")
            for element in location["weatherElement"]:
                print(f"- {element['elementName']}: {element['elementDesc']}")
                print(f"  範例值: {element['time'][0]['parameter']['parameterName']}")
                print()
        else:
            print("無法獲取資料，API回傳:", data)
    except Exception as e:
        print(f"API測試發生錯誤: {e}")

def get_indoor_climate():
    """獲取室內溫濕度"""
    try:
        temperature = dht_device.temperature
        humidity = dht_device.humidity
        if temperature is not None and humidity is not None:
            print(f"室內環境: 溫度={temperature}°C, 濕度={humidity}%")
            return f"In:{temperature}C {humidity}%"
        return "DHT Error"
    except Exception as e:
        print(f"DHT11 Error: {e}")
        return "DHT Error"

INDOOR_UPDATE_INTERVAL = 60  # 3分鐘更新一次室內溫濕度
last_indoor_update = 0

def main():
    lcd_init()
    global last_indoor_update  # 修正全域變數問題
    
    last_weather_update = 0
    last_indoor_update = 0  # 初始化
    weather_info = "Loading..."
    indoor_info = "Loading..."
    last_time = time.time()
    frame = 0
    show_weather = True

    while True:
        current_time = time.time()
        now = datetime.now()
        separator = ':' if now.second % 2 == 0 else ' '
        time_str = now.strftime(f"%b%d %a %H{separator}%02M")
        centered_time = time_str.center(LCD_WIDTH)
        
        # 每60秒更新一次資訊
        if current_time - last_weather_update > 60:
            weather_info = get_weather()
            indoor_info = get_indoor_climate()
            last_weather_update = current_time
            last_indoor_update = current_time
            print(f"已更新資訊: {weather_info} | {indoor_info}")

        # 更新動畫幀
        create_custom_chars(frame)
        frame = (frame + 1) % 2
        
        # 顯示時間在第一行
        lcd_string(centered_time, LCD_LINE_1)
        
        # 根據切換狀態顯示天氣或室內資訊
        if show_weather:
            lcd_string(weather_info.center(LCD_WIDTH), LCD_LINE_2)
        else:
            lcd_string(indoor_info.center(LCD_WIDTH), LCD_LINE_2)
        
        # 每 DISPLAY_SWITCH_TIME 秒切換一次顯示內容
        if int(time.time()) % DISPLAY_SWITCH_TIME == 0:
            show_weather = not show_weather
        
        # 每 INDOOR_UPDATE_INTERVAL 秒更新一次室內溫濕度
        if time.time() - last_indoor_update > INDOOR_UPDATE_INTERVAL:
            indoor_info = get_indoor_climate()
            last_indoor_update = time.time()
        
        next_time = last_time + 1
        sleep_time = max(0, next_time - time.time())
        time.sleep(sleep_time)
        last_time = next_time

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("程式已由使用者中斷")
    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        # 清空LCD顯示
        try:
            lcd_byte(0x01, LCD_CMD)
            print("LCD已清空")
        except:
            pass