import requests
from bs4 import BeautifulSoup
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN   = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
URL     = "https://capd.jnu.ac.kr/RecrProgram/RegProgram.aspx"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://capd.jnu.ac.kr/",
}

resp = requests.get(URL, headers=headers, timeout=15, verify=False)
resp.encoding = "utf-8"
soup = BeautifulSoup(resp.text, "html.parser")

# 모든 링크 중 Seq= 포함된 것 출력
links = [a for a in soup.find_all("a", href=True) if "Seq=" in a.get("href","")]
print(f"Seq= 링크 수: {len(links)}")
for a in links[:5]:
    print(a.get_text(strip=True)[:60], "|", a["href"][:80])

# HTML 앞부분 텔레그램으로 전송 (구조 확인용)
def send(text):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id": CHAT_ID, "text": text})

send(f"상태코드: {resp.status_code}\nSeq링크수: {len(links)}\n\nHTML앞부분:\n{resp.text[:1000]}")
