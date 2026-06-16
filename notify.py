import requests
from bs4 import BeautifulSoup
import urllib3
import os
import json
import re
from urllib.parse import urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN   = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
SEEN_FILE = "seen_ids.json"

# INIT_MODE=true 로 실행하면 현재 공지를 모두 "읽음"으로 저장만 하고 알림은 안 보냄
INIT_MODE = os.environ.get("INIT_MODE", "false").lower() == "true"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

SITES = [
    {"id": "capd",    "name": "📋 전남대 취업진로포털",      "url": "https://capd.jnu.ac.kr/RecrProgram/RegProgram.aspx", "type": "capd"},
    {"id": "aicoss",  "name": "🤖 AI융합대학사업단",          "url": "https://aicoss.kr/www/notice/?cate=%EC%A0%84%EB%82%A8%EB%8C%80%ED%95%99%EA%B5%90", "type": "aicoss"},
    {"id": "sojoong", "name": "💻 SW중심대학사업단",          "url": "https://sojoong.kr/notice/notice-board/", "type": "sojoong"},
    {"id": "juice",   "name": "🔬 반도체특성화대학사업단",    "url": "https://www.juice-semi.kr/jnu/main/?menu=63", "type": "juice"},
    {"id": "eng",     "name": "⚙️ 공과대학",                 "url": "https://eng.jnu.ac.kr/eng/7343/subview.do", "type": "k2web"},
    {"id": "eceng",   "name": "🖥️ 전자컴퓨터공학부",         "url": "https://eceng.jnu.ac.kr/bbs/eceng/3287/artclList.do", "type": "k2web"},
]


def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_seen(seen: dict):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)


def send_telegram(text: str):
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    resp = requests.post(api_url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }, timeout=10)
    resp.raise_for_status()


def get_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return BeautifulSoup(resp.text, "html.parser")


def parse_capd(soup, url):
    notices = []
    if "로그인후 이용가능" in soup.text:
        return notices
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "Seq=" not in href:
            continue
        seq = href.split("Seq=")[-1].split("&")[0]
        title = a.get_text(strip=True)
        if not title:
            continue
        link = f"https://capd.jnu.ac.kr/RecrProgram/{href}" if not href.startswith("http") else href
        notices.append({"id": seq, "title": title, "link": link})
    return notices


def parse_aicoss(soup, url):
    notices = []
    for row in soup.select("table tbody tr"):
        a = row.find("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        m = re.search(r"movePageView\((\d+)\)", str(a))
        if not m:
            continue
        post_id = m.group(1)
        link = f"https://aicoss.kr/www/notice/?uid={post_id}&mod=document"
        notices.append({"id": post_id, "title": title, "link": link})
    return notices


def parse_sojoong(soup, url):
    notices = []
    for a in soup.select("td.kboard-list-title a, h2.entry-title a, .kboard-list a"):
        title = a.get_text(strip=True)
        link = a.get("href", "")
        if not title or not link:
            continue
        m = re.search(r"uid=(\d+)", link)
        post_id = m.group(1) if m else link.split("/")[-2]
        notices.append({"id": post_id, "title": title, "link": link})
    return notices


def parse_juice(soup, url):
    notices = []
    for a in soup.select("ul li a, .bbs_list a"):
        href = a.get("href", "")
        if "no=" not in href and "mode=view" not in href:
            continue
        title = a.get_text(strip=True)
        if not title:
            continue
        m = re.search(r"no=(\d+)", href)
        post_id = m.group(1) if m else href
        link = f"https://www.juice-semi.kr{href}" if href.startswith("/") else href
        notices.append({"id": post_id, "title": title, "link": link})
    return notices


def parse_k2web(soup, url):
    notices = []
    for a in soup.select("table tbody tr td a"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not title or not href:
            continue
        if "artclView" not in href and "subview" not in href:
            continue
        m = re.search(r"/(\d+)/artclView", href)
        post_id = m.group(1) if m else href
        link = urljoin(url, href)
        notices.append({"id": post_id, "title": title, "link": link})
    return notices


PARSERS = {
    "capd":    parse_capd,
    "aicoss":  parse_aicoss,
    "sojoong": parse_sojoong,
    "juice":   parse_juice,
    "k2web":   parse_k2web,
}


def main():
    if INIT_MODE:
        print("=== 초기화 모드: 현재 공지를 읽음으로 저장 (알림 없음) ===")
    else:
        print("=== 전남대 공지사항 확인 시작 ===")

    seen = load_seen()
    total_new = 0

    for site in SITES:
        site_id = site["id"]
        seen.setdefault(site_id, [])
        seen_set = set(seen[site_id])

        print(f"\n[{site['name']}] 확인 중...")
        try:
            soup = get_soup(site["url"])
            notices = PARSERS[site["type"]](soup, site["url"])
            print(f"  → {len(notices)}개 공지 파싱됨")
        except Exception as e:
            print(f"  ⚠️ 오류: {e}")
            if not INIT_MODE:
                send_telegram(f"⚠️ 크롤링 오류\n{site['name']}\n{e}")
            continue

        if not notices:
            print("  → 공지사항을 찾지 못했습니다")
            continue

        for notice in notices:
            if notice["id"] in seen_set:
                continue

            if INIT_MODE:
                # 초기화 모드: 알림 없이 읽음 처리만
                seen_set.add(notice["id"])
                print(f"  📌 읽음 처리: {notice['title'][:40]}")
            else:
                # 일반 모드: 새 공지 알림 전송
                msg = (
                    f"🔔 <b>새 공지사항</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{site['name']}\n\n"
                    f"📌 <b>{notice['title']}</b>\n\n"
                    f"🔗 {notice['link']}"
                )
                try:
                    send_telegram(msg)
                    seen_set.add(notice["id"])
                    total_new += 1
                    print(f"  ✅ 전송: {notice['title'][:40]}")
                except Exception as e:
                    print(f"  ❌ 전송 실패: {e}")

        seen[site_id] = list(seen_set)

    save_seen(seen)

    if INIT_MODE:
        print(f"\n=== 초기화 완료! 다음 실행부터 새 공지만 알림 전송됩니다 ===")
    else:
        print(f"\n=== 완료: 총 {total_new}건 새 공지 전송 ===")


if __name__ == "__main__":
    main()
