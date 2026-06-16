# 전남대 취업프로그램 공지 알림봇 🤖

전남대학교 취업진로포털의 새 공지사항을 텔레그램으로 알려주는 봇입니다.

## 알림 시간
- 오전 10:30
- 오후 2:00
- 오후 7:00

---

## 설치 방법

### 1. 이 레포지토리를 GitHub에 업로드

GitHub에서 **New repository** 생성 후 아래 파일들을 업로드:
```
notify.py
.github/workflows/notify.yml
```

### 2. GitHub Secrets 등록 (⚠️ 필수)

GitHub 레포지토리 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Name | Value |
|------|-------|
| `TELEGRAM_TOKEN` | 텔레그램 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 텔레그램 채팅 ID |

### 3. Actions 활성화 확인

레포지토리 → **Actions** 탭 → "I understand my workflows" 버튼 클릭 (처음 한 번만)

### 4. 테스트 실행

Actions 탭 → **전남대 취업프로그램 공지 알림** → **Run workflow** 버튼으로 즉시 테스트 가능

---

## 주의사항

- 페이지 HTML 구조가 변경되면 `notify.py`의 파싱 코드 수정이 필요할 수 있습니다.
- 텔레그램 토큰은 절대 코드에 직접 넣지 마세요. Secrets에만 저장하세요.
