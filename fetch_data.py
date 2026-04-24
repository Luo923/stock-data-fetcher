import requests, json, os, time, re
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

# Fund list with correct names - using eastmoney API for NAV + holdings
FUNDS = {
    "240022": "华宝资源优选混合A",
    "011369": "华商均衡成长混合A",
    "004320": "前海开源沪港深乐享生活",
    "015790": "永赢高端装备智选混合发起C",
}

os.makedirs("data", exist_ok=True)
os.makedirs("data/fund_holdings", exist_ok=True)
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

# Fetch fund NAV data from eastmoney API (works on GitHub Actions)
def fetch_fund_nav(fund_code, fund_name):
    """Fetch fund historical NAV from eastmoney API"""
    try:
        # eastmoney fund history NAV API
        url = f"https://api.fund.eastmoney.com/f10/lsjz"
        params = {
            "fundCode": fund_code,
            "pageIndex": 1,
            "pageSize": 250,
            "startDate": "",
            "endDate": "",
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": f"https://fundf10.eastmoney.com/jjjz_{fund_code}.html",
        }
        r = requests.get(url, params=params, headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            nav_list = data.get("Data", {}).get("LSJZList", [])
            if nav_list:
                csv_path = f"data/fund_{fund_code}.csv"
                count = 0
                with open(csv_path, "w") as f:
                    f.write("date,nav,acc_nav,change_pct\n")
                    for item in nav_list:
                        fsrq = item.get("FSRQ", "")
                        dwjz = item.get("DWJZ", "")
                        ljjz = item.get("LJJZ", "")
                        jzzzl = item.get("JZZZL", "")
                        if fsrq and dwjz:
                            f.write(f"{fsrq},{dwjz},{ljjz},{jzzzl}\n")
                            count += 1
                manifest["funds"][fund_code] = {"name": fund_name, "rows": count, "csv": csv_path}
                print(f"  {fund_code} {fund_name} NAV: {count} rows")
                return count
        # Fallback: try another eastmoney endpoint
        url2 = f"https://fund.eastmoney.com/f10/F10DataApi.aspx"
        params2 = {
            "type": "lsjz",
            "code": fund_code,
            "page": 1,
            "sdate": "",
            "edate": "",
            "per": 250,
        }
        r2 = requests.get(url2, params=params2, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        if r2.status_code == 200:
            # Parse HTML table
            rows = re.findall(r'<tr>(.*?)</tr>', r2.text, re.DOTALL)
            if rows:
                csv_path = f"data/fund_{fund_code}.csv"
                count = 0
                with open(csv_path, "w") as f:
                    f.write("date,nav,acc_nav,change_pct\n")
                    for row in rows[1:]:  # skip header
                        cols = re.findall(r'<td[^>]*>(.*?)</td>', row)
                        if len(cols) >= 4:
                            f.write(f"{cols[0]},{cols[1]},{cols[2]},{cols[3]}\n")
                            count += 1
                manifest["funds"][fund_code] = {"name": fund_name, "rows": count, "csv": csv_path}
                print(f"  {fund_code} {fund_name} NAV(fallback): {count} rows")
                return count
        print(f"  {fund_code} {fund_name} NAV: no data")
        manifest["funds"][fund_code] = {"name": fund_name, "rows": 0, "error": "no nav data"}
        return 0
    except Exception as e:
        print(f"  {fund_code} {fund_name} NAV: ERROR {e}")
        manifest["funds"][fund_code] = {"name": fund_name, "rows": 0, "error": str(e)}
        return 0

def fetch_fund_holdings(fund_code, fund_name):
    """Fetch fund top-10 stock holdings from eastmoney"""
    try:
        url = "https://fundf10.eastmoney.com/FundArchivesDatas.aspx"
        params = {
            "type": "jjcc",
            "code": fund_code,
            "topline": 10,
            "year": datetime.now().year,
            "month": "",
            "rt": "0." + str(int(time.time() * 1000))[-10:],
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": f"https://fundf10.eastmoney.com/ccmx_{fund_code}.html",
        }
        r = requests.get(url, params=params, headers=headers, timeout=30)
        if r.status_code == 200 and "暂无数据" not in r.text:
            # Parse holdings from HTML
            holdings = []
            rows = re.findall(r'<tr>(.*?)</tr>', r.text, re.DOTALL)
            for row in rows:
                cols = re.findall(r'<td[^>]*>(.*?)</td>', row)
                links = re.findall(r'<a[^>]*>(.*?)</a>', row)
                if len(cols) >= 6:
                    stock_code = re.sub(r'<[^>]+>', '', cols[0]).strip()
                    stock_name = re.sub(r'<[^>]+>', '', cols[1]).strip() if len(cols) > 1 else ""
                    if not stock_name and links:
                        stock_name = re.sub(r'<[^>]+>', '', links[0]).strip()
                    holdings.append({
                        "code": stock_code,
                        "name": stock_name,
                        "share": cols[2] if len(cols) > 2 else "",
                        "value": cols[3] if len(cols) > 3 else "",
                        "ratio": cols[4] if len(cols) > 4 else "",
                    })
            if holdings:
                hold_path = f"data/fund_holdings/{fund_code}.json"
                with open(hold_path, "w", encoding="utf-8") as f:
                    json.dump({"fund_code": fund_code, "fund_name": fund_name, 
                               "holdings": holdings, "updated": datetime.now().isoformat()}, 
                              f, ensure_ascii=False, indent=2)
                manifest["funds"][fund_code]["holdings"] = hold_path
                manifest["funds"][fund_code]["holdings_count"] = len(holdings)
                print(f"  {fund_code} {fund_name} holdings: {len(holdings)} stocks")
            else:
                print(f"  {fund_code} {fund_name} holdings: parsed 0")
        else:
            print(f"  {fund_code} {fund_name} holdings: no data")
    except Exception as e:
        print(f"  {fund_code} {fund_name} holdings: ERROR {e}")

# Fetch fund data
for fund_code, fund_name in FUNDS.items():
    fetch_fund_nav(fund_code, fund_name)
    fetch_fund_holdings(fund_code, fund_name)
    time.sleep(1)

with open("data/manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2, default=str)

print(f"\nDone: {len(manifest['stocks'])} stocks, {len(manifest['funds'])} funds")
total_rows = sum(s.get('rows',0) for s in manifest['stocks'].values())
fund_rows = sum(f.get('rows',0) for f in manifest['funds'].values())
print(f"Total data rows: stocks={total_rows}, funds={fund_rows}")