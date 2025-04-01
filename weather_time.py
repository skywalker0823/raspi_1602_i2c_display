import smbus2
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

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

# ☀️ 天氣譯名
weather_dict = {
    "晴時多雲": "Sunny",
    "多雲時晴": "Cloudy/Sun",
    "多雲": "Cloudy",
    "陰天": "Overcast",
    "小雨": "Rain",
    "中雨": "Rain++",
    "大雨": "HeavyRain",
    "雷陣雨": "Thunder",
    "局部陣雨": "Shower",
    "多雲時陰": "Cloudy",
    "陰短暫雨": "Overcast",
}

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

# 更新天氣圖示對應
weather_icons = {
    # 晴天系列 (代碼 1-3)
    "晴天": (0, "Clear"),
    "晴時多雲": (0, "MClear"),
    "多雲時晴": (1, "PClear"),
    
    # 多雲系列 (代碼 4-7)
    "多雲": (1, "Cloud"),
    "多雲時陰": (1, "MCloud"),
    "陰時多雲": (1, "MCloud"),
    "陰天": (1, "Cloud"),
    
    # 陣雨系列 (代碼 8-11)
    "多雲陣雨": (2, "Rain"),
    "多雲短暫雨": (2, "Rain"),
    "午後短暫陣雨": (2, "Rain"),
    "陰短暫雨": (2, "Rain"),
    "多雲時晴短暫陣雨": (2, "Rain"),
    "多雲時陰短暫陣雨": (2, "Rain"),
    "陰時多雲短暫雨": (2, "Rain"),
    
    # 陣雨/雷雨系列 (代碼 15-18)
    "多雲陣雨或雷雨": (3, "Storm"),
    "陣雨或雷雨": (3, "Storm"),
    "午後雷陣雨": (3, "Storm"),
    "雷陣雨": (3, "Storm"),
    
    # 局部雨系列 (代碼 29-34)
    "多雲局部陣雨": (2, "LRain"),
    "多雲局部短暫雨": (2, "LRain"),
    "局部陣雨": (2, "LRain"),
    "局部短暫雨": (2, "LRain"),
    
    # 有霧系列 (代碼 24-28)
    "有霧": (1, "Foggy"),
    "晨霧": (1, "Foggy"),
    "陰有霧": (1, "Foggy"),
    
    # 雪系列 (代碼 42)
    "下雪": (2, "Snow"),
    "積冰": (2, "Ice"),
    "暴風雪": (2, "Snow"),
}

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

def main():
    lcd_init()
    
    last_weather_update = 0
    weather_info = "Loading..."
    last_time = time.time()
    frame = 0
    
    while True:
        # 取得當前時間
        now = datetime.now()
        # 根據秒數決定冒號或空格
        separator = ':' if now.second % 2 == 0 else ' '
        # 組合時間字串，移除年份，加入星期幾
        time_str = now.strftime(f"%b%d %a %H{separator}%02M")
        centered_time = time_str.center(LCD_WIDTH)
        
        # 每60秒更新一次天氣資訊
        if time.time() - last_weather_update > 60:
            weather_info = get_weather()
            last_weather_update = time.time()
            print(f"已更新天氣資訊: {weather_info}")
        
        # 更新動畫幀
        create_custom_chars(frame)
        frame = (frame + 1) % 2
        
        lcd_string(centered_time, LCD_LINE_1)
        lcd_string(weather_info.center(LCD_WIDTH), LCD_LINE_2)  # 置中天氣資訊
        
        next_time = last_time + 1  # 計算下次應該執行的時間點
        sleep_time = max(0, next_time - time.time())  # 避免 sleep 變成負數
        time.sleep(sleep_time)
        last_time = next_time  # 更新 last_time

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