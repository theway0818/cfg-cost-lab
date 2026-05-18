import streamlit as st

st.set_page_config(
    page_title="CFG Cost Lab",
    page_icon="📊",
    layout="wide",
)

# 사이드바
with st.sidebar:
    st.title("📊 CFG Cost Lab")
    st.markdown("---")
    st.markdown("**카페게이트 구매물류팀**")
    st.markdown("원가율 진단·시뮬레이션 도구")
    st.markdown("---")
    st.caption("⚠️ 사내 전용 — 외부 공유 금지")

# 메인 화면
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

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("#### 📋 1. 품목별 원가율")
    st.markdown(
        "엑셀 파일을 업로드하면 품목별 매입 원가율과 "
        "역매입 원가율을 자동으로 계산합니다.  \n"
        "80% 초과 비정상 품목은 자동으로 표시됩니다."
    )

with col_b:
    st.markdown("#### 🎯 2. 핵심품목 20·80 분석")
    st.markdown(
        "매출액 기준으로 상위 80%를 차지하는 핵심 품목을 "
        "자동으로 추출합니다.  \n"
        "카테고리별 파레토 차트를 제공합니다."
    )

st.markdown("---")
st.caption("Phase 1 MVP | 데이터는 사내 PC에만 저장됩니다.")
