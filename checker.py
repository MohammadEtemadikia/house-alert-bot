import requests
from bs4 import BeautifulSoup
import json
import os
import re
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
        print(f"Telegram send error: {e}")

def get_pararius_new():
    new_ads = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        url = "https://www.pararius.com/apartments/nederland/600-1000/25m2"
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # پیدا کردن همه لینک‌های اجاره (الگوی فعلی)
        rental_links = soup.find_all("a", href=re.compile(r"/(studio|apartment|room|flat|house)-for-rent/"))

        for a in rental_links[:20]:  # حداکثر ۲۰ تا چک کنیم
            href = a["href"]
            full_link = "https://www.pararius.com" + href if href.startswith("/") else href
            unique = full_link.split("?")[0].rstrip("/")
            if unique in seen_ads:
                continue

            title = a.get_text(strip=True)
            if not title:
                title = "بدون عنوان"

            # قیمت: جستجو در متن بعدی یا والد
            price = ""
            current = a
            for _ in range(5):  # حداکثر ۵ سطح بعدی بگرد
                if current.next_sibling:
                    txt = str(current.next_sibling).strip()
                    if re.search(r"€\s*\d+|\d+\s*per month", txt, re.I):
                        price = txt
                        break
                current = current.parent if current.parent else None

            # چک New
            is_new = bool(a.find_previous_sibling(string=re.compile(r"New|Nieuw", re.I)) or 
                          "new" in str(a).lower())

            seen_ads.add(unique)
            label = "(New!)" if is_new else ""
            new_ads.append(f"🆕 Pararius {label}\n{title}\n{price}\n{full_link}")

        print(f"Pararius: {len(new_ads)} جدید پیدا شد (از {len(rental_links)} لینک)")
    except Exception as e:
        print(f"Pararius error: {e}")
    return new_ads

def get_funda_new():
    new_ads = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = "https://www.funda.nl/zoeken/huur?selected_area=[%22nl%22]&price=%22500-1000%22&publication_date=%221%22"
        r = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")

        # selector قدیمی + fallback
        items = soup.select("li.search-result, li[class*='result'], div[class*='listing'], article")
        if not items:
            items = soup.find_all("a", href=re.compile(r"/koop/|/huur/|\d{8}/"))

        for item in items[:15]:
            a = item if item.name == "a" else item.find("a")
            if not a or not a.get("href"):
                continue

            href = a["href"]
            full_link = "https://www.funda.nl" + href if href.startswith("/") else href
            unique = full_link.split("?")[0].rstrip("/")
            if unique in seen_ads:
                continue

            title = a.get_text(strip=True) or item.get_text(strip=True)[:100]
            price_tag = item.find(class_=re.compile(r"price|kosten|€"))
            price = price_tag.get_text(strip=True) if price_tag else ""

            is_new = bool(item.find(string=re.compile(r"Nieuw|New", re.I)))

            seen_ads.add(unique)
            label = "(Nieuw!)" if is_new else ""
            new_ads.append(f"🆕 Funda {label}\n{title}\n{price}\n{full_link}")

        print(f"Funda: {len(new_ads)} جدید پیدا شد")
    except Exception as e:
        print(f"Funda error: {e}")
    return new_ads

async def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not os.path.exists(DATA_FILE):
        await send_telegram(f"اسکریپر شروع شد - {now}\nهر ساعت چک می‌کنه (فقط جدیدها ارسال می‌شن)")

    par_new = get_pararius_new()
    fun_new = get_funda_new()
    all_new = par_new + fun_new

    if all_new:
        msg = f"آگهی جدید! ({len(all_new)}) — {now}\n\n" + "\n\n─────────────────\n".join(all_new)
        await send_telegram(msg)
    else:
        print("هیچ آگهی جدیدی پیدا نشد - ممکنه ساختار سایت تغییر کرده باشه")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_ads), f, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(main())
