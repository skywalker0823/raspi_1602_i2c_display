import requests
from dotenv import load_dotenv
import os

# 載入環境變數
load_dotenv()

API_KEY = os.getenv('CWB_API_KEY')
LOCATION_NAME = os.getenv('LOCATION_NAME', '臺北市')
CWB_URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={API_KEY}&locationName={LOCATION_NAME}"

# 天氣圖示對應表（從原始程式複製過來）
weather_icons = {
    # 晴天系列
    "晴天": (0, "Clear"),
    "晴時多雲": (0, "MClear"),
    "多雲時晴": (1, "PClear"),
    
    # 多雲系列
    "多雲": (1, "Cloud"),
    "多雲時陰": (1, "MCloud"),
    "陰時多雲": (1, "MCloud"),
    "陰天": (1, "Cloud"),
    
    # 陣雨系列
    "多雲陣雨": (2, "Rain"),
    "多雲短暫雨": (2, "Rain"),
    "午後短暫陣雨": (2, "Rain"),
    "陰短暫雨": (2, "Rain"),
    
    # 其他天氣類型
    "雷陣雨": (3, "Storm"),
    "局部陣雨": (2, "LRain"),
    "有霧": (1, "Foggy")
}

def test_weather_api():
    print("開始測試天氣 API...")
    try:
        response = requests.get(CWB_URL)
        data = response.json()
        
        print(f"\n1. API 回應狀態碼: {response.status_code}")
        
        if "records" in data and "location" in data["records"]:
            location = data["records"]["location"][0]
            print(f"\n2. 地點: {location['locationName']}")
            
            # 取得天氣描述
            weather = None
            for element in location["weatherElement"]:
                if element["elementName"] == "Wx":
                    weather = element["time"][0]["parameter"]["parameterName"]
                    weather_code = element["time"][0]["parameter"]["parameterValue"]
                    print(f"\n3. 目前天氣: {weather}")
                    print(f"   天氣代碼: {weather_code}")
                    break
            
            # 測試天氣對應
            if weather:
                print("\n4. 測試天氣圖示對應:")
                print(f"   原始天氣描述: {weather}")
                if weather in weather_icons:
                    icon_num, weather_text = weather_icons[weather]
                    print(f"   對應到的圖示: {icon_num}")
                    print(f"   對應到的文字: {weather_text}")
                else:
                    print(f"   *** 錯誤: 在 weather_icons 中找不到 '{weather}' 的對應")
                    print("   可用的天氣類型:")
                    for key in weather_icons.keys():
                        print(f"   - {key}")
            
        else:
            print("錯誤: API 回應中沒有找到天氣資料")
            print("原始回應:", data)
            
    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    test_weather_api()
