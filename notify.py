import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup
import os
import json

# ── 설정 ──────────────────────────────────────────────
TOKEN   = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
URL     = "https://capd.jnu.ac.kr/RecrProgram/RegProgram.aspx"
SEEN_FILE = "seen_ids.json"   # 이미 알림 보낸 게시글 ID 저장용
# ──────────────────────────────────────────────────────


def load_seen():
    """이전에 알림 보낸 게시글 ID 목록 불러오기"""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set):
    """알림 보낸 게시글 ID 목록 저장"""
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def send_telegram(text: str):
    """텔레그램 메시지 전송"""
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    resp = requests.post(api_url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    })
    resp.raise_for_status()
    print(f"[전송 완료] {text[:50]}...")


def fetch_notices():
    """공지사항 목록 크롤링"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(URL, headers=headers, timeout=15, verify=False)
    resp.raise_for_status()
    resp.encoding = "utf-8"

    soup = BeautifulSoup(resp.text, "html.parser")

    notices = []

    # ── 테이블 행에서 공지사항 추출 ──────────────────
    # 전남대 취업포털은 <table> 기반 목록 구조
    rows = soup.select("table tbody tr")

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        # 링크 태그에서 제목과 Seq 추출
        a_tag = row.find("a")
        if not a_tag:
            continue

        title = a_tag.get_text(strip=True)
        href  = a_tag.get("href", "")

        # href 예: RegProgram.aspx?Mode=View&Seq=2641
        if "Seq=" not in href:
            continue

        seq = href.split("Seq=")[-1].split("&")[0]
        link = f"https://capd.jnu.ac.kr/RecrProgram/{href}" if not href.startswith("http") else href

        # 날짜 (마지막 td)
        date_text = cells[-1].get_text(strip=True) if cells else ""

        notices.append({
            "seq":   seq,
            "title": title,
            "link":  link,
            "date":  date_text,
        })

    return notices


def main():
    print("공지사항 확인 중...")
    seen = load_seen()

    try:
        notices = fetch_notices()
    except Exception as e:
        send_telegram(f"⚠️ 공지사항 크롤링 오류\n{e}")
        raise

    if not notices:
        print("공지사항을 찾지 못했습니다. HTML 구조가 바뀌었을 수 있어요.")
        send_telegram("⚠️ 공지사항 파싱 실패\n페이지 구조가 변경됐을 수 있습니다.\n확인: https://capd.jnu.ac.kr/RecrProgram/RegProgram.aspx")
        return

    new_count = 0
    for notice in notices:
        if notice["seq"] in seen:
            continue

        msg = (
            f"📢 <b>전남대 취업프로그램 새 공지</b>\n\n"
            f"📌 {notice['title']}\n"
            f"📅 {notice['date']}\n"
            f"🔗 {notice['link']}"
        )
        send_telegram(msg)
        seen.add(notice["seq"])
        new_count += 1

    save_seen(seen)

    if new_count == 0:
        print("새로운 공지사항이 없습니다.")
    else:
        print(f"새 공지사항 {new_count}건 알림 전송 완료!")


if __name__ == "__main__":
    main()
