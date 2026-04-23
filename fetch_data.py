
import akshare as ak
import time
import pandas as pd
import os, json
from datetime import datetime, timedelta

STOCKS = {
    "601899": "紫金矿业",
    "600519": "贵州茅台",
    "300308": "中际旭创",
    "300502": "新易盛",
    "688981": "中芯国际",
    "600875": "东方电气",
    "601727": "上海电气",
    "600111": "北方稀土",
    "002460": "赣锋锂业",
    "300750": "宁德时代",
    "002384": "东山精密",
    "300476": "胜宏科技",
    "002475": "立讯精密",
    "600547": "山东黄金",
    "603993": "洛阳钼业",
    "000630": "铜陵有色",
    "601600": "中国铝业",
    "600036": "招商银行",
    "000858": "五粮液",
    "603083": "剑桥科技",
}

end_date = datetime.now().strftime("%Y%m%d")
start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

os.makedirs("data", exist_ok=True)
manifest = []

for code, name in STOCKS.items():
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                start_date=start_date, end_date=end_date, adjust="qfq")
        filepath = f"data/{code}.csv"
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        manifest.append({"code": code, "name": name, "rows": len(df),
                         "start": df["日期"].iloc[0] if len(df)>0 else "",
                         "end": df["日期"].iloc[-1] if len(df)>0 else ""})
        print(f"  {code} {name}: {len(df)} rows")
    except Exception as e:
        print(f"  {code} {name}: ERROR {e}")
        manifest.append({"code": code, "name": name, "rows": 0, "error": str(e)})

with open("data/manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2, default=str)

print(f"\nDone: {sum(1 for m in manifest if m['rows']>0)}/{len(STOCKS)} stocks fetched")
