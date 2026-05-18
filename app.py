import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from pathlib import Path

st.set_page_config(
    page_title="CFG Cost Lab",
    page_icon="📊",
    layout="wide",
)

# ── 인증 설정 로드 ────────────────────────────────────────────
config_path = Path(__file__).parent / "config.yaml"
with open(config_path, encoding="utf-8") as f:
    config = yaml.load(f, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

# ── 로그인 화면 ──────────────────────────────────────────────
authenticator.login(location="main")

if st.session_state.get("authentication_status") is False:
    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
    st.stop()

elif st.session_state.get("authentication_status") is None:
    st.markdown(
        "<h1 style='text-align:center; margin-top:80px;'>📊 CFG Cost Lab</h1>"
        "<p style='text-align:center; color:gray;'>카페게이트 구매물류팀 전용 · 사내 사용자만 접근 가능</p>",
        unsafe_allow_html=True,
    )
    st.stop()

# ── 로그인 성공 후 메인 화면 ──────────────────────────────────
name = st.session_state.get("name", "")

with st.sidebar:
    st.title("📊 CFG Cost Lab")
    st.markdown("---")
    st.markdown(f"**{name}** 님")
    st.markdown("카페게이트 구매물류팀")
    st.markdown("---")
    authenticator.logout("로그아웃", location="sidebar")
    st.caption("⚠️ 사내 전용 — 외부 공유 금지")

st.title("📊 CFG Cost Lab")
st.subheader("카페게이트 원가율 진단·시뮬레이션 도구")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 목표")
    st.info("매출원가율 **70%대 → 65%** 인하")

with col2:
    st.markdown("### 분석 축")
    st.info("협력업체 매입가 vs CJ 역매입가")

st.markdown("---")
st.markdown("### 메뉴")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("#### 📋 1. 품목별 원가율")
    st.markdown(
        "엑셀 업로드 → 매입·역매입 원가율 자동 계산.  \n"
        "80% 초과 비정상 품목 자동 표시."
    )

with col_b:
    st.markdown("#### 🎯 2. 핵심품목 20·80")
    st.markdown(
        "매출액 기준 상위 80% 핵심품목 자동 추출.  \n"
        "카테고리별 파레토 차트."
    )

with col_c:
    st.markdown("#### 💹 3. 판가 시뮬레이터")
    st.markdown(
        "매입단가·물류비 조정 시  \n"
        "목표 원가율 달성 여부 시뮬레이션."
    )

col_d, col_e = st.columns(2)

with col_d:
    st.markdown("#### 🔄 4. 유통구조 비교")
    st.markdown(
        "수수료 유통 vs 직매입 원가율 비교.  \n"
        "월 절감 예상액 자동 계산."
    )

with col_e:
    st.markdown("#### 🆕 5. 신메뉴 BEP")
    st.markdown(
        "원재료 입력 → 원가율 + BEP 수량 계산.  \n"
        "손익분기점 차트 제공."
    )

st.markdown("---")
st.caption("데이터는 사내 PC에만 저장됩니다. 외부 서버로 전송되지 않습니다.")
