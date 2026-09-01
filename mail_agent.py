"""
JSA 자금계획 - 사내 PC 메일 발송 프로그램 (에이전트)

동작:
  - 웹앱(Railway)의 발송 대기열을 주기적으로 조회한다.
  - 대기 중인 메일을 이 PC에서 회사 메일서버(mail.icams.co.kr)로 발송한다.
  - 발송 결과(성공/실패)를 웹앱에 다시 기록한다.

전제:
  - 이 PC가 사내망에 있어 mail.icams.co.kr 로 메일 발송이 가능해야 한다.
  - 웹앱(Railway)에 MAIL_AGENT_TOKEN 환경변수가 설정되어 있고, 아래 TOKEN 과 동일해야 한다.

실행:
  python mail_agent.py
  (계속 켜 두면 됩니다. Ctrl+C 로 종료)

설정: 아래 값을 채우거나 환경변수로 지정하세요.
"""
import json
import os
import smtplib
import time
import urllib.parse
import urllib.request
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

# ===== 설정 (환경변수 우선, 없으면 아래 기본값 사용) =====
BASE_URL = os.environ.get("JSA_BASE_URL", "https://jsa-production-6ccc.up.railway.app")
TOKEN = os.environ.get("MAIL_AGENT_TOKEN", "여기에_웹앱과_동일한_토큰_입력")

SMTP_HOST = os.environ.get("SMTP_HOST", "mail.icams.co.kr")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "25"))
SMTP_USER = os.environ.get("SMTP_USER", "cams@icams.co.kr")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "여기에_메일_비밀번호_입력")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "0") == "1"
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USER)

POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "15"))
# =====================================================


def _get_pending():
    url = f"{BASE_URL}/mail/outbox/pending?token={urllib.parse.quote(TOKEN)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data.get("jobs", [])


def _report(job_id, status, error=""):
    url = f"{BASE_URL}/mail/outbox/{job_id}/done?token={urllib.parse.quote(TOKEN)}"
    body = urllib.parse.urlencode({"status": status, "error": error[:500]}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()


def _open_smtp():
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
    if SMTP_USE_TLS:
        server.starttls()
    if SMTP_PASSWORD and SMTP_PASSWORD != "여기에_메일_비밀번호_입력":
        server.login(SMTP_USER, SMTP_PASSWORD)
    return server


def _send_batch(jobs):
    server = None
    try:
        server = _open_smtp()
    except Exception as e:  # noqa: BLE001
        print(f"[SMTP 연결 실패] {e}  (다음 주기에 재시도)")
        return
    try:
        for job in jobs:
            job_id = job["id"]
            recipients = [a.strip() for a in (job.get("recipients") or "").split(",") if a.strip()]
            if not recipients:
                _report(job_id, "failed", "수신자 없음")
                continue
            msg = MIMEText(job.get("body") or "", _charset="utf-8")
            msg["Subject"] = job.get("subject") or ""
            msg["From"] = FROM_EMAIL
            msg["To"] = ", ".join(recipients)
            # 정상 메일 헤더 (스팸/위조 오탐 방지)
            msg["Date"] = formatdate(localtime=True)
            _dom = FROM_EMAIL.split("@", 1)[1] if "@" in FROM_EMAIL else None
            msg["Message-ID"] = make_msgid(domain=_dom)
            try:
                server.sendmail(FROM_EMAIL, recipients, msg.as_string())
                _report(job_id, "sent")
                print(f"[발송완료] #{job_id} -> {', '.join(recipients)}")
            except Exception as e:  # noqa: BLE001
                _report(job_id, "failed", str(e))
                print(f"[발송실패] #{job_id}: {e}")
    finally:
        try:
            server.quit()
        except Exception:  # noqa: BLE001
            pass


def main():
    print(f"JSA 메일 발송 프로그램 시작. 대상: {BASE_URL}  (SMTP: {SMTP_HOST}:{SMTP_PORT})")
    print(f"{POLL_SECONDS}초마다 대기열 확인. 종료하려면 Ctrl+C.")
    while True:
        try:
            jobs = _get_pending()
            if jobs:
                print(f"대기 메일 {len(jobs)}건 발견 -> 발송 시작")
                _send_batch(jobs)
        except Exception as e:  # noqa: BLE001
            print(f"[오류] {e}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
