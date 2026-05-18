import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.user_manager import get_pending_list, approve_user, reject_user

st.set_page_config(page_title="회원 관리", page_icon="👤", layout="wide")

# ── 로그인 체크 ───────────────────────────────────────────────
if not st.session_state.get("authentication_status"):
    st.warning("로그인이 필요합니다.")
    st.stop()

# ── 관리자 권한 체크 ──────────────────────────────────────────
if st.session_state.get("username") != "admin":
    st.error("관리자만 접근할 수 있는 페이지입니다.")
    st.stop()

with st.sidebar:
    st.title("📊 CFG Cost Lab")
    st.markdown("---")
    st.markdown(f"**{st.session_state.get('name', '')}** 님")
    st.caption("⚠️ 사내 전용 — 외부 공유 금지")

st.title("👤 회원 관리")
st.markdown("가입 신청자를 승인하거나 거절합니다.")
st.markdown("---")

# ── 승인 대기 목록 ─────────────────────────────────────────
pending = get_pending_list()

if not pending:
    st.success("현재 승인 대기 중인 신청자가 없습니다.")
else:
    st.markdown(f"### 승인 대기 중 — {len(pending)}명")

    for p in pending:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            col1.markdown(f"**이름**  \n{p['name']}")
            col2.markdown(f"**이메일**  \n{p['email']}")
            col3.markdown(f"**신청일시**  \n{p['requested_at']}")

            with col4:
                col_approve, col_reject = st.columns(2)
                if col_approve.button("✅ 승인", key=f"approve_{p['email']}", use_container_width=True, type="primary"):
                    username = approve_user(p["email"])
                    st.success(f"**{p['name']}**님 승인 완료! 아이디: `{username}`")
                    st.rerun()
                if col_reject.button("❌ 거절", key=f"reject_{p['email']}", use_container_width=True):
                    reject_user(p["email"])
                    st.warning(f"**{p['name']}**님 신청을 거절했습니다.")
                    st.rerun()
