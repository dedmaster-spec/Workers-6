import requests
import re
import json
import time
from datetime import datetime

session = requests.Session()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://catcast.tv/",
    "Accept": "*/*",
    "Connection": "keep-alive"
}

session.headers.update(HEADERS)


def log(text):
    with open("logs.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {text}\n")
    print(text)


def extract_m3u8(text):
    patterns = [
        r'https?://[^"]+\.m3u8[^"]*',
        r'https?://[^\'"]+index\.m3u8[^\'"]*'
    ]

    for p in patterns:
        match = re.search(p, text)
        if match:
            return match.group(0)

    return None


def check_stream(url):
    try:
        r = session.head(url, timeout=5)
        return r.status_code == 200
    except:
        return False


def get_stream(url):
    try:
        log(f"🌐 Открываю: {url}")
        r = session.get(url, timeout=10)
        html = r.text

        # 1. Прямой поиск
        stream = extract_m3u8(html)
        if stream:
            log("✔ Найден в HTML")
            return stream

        # 2. channelId
        match_id = re.search(r'channelId["\']?\s*[:=]\s*["\']?(\d+)', html)
        if match_id:
            channel_id = match_id.group(1)
            api_url = f"https://api.catcast.tv/api/channel/{channel_id}"

            log(f"🔗 API: {api_url}")
            r2 = session.get(api_url, timeout=10)

            stream = extract_m3u8(r2.text)
            if stream:
                log("✔ Найден через API")
                return stream

        # 3. fallback JS
        links = re.findall(r'https?://[^"]+', html)
        for link in links:
            if ".m3u8" in link:
                log("✔ Найден fallback")
                return link

        log("❌ Поток не найден")
        return None

    except Exception as e:
        log(f"Ошибка: {e}")
        return None


def main():
    with open("channels.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    playlist = "#EXTM3U\n"

    for ch in data["channels"]:
        name = ch["name"]
        url = ch["url"]

        log(f"\n🔍 Проверка: {name}")

        stream = get_stream(url)

        if stream and check_stream(stream):
            log(f"✅ Работает: {name}")
            playlist += f'#EXTINF:-1,{name}\n{stream}\n'
        else:
            log(f"❌ Не работает: {name}")

        time.sleep(3)

    with open("catcast.m3u8", "w", encoding="utf-8") as f:
        f.write(playlist)


if __name__ == "__main__":
    main()
