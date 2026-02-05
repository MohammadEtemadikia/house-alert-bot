import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from telegram import Bot
import asyncio

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

DATA_FILE = "seen_ads.json"

seen_ads = set()
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            seen_ads = set(json.load(f))
    except:
        pass

async def send_telegram(msg):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=msg, disable_web_page_preview=True)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_pararius_listings():
    listings = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        url = "https://www.pararius.com/apartments/nederland/600-1000/25m2"
        r = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        
        # پیدا کردن همه کارت‌های آگهی (ساختار فعلی ۲۰۲۶)
        items = soup.select("div[class*='search-result'] article, li[class*='listing'], div[class*='property-card']")
        if not items:
            items = soup.find_all("a", href=lambda h: h and "/for-rent/" in h)
        
        for item in items[:15]:
            a = item.find("a") if item.name != "a" else item
            if not a:
                continue
            href = a.get("href")
            if not href:
                continue
            link = "https://www.pararius.com" + href if href.startswith("/") else href
            unique = link.split("?")[0].rstrip("/")
            if unique in seen_ads:
                continue
            
            title = a.get_text(strip=True) or item.find(["h2", "h3", "span"]).get_text(strip=True) if item.find(["h2", "h3", "span"]) else "بدون عنوان"
            
            price_tag = item.find(class_=re.compile(r"price|rent", re.I))
            price = price_tag.get_text(strip=True) if price_tag else ""
            
            seen_ads.add(unique)
            listings.append(f"🆕 Pararius\n{title}\n{price}\n{link}")
    except Exception as e:
        print(f"Pararius error: {e}")
    return listings

def get_funda_listings():
    listings = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        url = "https://www.funda.nl/zoeken/huur?selected_area=[%22nl%22]&price=%22500-1000%22&publication_date=%221%22"
        r = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        
        # ساختار فعلی Funda ۲۰۲۶
        items = soup.select("li[data-test-id='search-result-item'], div[class*='search-result'], article")
        if not items:
            items = soup.find_all("a", href=lambda h: h and "/koop/" in h or "/huur/" in h)
        
        for item in items[:15]:
            a = item.find("a") if item.name != "a" else item
            if not a:
                continue
            href = a.get("href")
            if not href:
                continue
            link = "https://www.funda.nl" + href if href.startswith("/") else href
            unique = link.split("?")[0].rstrip("/")
            if unique in seen_ads:
                continue
            
            title = a.get_text(strip=True) or item.find(["h2", "h3", "span"]).get_text(strip=True) if item.find(["h2", "h3", "span"]) else "بدون عنوان"
            
            price_tag = item.find(class_=re.compile(r"price|kosten", re.I))
            price = price_tag.get_text(strip=True) if price_tag else ""
            
            seen_ads.add(unique)
            listings.append(f"🆕 Funda\n{title}\n{price}\n{link}")
    except Exception as e:
        print(f"Funda error: {e}")
    return listings

async def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # پیام شروع فقط بار اول
    if not os.path.exists(DATA_FILE):
        await send_telegram(f"✅ اسکریپر شروع شد!\nزمان: {now}\nهر ساعت چک می‌کنه")

    par_new = get_pararius_listings()
    fun_new = get_funda_listings()
    all_new = par_new + fun_new

    if all_new:
        msg = f"آگهی جدید پیدا شد ({len(all_new)}) — {now}\n\n" + "\n─────────────────\n".join(all_new)
        await send_telegram(msg)

    # ذخیره seen_ads
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_ads), f, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(main())
