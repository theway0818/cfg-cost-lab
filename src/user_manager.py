import yaml
import bcrypt
import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
PENDING_PATH = Path(__file__).parent.parent / "pending_users.yaml"
CODE_EXPIRY_MINUTES = 10


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
    return os.environ.get("ALLOWED_DOMAIN", "cafegate.co.kr")


def is_email_registered(email: str) -> bool:
    config = _load_config()
    users = config.get("credentials", {}).get("usernames", {})
    return any(u.get("email") == email for u in users.values())


def is_email_pending(email: str) -> bool:
    pending = _load_pending()
    return email in pending


def add_pending_user(email: str, name: str, password: str, code: str) -> None:
    pending = _load_pending()
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    pending[email] = {
        "name": name,
        "password": hashed_pw,
        "code": code,
        "expires_at": (datetime.now() + timedelta(minutes=CODE_EXPIRY_MINUTES)).isoformat(),
    }
    _save_pending(pending)


def verify_and_activate(email: str, code: str) -> tuple[bool, str]:
    """인증 코드 확인 후 계정 활성화. (성공여부, 메시지) 반환."""
    pending = _load_pending()

    if email not in pending:
        return False, "인증 요청 정보가 없습니다. 다시 회원가입을 시도해 주세요."

    entry = pending[email]
    expires_at = datetime.fromisoformat(entry["expires_at"])

    if datetime.now() > expires_at:
        del pending[email]
        _save_pending(pending)
        return False, f"인증 코드가 만료되었습니다 ({CODE_EXPIRY_MINUTES}분 초과). 다시 회원가입을 시도해 주세요."

    if entry["code"] != code.strip():
        return False, "인증 코드가 올바르지 않습니다."

    # 계정 활성화
    config = _load_config()
    username = email.split("@")[0].replace(".", "_")
    # 중복 username 처리
    existing = config["credentials"]["usernames"]
    base = username
    i = 2
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

    return True, f"회원가입이 완료되었습니다. 아이디: {username}"
