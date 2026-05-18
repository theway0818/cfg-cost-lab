import smtplib
import os
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def send_verification_email(to_email: str, name: str, code: str) -> None:
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")

    if not smtp_user or not smtp_password:
        raise EnvironmentError("SMTP 설정이 .env 파일에 없습니다. .env.example을 참고해 .env를 만들어 주세요.")

    msg = MIMEMultipart("alternative")
    msg["From"] = f"CFG Cost Lab <{smtp_user}>"
    msg["To"] = to_email
    msg["Subject"] = "[CFG Cost Lab] 이메일 인증 코드"

    plain = f"""안녕하세요, {name}님.

CFG Cost Lab 회원가입 이메일 인증 코드를 안내드립니다.

인증 코드: {code}

이 코드는 10분간 유효합니다.
본인이 요청하지 않으셨다면 이 메일을 무시하세요.

CFG Cost Lab 팀 드림
"""

    html = f"""
<div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px;border:1px solid #e0e0e0;border-radius:8px;">
  <h2 style="color:#1976D2;">📊 CFG Cost Lab</h2>
  <p>안녕하세요, <strong>{name}</strong>님.</p>
  <p>아래 인증 코드를 앱에 입력해 회원가입을 완료해 주세요.</p>
  <div style="background:#F5F7FA;border-radius:8px;padding:24px;text-align:center;margin:24px 0;">
    <span style="font-size:36px;font-weight:bold;letter-spacing:12px;color:#1976D2;">{code}</span>
  </div>
  <p style="color:#888;font-size:13px;">⏱ 이 코드는 <strong>10분간</strong> 유효합니다.</p>
  <p style="color:#888;font-size:13px;">본인이 요청하지 않으셨다면 이 메일을 무시하세요.</p>
  <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
  <p style="color:#bbb;font-size:12px;">CFG Cost Lab — 카페게이트 구매물류팀 전용</p>
</div>
"""

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
