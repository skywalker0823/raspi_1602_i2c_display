import json

file_path = r'weather_list.json'

# 讀取檔案內容
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# 替換括號
content = content.replace('(', '[').replace(')', ']')

# 寫回檔案
with open(file_path, 'w', encoding='utf-8') as file:
    file.write(content)

print("替換完成")