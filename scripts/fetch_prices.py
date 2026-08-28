"""
키움 REST API로 국내/해외 종목의 현재가·52주 최고/최저를 조회해
prices.json 파일로 저장한다.

필요한 환경변수 (GitHub Actions Secrets로 주입됨):
  KIWOOM_APPKEY
  KIWOOM_SECRETKEY

config/stocks.json 에 조회할 종목 목록을 적어두면 된다.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error

API_HOST = "https://api.kiwoom.com"
KST = timezone(timedelta(hours=9))

APPKEY = os.environ.get("KIWOOM_APPKEY", "")
SECRETKEY = os.environ.get("KIWOOM_SECRETKEY", "")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "stocks.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "prices.json")


def http_post(path, headers, body):
    url = API_HOST + path
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[HTTP {e.code}] {path} -> {e.read().decode('utf-8', 'ignore')}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[ERROR] {path} -> {e}", file=sys.stderr)
        return None


def get_token():
    if not APPKEY or not SECRETKEY:
        print("KIWOOM_APPKEY / KIWOOM_SECRETKEY 환경변수가 없습니다.", file=sys.stderr)
        sys.exit(1)
    body = {"grant_type": "client_credentials", "appkey": APPKEY, "secretkey": SECRETKEY}
    res = http_post("/oauth2/token", {"Content-Type": "application/json;charset=UTF-8"}, body)
    if not res or "token" not in res:
        print("토큰 발급 실패:", res, file=sys.stderr)
        sys.exit(1)
    return res["token"]


def clean_num(v):
    """키움 숫자 필드는 '+70600' 처럼 부호가 붙어 문자열로 온다."""
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    if s in ("", "-", "+"):
        return None
    try:
        return abs(float(s))
    except ValueError:
        return None


def fetch_domestic(token, stk_cd):
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}",
        "api-id": "ka10001",
    }
    res = http_post("/api/dostk/stkinfo", headers, {"stk_cd": stk_cd})
    if not res:
        return None
    return {
        "currentPrice": clean_num(res.get("cur_prc")),
        "week52High": clean_num(res.get("250hgst")),
        "week52Low": clean_num(res.get("250lwst")),
    }


def fetch_overseas(token, stk_cd, exchange):
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}",
        "api-id": "usa20100",
    }
    res = http_post("/api/us/mrkcond", headers, {"stex_tp": exchange, "stk_cd": stk_cd})
    if not res:
        return None
    return {
        "currentPrice": clean_num(res.get("cur_prc")),
        "week52High": clean_num(res.get("52wk_hgst_pric")),
        "week52Low": clean_num(res.get("52wk_lwst_pric")),
    }


def main():
    if not os.path.exists(CONFIG_PATH):
        print(f"설정 파일이 없습니다: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(CONFIG_PATH, encoding="utf-8") as f:
        stocks = json.load(f)

    token = get_token()
    result = {}
    now_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")

    for s in stocks:
        market = s.get("market")
        ticker = (s.get("ticker") or "").strip()
        if not ticker:
            continue
        key = f"{market}::{ticker.upper()}"

        if market == "domestic":
            data = fetch_domestic(token, ticker)
        elif market == "overseas":
            exchange = s.get("exchange", "ND")  # ND=나스닥, NY=뉴욕, NA=아멕스
            data = fetch_overseas(token, ticker, exchange)
        else:
            continue

        if data:
            data["asOf"] = now_str
            result[key] = data
            print(f"OK  {key} -> {data}")
        else:
            print(f"FAIL {key}", file=sys.stderr)

        time.sleep(0.3)  # TR 호출 제한 대비

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"updatedAt": now_str, "prices": result}, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: {OUTPUT_PATH} ({len(result)}개 종목)")


if __name__ == "__main__":
    main()
