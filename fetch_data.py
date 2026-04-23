import requests, json, os, time
from datetime import datetime

STOCKS = {
    "1.601899": "紫金矿业",
    "1.600519": "贵州茅台",
    "0.300308": "中际旭创",
    "0.300502": "新易盛",
    "1.688981": "中芯国际",
    "1.600875": "东方电气",
    "1.601727": "上海电气",
    "1.600111": "北方稀土",
    "0.002460": "赣锋锂业",
    "0.002384": "东山精密",
    "0.300476": "胜宏科技",
    "0.300751": "迈为股份",
    "0.002475": "立讯精密",
    "1.603259": "巨星科技",
    "0.002008": "大族激光",
    "0.603083": "剑桥科技",
    "0.300570": "太辰光",
    "0.603306": "华懋科技",
    "0.002281": "光迅科技",
    "0.300964": "本川智能",
    "1.688396": "华润微",
    "0.300049": "福瑞股份",
    "1.600547": "山东黄金",
    "1.601600": "中国铝业",
    "0.000630": "铜陵有色",
    "1.603993": "洛阳钼业",
    "0.002738": "中矿资源",
    "0.603799": "华友钴业",
    "0.000831": "五矿稀土",
    "0.300999": "金龙鱼",
}

FUNDS = {
    "240022": "华宝资源优选",
    "003365": "平安鑫安混合",
    "015780": "永赢高端装备",
    "013942": "华宝稀有金属",
    "004320": "前海开源乐享",
}

os.makedirs("data", exist_ok=True)

# Fetch stock K-line data
manifest = {"stocks": {}, "funds": {}, "updated": datetime.now().isoformat()}

for secid, name in STOCKS.items():
    code = secid.split(".")[1]
    try:
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&secid={secid}&beg=20250101&end=20260423"
        r = requests.get(url, timeout=30)
        data = r.json()
        if data.get("data") and data["data"].get("klines"):
            klines = data["data"]["klines"]
            csv_path = f"data/stock_{code}.csv"
            with open(csv_path, "w") as f:
                f.write("date,open,close,high,low,volume,amount,amplitude\n")
                for line in klines:
                    parts = line.split(",")
                    if len(parts) >= 6:
                        f.write(f"{parts[0]},{parts[1]},{parts[2]},{parts[3]},{parts[4]},{parts[5]},{parts[6] if len(parts)>6 else 0},{parts[7] if len(parts)>7 else 0}\n")
            manifest["stocks"][code] = {"name": name, "rows": len(klines), "csv": csv_path}
            print(f"  {code} {name}: {len(klines)} rows")
        else:
            print(f"  {code} {name}: no data")
            manifest["stocks"][code] = {"name": name, "rows": 0, "error": "no data"}
    except Exception as e:
        print(f"  {code} {name}: ERROR {e}")
        manifest["stocks"][code] = {"name": name, "rows": 0, "error": str(e)}
    time.sleep(0.5)

# Fetch fund NAV data
for fund_code, fund_name in FUNDS.items():
    try:
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&secid=0.{fund_code}&beg=20250101&end=20260423"
        r = requests.get(url, timeout=30)
        data = r.json()
        if data.get("data") and data["data"].get("klines"):
            klines = data["data"]["klines"]
            csv_path = f"data/fund_{fund_code}.csv"
            with open(csv_path, "w") as f:
                f.write("date,nav,close,high,low,volume\n")
                for line in klines:
                    parts = line.split(",")
                    if len(parts) >= 6:
                        f.write(f"{parts[0]},{parts[1]},{parts[2]},{parts[3]},{parts[4]},{parts[5]}\n")
            manifest["funds"][fund_code] = {"name": fund_name, "rows": len(klines), "csv": csv_path}
            print(f"  {fund_code} {fund_name}: {len(klines)} rows")
        else:
            print(f"  {fund_code} {fund_name}: no data")
            manifest["funds"][fund_code] = {"name": fund_name, "rows": 0, "error": "no data"}
    except Exception as e:
        print(f"  {fund_code} {fund_name}: ERROR {e}")
        manifest["funds"][fund_code] = {"name": fund_name, "rows": 0, "error": str(e)}
    time.sleep(0.5)

with open("data/manifest.json", "w") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2, default=str)

print(f"\nDone: {len(manifest['stocks'])} stocks, {len(manifest['funds'])} funds")
