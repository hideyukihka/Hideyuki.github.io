#!/usr/bin/env python3
import os
import json
import requests

def main():
    print("--- Start Status Updater (Rule-based Fallback Only) ---")
    
    # 1. 環境変数の読み込み
    status_file = os.environ.get("STATUS_FILE_PATH", "status.txt")
    meta_file = os.environ.get("STATUS_META_PATH", "status.json")
    
    print(f"Target files: {status_file}, {meta_file}")
    
    # 2. 最新のビットコイン価格と24時間変動率を取得 (CoinGecko API)
    current_status = "START"
    reason = "Market is stable."
    change_24h = 0.0
    
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
        res = requests.get(url, timeout=10).json()
        change_24h = res["bitcoin"]["usd_24h_change"]
        print(f"BTC 24h Change: {change_24h:.2f}%")
        
        # 変動率が ±8% を超える異常ボラティリティの場合は停止
        if abs(change_24h) >= 8.0:
            current_status = "STOP"
            reason = f"High volatility detected. 24h change: {change_24h:.2f}%"
    except Exception as e:
        print(f"Failed to fetch market data: {e}")
        # 取得失敗時は安全のため前回の状態を維持するか、STOPにはしない
    
    # 3. 簡易ニュースチェック (CryptoCompare API)
    try:
        news_url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        news_res = requests.get(news_url, timeout=10).json()
        articles = news_res.get("Data", [])
        
        ng_words = ["hack", "exploit", "scam", "heist", "attack", "stolen", "drain"]
        for article in articles[:5]:  # 直近5件をチェック
            title = article.get("title", "").lower()
            body = article.get("body", "").lower()
            
            for word in ng_words:
                if word in title or word in body:
                    current_status = "STOP"
                    reason = f"Urgent news risk detected: '{word}' found in headlines."
                    break
            if current_status == "STOP":
                break
    except Exception as e:
        print(f"Failed to fetch news data: {e}")

    print(f"Final Decision: {current_status} ({reason})")

    # 4. status.txt の書き込み
    with open(status_file, "w", encoding="utf-8") as f:
        f.write(current_status)
    print(f"Updated {status_file}")

    # 5. status.json の書き込み
    from datetime import datetime
    meta_data = {
        "status": current_status,
        "generated_at_utc": datetime.utcnow().isoformat() + "Z",
        "reason": reason,
        "btc_24h_change_pct": round(change_24h, 2)
    }
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=2, ensure_ascii=False)
    print(f"Updated {meta_file}")

if __name__ == "__main__":
    main()
