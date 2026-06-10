import hashlib
import json
import time
import uuid

import requests


BASE = "https://www.weaquery.com"
LOGIN_URL = BASE + "/weather/user/login/"
CURRENT_URL = BASE + "/weather/user/current/"
EMAIL = "admin02@test.com"
PASSWORD = "123456"
TOTAL = 30
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}


session = requests.Session()
session.headers.update(
    {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
)

login_resp = session.post(
    LOGIN_URL,
    json={"email": EMAIL, "password": PASSWORD, "force_login": True},
    timeout=30,
    proxies=PROXIES,
)
login_body = login_resp.json()
login_data = login_body.get("data", {}) if isinstance(login_body, dict) else {}
access_token = login_data.get("access_token") or login_data.get("token")
sign_key = login_data.get("sign_key") or login_data.get("session_sign_key")

if login_resp.status_code != 200 or login_body.get("code") != 200 or not access_token or not sign_key:
    print(
        json.dumps(
            {
                "stage": "login",
                "http_status": login_resp.status_code,
                "body": login_body,
                "has_access_token": bool(access_token),
                "has_sign_key": bool(sign_key),
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(1)

results = []
for i in range(1, TOTAL + 1):
    timestamp = str(int(time.time() * 1000))
    nonce = f"{uuid.uuid4().hex[:13]}{int(time.time())}"
    raw = f"&timestamp={timestamp}&nonce={nonce}&secret={sign_key}"
    x_sign = hashlib.md5(raw.encode("utf-8")).hexdigest().upper()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Sign": x_sign,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    t0 = time.time()
    try:
        resp = session.get(CURRENT_URL, headers=headers, timeout=30, proxies=PROXIES)
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text[:300]}
        results.append(
            {
                "index": i,
                "http_status": resp.status_code,
                "code": body.get("code") if isinstance(body, dict) else None,
                "message": body.get("message") if isinstance(body, dict) else None,
                "elapsed_ms": elapsed_ms,
            }
        )
    except Exception as exc:
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        results.append({"index": i, "error": str(exc), "elapsed_ms": elapsed_ms})

ok = [r for r in results if r.get("http_status") == 200 and r.get("code") == 200]
unauth = [r for r in results if r.get("http_status") == 401 or r.get("code") == 401]
handshake = [r for r in results if "error" in r and "SSL" in r["error"]]
other = [r for r in results if r not in ok and r not in unauth and r not in handshake]

print(
    json.dumps(
        {
            "stage": "current_loop",
            "login_http_status": login_resp.status_code,
            "login_code": login_body.get("code"),
            "total": TOTAL,
            "ok_count": len(ok),
            "unauth_count": len(unauth),
            "ssl_error_count": len(handshake),
            "other_fail_count": len(other),
            "sample_failures": (unauth + handshake + other)[:8],
        },
        ensure_ascii=False,
    )
)
