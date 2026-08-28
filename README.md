# 주식 관리 앱 + 키움 REST API 자동 시세

## 폴더 구조
```
index.html                 ← 실제 앱 (GitHub Pages로 배포)
prices.json                ← 자동 생성됨 (건드리지 마세요)
config/stocks.json         ← 조회할 종목 목록 (직접 수정)
scripts/fetch_prices.py    ← 키움 API 호출 스크립트
.github/workflows/update-prices.yml  ← 자동 실행 설정
```

## 처음 설정하는 방법

### 1. 이 폴더 전체를 GitHub 저장소에 업로드
`index.html`, `prices.json`은 없어도 됨(자동 생성), 나머지 전부 올리기.

### 2. GitHub Secrets에 키움 API 키 등록
저장소 → **Settings → Secrets and variables → Actions → New repository secret**
- `KIWOOM_APPKEY` = 키움 개발자센터에서 발급받은 앱키
- `KIWOOM_SECRETKEY` = 시크릿키

(여기 등록하면 코드에는 절대 노출되지 않습니다.)

### 3. 조회할 종목 등록
`config/stocks.json` 파일을 GitHub 웹에서 직접 열어 수정:
```json
[
  { "market": "domestic", "name": "삼성전자", "ticker": "005930" },
  { "market": "overseas", "name": "Apple", "ticker": "AAPL", "exchange": "ND" }
]
```
- market: "domestic"(국내) 또는 "overseas"(해외)
- 해외는 exchange 필수: NASDAQ=ND, NYSE=NY, AMEX=NA
- 앱의 "종목코드/티커" 칸에 입력한 값과 **정확히 일치**해야 자동으로 매칭됩니다.

### 4. GitHub Pages 켜기
Settings → Pages → Branch: main / root → Save

### 5. Actions 켜기 & 첫 실행
저장소 상단 **Actions** 탭 → 좌측 "Update stock prices" 선택 → **Run workflow** 버튼으로 수동 1회 실행
(정상 동작하면 `prices.json`이 자동 커밋됩니다. 이후로는 스케줄에 따라 자동 실행됩니다.)

## 동작 방식
- 장중(국내 09~15:30 KST, 미국 23:30~06:00 KST) 30분마다 자동 실행
- 종목코드가 `config/stocks.json`과 일치하는 관심종목/보유종목은 현재가·52주 최고/최저가 **자동** 표시
- 일치하지 않는 종목은 기존처럼 수동 입력 값 그대로 사용됨
- 앱 화면 상단에 "시세 갱신: YYYY-MM-DD HH:MM KST"로 마지막 갱신 시각 표시

## 문제 생기면
Actions 탭 → 실패한 실행(빨간 X) 클릭 → 로그 확인. 대부분 앱키/시크릿 오타이거나, 종목코드 형식 문제입니다.
