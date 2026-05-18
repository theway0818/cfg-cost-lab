import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

if not st.session_state.get("authentication_status"):
    st.warning("로그인이 필요합니다. 홈 화면에서 로그인해 주세요.")
    st.stop()

sys.path.append(str(Path(__file__).parent.parent))
from src.loaders import load_excel, load_sample
from src.cost_analyzer import calc_cost_rates, get_summary, to_excel_bytes

st.set_page_config(page_title="품목별 원가율", page_icon="📋", layout="wide")

with st.sidebar:
    st.title("📊 CFG Cost Lab")
    st.markdown("---")
    st.markdown("**카페게이트 구매물류팀**")
    st.caption("⚠️ 사내 전용 — 외부 공유 금지")

st.title("📋 품목별 원가율 전수조사")
st.markdown("엑셀 파일을 업로드하면 품목별 매입 원가율과 역매입 원가율을 자동으로 계산합니다.")

# ── 데이터 로드 ──────────────────────────────────────────────
col_upload, col_sample = st.columns([3, 1])
with col_upload:
    uploaded = st.file_uploader("엑셀 파일 업로드 (.xlsx)", type=["xlsx"])
with col_sample:
    use_sample = st.checkbox("샘플 데이터로 먼저 보기", value=True if not uploaded else False)

df_raw = None
if uploaded:
    try:
        df_raw = load_excel(uploaded)
        st.success(f"파일 로드 완료 — {len(df_raw)}개 품목")
    except ValueError as e:
        st.error(f"파일 오류: {e}")
        st.info("필수 컬럼: 품목명, 카테고리, 매입단가, 역매입단가, 판매단가, 월매출수량")
        st.stop()
elif use_sample:
    df_raw = load_sample()
    st.info("샘플 데이터(익명화)를 표시합니다. 실제 엑셀을 업로드하면 교체됩니다.")

if df_raw is None:
    st.stop()

df = calc_cost_rates(df_raw)

# ── 요약 지표 ────────────────────────────────────────────────
summary = get_summary(df)
st.markdown("---")
st.markdown("### 전체 요약")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("전체 품목 수", f"{summary['전체_품목수']}개")
m2.metric(
    "평균 매입원가율",
    f"{summary['평균_매입원가율']}%",
    delta=f"{summary['평균_매입원가율'] - 65:.1f}%p (목표 65%)",
    delta_color="inverse",
)
m3.metric(
    "평균 역매입원가율",
    f"{summary['평균_역매입원가율']}%",
    delta=f"{summary['평균_역매입원가율'] - 65:.1f}%p (목표 65%)",
    delta_color="inverse",
)
m4.metric("비정상 품목 (매입)", f"{summary['비정상_품목수_매입']}개", delta_color="off")
m5.metric("비정상 품목 (역매입)", f"{summary['비정상_품목수_역매입']}개", delta_color="off")

# ── 비정상 임계값 설정 ────────────────────────────────────────
st.markdown("---")
threshold = st.slider(
    "비정상 판단 기준 원가율 (%)",
    min_value=50, max_value=100, value=80, step=1,
    help="이 값보다 높은 원가율을 가진 품목을 비정상으로 표시합니다.",
)
df["매입_비정상"] = df["매입원가율"] > threshold
df["역매입_비정상"] = df["역매입원가율"] > threshold

# ── 필터 ────────────────────────────────────────────────────
col_f1, col_f2 = st.columns(2)
with col_f1:
    categories = ["전체"] + sorted(df["카테고리"].unique().tolist())
    selected_cat = st.selectbox("카테고리 필터", categories)
with col_f2:
    show_abnormal = st.checkbox("비정상 품목만 보기", value=False)

df_view = df.copy()
if selected_cat != "전체":
    df_view = df_view[df_view["카테고리"] == selected_cat]
if show_abnormal:
    df_view = df_view[df_view["매입_비정상"] | df_view["역매입_비정상"]]

# ── 결과 테이블 ──────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### 품목별 원가율 ({len(df_view)}개)")

display_cols = ["품목명", "카테고리", "매입단가", "역매입단가", "판매단가",
                "매입원가율", "역매입원가율", "매입_비정상", "역매입_비정상", "월매출액"]

def highlight_abnormal(row):
    styles = [""] * len(row)
    cols = row.index.tolist()
    if row.get("매입_비정상", False):
        idx = cols.index("매입원가율") if "매입원가율" in cols else -1
        if idx >= 0:
            styles[idx] = "background-color: #ffe0e0"
    if row.get("역매입_비정상", False):
        idx = cols.index("역매입원가율") if "역매입원가율" in cols else -1
        if idx >= 0:
            styles[idx] = "background-color: #ffe0e0"
    return styles

st.dataframe(
    df_view[display_cols].style.apply(highlight_abnormal, axis=1),
    use_container_width=True,
    height=400,
)

# ── 차트 ────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 원가율 시각화")

tab1, tab2 = st.tabs(["매입 원가율 분포", "매입 vs 역매입 비교"])

with tab1:
    fig = px.bar(
        df_view.sort_values("매입원가율", ascending=False),
        x="품목명", y="매입원가율",
        color="카테고리",
        text="매입원가율",
        title="품목별 매입 원가율",
    )
    fig.add_hline(y=65, line_dash="dash", line_color="green", annotation_text="목표 65%")
    fig.add_hline(y=threshold, line_dash="dash", line_color="red",
                  annotation_text=f"비정상 기준 {threshold}%")
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(xaxis_tickangle=-45, height=450)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    df_melt = df_view.melt(
        id_vars=["품목명", "카테고리"],
        value_vars=["매입원가율", "역매입원가율"],
        var_name="구분", value_name="원가율",
    )
    fig2 = px.bar(
        df_melt,
        x="품목명", y="원가율",
        color="구분", barmode="group",
        title="매입 원가율 vs 역매입 원가율 비교",
    )
    fig2.add_hline(y=65, line_dash="dash", line_color="green", annotation_text="목표 65%")
    fig2.update_layout(xaxis_tickangle=-45, height=450)
    st.plotly_chart(fig2, use_container_width=True)

# ── 다운로드 ─────────────────────────────────────────────────
st.markdown("---")
col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    st.download_button(
        "📥 엑셀 다운로드",
        data=to_excel_bytes(df_view[display_cols]),
        file_name="원가율분석결과.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
with col_dl2:
    st.download_button(
        "📥 CSV 다운로드",
        data=df_view[display_cols].to_csv(index=False, encoding="utf-8-sig"),
        file_name="원가율분석결과.csv",
        mime="text/csv",
    )
