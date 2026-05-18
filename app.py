import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from src.email_sender import generate_code, send_verification_email
from src.user_manager import (
    get_allowed_domain,
    is_email_registered,
    is_email_pending,
    add_pending_user,
    verify_and_activate,
)

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

# ── 로그인 / 회원가입 / 인증 탭 ──────────────────────────────
if not st.session_state.get("authentication_status"):

    st.markdown(
        "<h1 style='text-align:center;margin-top:40px;'>📊 CFG Cost Lab</h1>"
        "<p style='text-align:center;color:gray;margin-bottom:32px;'>"
        "카페게이트 구매물류팀 전용 원가율 진단·시뮬레이션 도구</p>",
        unsafe_allow_html=True,
    )

    tab_login, tab_register, tab_verify = st.tabs(["🔑 로그인", "📝 회원가입", "✉️ 이메일 인증"])

    # ── 로그인 탭 ────────────────────────────────────────────
    with tab_login:
        authenticator.login(location="main")
        if st.session_state.get("authentication_status") is False:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    # ── 회원가입 탭 ──────────────────────────────────────────
    with tab_register:
        allowed_domain = get_allowed_domain()
        st.markdown(f"**회사 이메일(@{allowed_domain})** 로만 가입할 수 있습니다.")
        st.markdown("---")

        with st.form("register_form"):
            reg_name = st.text_input("이름", placeholder="홍길동")
            reg_email = st.text_input(
                "회사 이메일",
                placeholder=f"example@{allowed_domain}",
            )
            reg_pw = st.text_input("비밀번호 (8자 이상)", type="password")
            reg_pw2 = st.text_input("비밀번호 확인", type="password")
            submitted = st.form_submit_button("인증 코드 받기", use_container_width=True, type="primary")

        if submitted:
            error = None
            if not reg_name.strip():
                error = "이름을 입력해 주세요."
            elif not reg_email.strip().endswith(f"@{allowed_domain}"):
                error = f"회사 이메일(@{allowed_domain})만 가입 가능합니다."
            elif len(reg_pw) < 8:
                error = "비밀번호는 8자 이상이어야 합니다."
            elif reg_pw != reg_pw2:
                error = "비밀번호가 일치하지 않습니다."
            elif is_email_registered(reg_email.strip()):
                error = "이미 가입된 이메일입니다. 로그인 탭에서 로그인해 주세요."

            if error:
                st.error(error)
            else:
                code = generate_code()
                try:
                    send_verification_email(reg_email.strip(), reg_name.strip(), code)
                    add_pending_user(reg_email.strip(), reg_name.strip(), reg_pw, code)
                    st.success(
                        f"**{reg_email.strip()}** 으로 인증 코드를 발송했습니다.  \n"
                        "받은편지함을 확인하고 **'이메일 인증' 탭**에서 코드를 입력해 주세요."
                    )
                    st.info("스팸 메일함도 확인해 보세요.")
                except EnvironmentError as e:
                    st.error(f"이메일 발송 설정 오류: {e}")
                except Exception as e:
                    st.error(f"이메일 발송 실패: {e}  \n관리자에게 문의해 주세요.")

    # ── 이메일 인증 탭 ────────────────────────────────────────
    with tab_verify:
        st.markdown("회원가입 후 이메일로 받은 **6자리 인증 코드**를 입력해 주세요.")
        st.markdown("---")

        with st.form("verify_form"):
            verify_email = st.text_input("가입 시 입력한 이메일")
            verify_code = st.text_input("인증 코드 (6자리)", max_chars=6, placeholder="123456")
            verify_submitted = st.form_submit_button("인증 완료", use_container_width=True, type="primary")

        if verify_submitted:
            if not verify_email.strip() or not verify_code.strip():
                st.error("이메일과 인증 코드를 모두 입력해 주세요.")
            else:
                success, message = verify_and_activate(verify_email.strip(), verify_code.strip())
                if success:
                    st.success(f"✅ {message}")
                    st.info("이제 **로그인 탭**에서 회사 이메일 아이디로 로그인하세요.")
                    st.balloons()
                else:
                    st.error(message)

    st.stop()

# ── 로그인 성공 — 메인 대시보드 ──────────────────────────────
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
    st.markdown("엑셀 업로드 → 매입·역매입 원가율 자동 계산. 80% 초과 비정상 품목 자동 표시.")
with col_b:
    st.markdown("#### 🎯 2. 핵심품목 20·80")
    st.markdown("매출액 기준 상위 80% 핵심품목 자동 추출. 카테고리별 파레토 차트.")
with col_c:
    st.markdown("#### 💹 3. 판가 시뮬레이터")
    st.markdown("매입단가·물류비 조정 시 목표 원가율 달성 여부 시뮬레이션.")

col_d, col_e = st.columns(2)
with col_d:
    st.markdown("#### 🔄 4. 유통구조 비교")
    st.markdown("수수료 유통 vs 직매입 원가율 비교. 월 절감 예상액 자동 계산.")
with col_e:
    st.markdown("#### 🆕 5. 신메뉴 BEP")
    st.markdown("원재료 입력 → 원가율 + BEP 수량 계산. 손익분기점 차트 제공.")

st.markdown("---")
st.caption("데이터는 사내 PC에만 저장됩니다. 외부 서버로 전송되지 않습니다.")
