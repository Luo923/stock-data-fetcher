import requests, json, os, time
from datetime import datetime

# Yahoo Finance API - globally accessible from GitHub Actions
STOCKS = {
    "601899.SS": ("601899", "紫金矿业"),
    "600519.SS": ("600519", "贵州茅台"),
    "300308.SZ": ("300308", "中际旭创"),
    "300502.SZ": ("300502", "新易盛"),
    "688981.SS": ("688981", "中芯国际"),
    "600875.SS": ("600875", "东方电气"),
    "601727.SS": ("601727", "上海电气"),
    "600111.SS": ("600111", "北方稀土"),
    "002460.SZ": ("002460", "赣锋锂业"),
    "002384.SZ": ("002384", "东山精密"),
    "300476.SZ": ("300476", "胜宏科技"),
    "300751.SZ": ("300751", "迈为股份"),
    "002475.SZ": ("002475", "立讯精密"),
    "603259.SS": ("603259", "巨星科技"),
    "002008.SZ": ("002008", "大族激光"),
    "603083.SS": ("603083", "剑桥科技"),
    "300570.SZ": ("300570", "太辰光"),
    "603306.SS": ("603306", "华懋科技"),
    "002281.SZ": ("002281", "光迅科技"),
    "300964.SZ": ("300964", "本川智能"),
    "688396.SS": ("688396", "华润微"),
    "300049.SZ": ("300049", "福瑞股份"),
    "600547.SS": ("600547", "山东黄金"),
    "601600.SS": ("601600", "中国铝业"),
    "000630.SZ": ("000630", "铜陵有色"),
    "603993.SS": ("603993", "洛阳钼业"),
    "002738.SZ": ("002738", "中矿资源"),
    "603799.SS": ("603799", "华友钴业"),
    "000831.SZ": ("000831", "五矿稀土"),
    "300999.SZ": ("300999", "金龙鱼"),
}

FUNDS = {
    "240022": "华宝资源优选",
    "003365": "平安鑫安混合",
    "015780": "永赢高端装备",
    "013942": "华宝稀有金属",
    "004320": "前海开源乐享",
}

os.makedirs("data", exist_ok=True)
manifest = {"stocks": {}, "funds": {}, "updated": datetime.now().isoformat()}

# Use crumb API for Yahoo Finance authentication
def get_yahoo_crumb():
    try:
        r = requests.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return None

crumb = get_yahoo_crumb()
print(f"Yahoo crumb: {'OK' if crumb else 'FAILED'}")

# Fetch stock data
for yahoo_code, (code, name) in STOCKS.items():
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_code}?range=1y&interval=1d"
        headers = {"User-Agent": "Mozilla/5.0"}
        if crumb:
            url += f"&crumb={crumb}"
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            result = data.get("chart", {}).get("result", [{}])[0]
            timestamps = result.get("timestamp", [])
            quotes = result.get("indicators", {}).get("quote", [{}])[0]
            closes = quotes.get("close", [])
            volumes = quotes.get("volume", [])
            opens = quotes.get("open", [])
            highs = quotes.get("high", [])
            lows = quotes.get("low", [])
            
            csv_path = f"data/stock_{code}.csv"
            count = 0
            with open(csv_path, "w") as f:
                f.write("date,open,high,low,close,volume\n")
                for i in range(len(timestamps)):
                    if closes[i] is not None:
                        dt = datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
                        o = opens[i] if opens[i] else ""
                        h = highs[i] if highs[i] else ""
                        l = lows[i] if lows[i] else ""
                        v = volumes[i] if volumes[i] else ""
                        f.write(f"{dt},{o},{h},{l},{closes[i]},{v}\n")
                        count += 1
            manifest["stocks"][code] = {"name": name, "rows": count, "csv": csv_path}
            print(f"  {code} {name}: {count} rows")
        else:
            print(f"  {code} {name}: HTTP {r.status_code}")
            manifest["stocks"][code] = {"name": name, "rows": 0, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        print(f"  {code} {name}: ERROR {e}")
        manifest["stocks"][code] = {"name": name, "rows": 0, "error": str(e)}
    time.sleep(1)

# Fetch fund NAV data from Yahoo (Chinese funds may not be available, try anyway)
for fund_code, fund_name in FUNDS.items():
    try:
        # Try as China fund
        yahoo_code = f"{fund_code}.SZ"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_code}?range=1y&interval=1d"
        headers = {"User-Agent": "Mozilla/5.0"}
        if crumb:
            url += f"&crumb={crumb}"
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            result = data.get("chart", {}).get("result", [{}])[0]
            timestamps = result.get("timestamp", [])
            quotes = result.get("indicators", {}).get("quote", [{}])[0]
            closes = quotes.get("close", [])
            
            csv_path = f"data/fund_{fund_code}.csv"
            count = 0
            with open(csv_path, "w") as f:
                f.write("date,close\n")
                for i in range(len(timestamps)):
                    if closes[i] is not None:
                        dt = datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
                        f.write(f"{dt},{closes[i]}\n")
                        count += 1
            manifest["funds"][fund_code] = {"name": fund_name, "rows": count, "csv": csv_path}
            print(f"  {fund_code} {fund_name}: {count} rows")
        else:
            print(f"  {fund_code} {fund_name}: HTTP {r.status_code}")
            manifest["funds"][fund_code] = {"name": fund_name, "rows": 0, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        print(f"  {fund_code} {fund_name}: ERROR {e}")
        manifest["funds"][fund_code] = {"name": fund_name, "rows": 0, "error": str(e)}
    time.sleep(1)

with open("data/manifest.json", "w") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2, default=str)

print(f"\nDone: {len(manifest['stocks'])} stocks, {len(manifest['funds'])} funds")
total_rows = sum(s.get('rows',0) for s in manifest['stocks'].values())
print(f"Total data rows: {total_rows}")
