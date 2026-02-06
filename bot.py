import requests
import json
from bs4 import BeautifulSoup
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PARARIUS_URL = "https://www.pararius.com/apartments/nederland/600-1000/25m2/since-1"
FUNDA_URL = "https://www.funda.nl/zoeken/huur?selected_area=[%22nl%22]&price=%22600-1000%22&publication_date=%221%22"

HEADERS = {"User-Agent": "Mozilla/5.0"}

def send_message(text, image=None):
    if image:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        data = {"chat_id": CHAT_ID, "photo": image, "caption": text}
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

def load_seen():
    try:
        with open("seen.json") as f:
            return json.load(f)
    except:
        return []

def save_seen(data):
    with open("seen.json", "w") as f:
        json.dump(data, f)

def check_pararius(seen):
    r = requests.get(PARARIUS_URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    for ad in soup.select("section.search-list__item"):
        a = ad.find("a")
        img = ad.find("img")
        if not a or not img:
            continue

        link = "https://www.pararius.com" + a["href"]
        if link in seen:
            continue

        image = img.get("data-src")
        send_message(f"🏠 آگهی جدید Pararius\n{link}", image)
        seen.append(link)

def check_funda(seen):
    r = requests.get(FUNDA_URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    for ad in soup.select("div.search-result"):
        a = ad.find("a")
        img = ad.find("img")
        if not a or not img:
            continue

        link = "https://www.funda.nl" + a["href"]
        if link in seen:
            continue

        send_message(f"🏠 آگهی جدید Funda\n{link}", img["src"])
        seen.append(link)

def main():
    send_message("✅ تست موفق: GitHub Actions به تلگرام وصله")

if __name__ == "__main__":
    main()
