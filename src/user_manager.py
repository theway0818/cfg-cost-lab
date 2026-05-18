import yaml
import bcrypt
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
PENDING_PATH = Path(__file__).parent.parent / "pending_users.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def _load_pending() -> dict:
    if not PENDING_PATH.exists():
        return {}
    with open(PENDING_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_pending(pending: dict) -> None:
    with open(PENDING_PATH, "w", encoding="utf-8") as f:
        yaml.dump(pending, f, allow_unicode=True, default_flow_style=False)


def get_allowed_domain() -> str:
    return os.environ.get("ALLOWED_DOMAIN", "ephgroup.co.kr")


def is_email_registered(email: str) -> bool:
    config = _load_config()
    users = config.get("credentials", {}).get("usernames", {})
    return any(u.get("email") == email for u in users.values())


def is_email_pending(email: str) -> bool:
    pending = _load_pending()
    return email in pending


def add_pending_user(email: str, name: str, password: str) -> None:
    """회원가입 신청 — 관리자 승인 대기 상태로 저장."""
    pending = _load_pending()
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    pending[email] = {
        "name": name,
        "password": hashed_pw,
        "requested_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    _save_pending(pending)


def get_pending_list() -> list[dict]:
    """관리자용 — 승인 대기 목록 반환."""
    pending = _load_pending()
    return [
        {"email": email, "name": info["name"], "requested_at": info["requested_at"]}
        for email, info in pending.items()
    ]


def approve_user(email: str) -> str:
    """관리자 승인 — pending → config.yaml 이동."""
    pending = _load_pending()
    if email not in pending:
        return "해당 신청자를 찾을 수 없습니다."

    entry = pending[email]
    config = _load_config()

    # 아이디: 이메일 @ 앞부분, 중복 시 숫자 붙임
    username = email.split("@")[0].replace(".", "_")
    existing = config["credentials"]["usernames"]
    base, i = username, 2
    while username in existing:
        username = f"{base}{i}"
        i += 1

    config["credentials"]["usernames"][username] = {
        "email": email,
        "name": entry["name"],
        "password": entry["password"],
    }
    _save_config(config)

    del pending[email]
    _save_pending(pending)
    return username


def reject_user(email: str) -> None:
    """관리자 거절 — pending에서 삭제."""
    pending = _load_pending()
    if email in pending:
        del pending[email]
        _save_pending(pending)
