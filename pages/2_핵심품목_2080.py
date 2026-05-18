import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.loaders import load_excel, load_sample
from src.cost_analyzer import calc_cost_rates, to_excel_bytes
from src.pareto import calc_pareto, get_category_summary

st.set_page_config(page_title="핵심품목 20·80", page_icon="🎯", layout="wide")

with st.sidebar:
    st.title("📊 CFG Cost Lab")
    st.markdown("---")
    st.markdown("**카페게이트 구매물류팀**")
    st.caption("⚠️ 사내 전용 — 외부 공유 금지")

st.title("🎯 핵심품목 20·80 분석")
st.markdown("매출액 기준으로 상위 80%를 차지하는 핵심 품목을 자동으로 추출합니다.")

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
        st.stop()
elif use_sample:
    df_raw = load_sample()
    st.info("샘플 데이터(익명화)를 표시합니다.")

if df_raw is None:
    st.stop()

df = calc_cost_rates(df_raw)

# ── 파레토 기준 설정 ──────────────────────────────────────────
top_pct = st.slider(
    "핵심품목 기준 누적 매출 비중 (%)",
    min_value=50, max_value=95, value=80, step=5,
    help="상위 몇 % 매출을 담당하는 품목을 핵심품목으로 볼지 설정합니다.",
)

df_pareto = calc_pareto(df, top_pct=top_pct / 100)
df_core = df_pareto[df_pareto["핵심품목"]]
df_non = df_pareto[~df_pareto["핵심품목"]]

# ── 요약 지표 ────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 파레토 요약")

m1, m2, m3, m4 = st.columns(4)
m1.metric("전체 품목 수", f"{len(df_pareto)}개")
m2.metric("핵심품목 수", f"{len(df_core)}개",
          delta=f"전체의 {len(df_core)/len(df_pareto)*100:.0f}%", delta_color="off")
m3.metric("핵심품목 매출 비중", f"{df_core['매출비중(%)'].sum():.1f}%")
m4.metric("핵심품목 평균 매입원가율", f"{df_core['매입원가율'].mean():.1f}%")

# ── 파레토 차트 ──────────────────────────────────────────────
st.markdown("---")
st.markdown("### 파레토 차트")

fig = go.Figure()

colors = ["#2196F3" if h else "#BBDEFB" for h in df_pareto["핵심품목"]]

fig.add_trace(go.Bar(
    x=df_pareto["품목명"],
    y=df_pareto["매출비중(%)"],
    name="매출 비중",
    marker_color=colors,
    text=df_pareto["매출비중(%)"].apply(lambda x: f"{x:.1f}%"),
    textposition="outside",
))

fig.add_trace(go.Scatter(
    x=df_pareto["품목명"],
    y=df_pareto["누적비중(%)"],
    name="누적 비중",
    yaxis="y2",
    line=dict(color="#FF5722", width=2),
    mode="lines+markers",
))

fig.add_hline(
    y=top_pct, yref="y2",
    line_dash="dash", line_color="green",
    annotation_text=f"기준 {top_pct}%",
)

fig.update_layout(
    title="품목별 매출 비중 및 누적 비중",
    xaxis_tickangle=-45,
    yaxis=dict(title="매출 비중 (%)"),
    yaxis2=dict(title="누적 비중 (%)", overlaying="y", side="right", range=[0, 105]),
    legend=dict(orientation="h", y=1.1),
    height=500,
    bargap=0.2,
)

st.plotly_chart(fig, use_container_width=True)
st.caption("■ 진파랑: 핵심품목 | □ 연파랑: 일반품목")

# ── 카테고리별 분석 ──────────────────────────────────────────
st.markdown("---")
st.markdown("### 카테고리별 현황")

cat_summary = get_category_summary(df_pareto)

col_tbl, col_chart = st.columns([1, 1])

with col_tbl:
    st.dataframe(
        cat_summary.rename(columns={
            "카테고리": "카테고리",
            "품목수": "품목 수",
            "월매출액합계": "월매출액 합계",
            "평균_매입원가율": "평균 매입원가율(%)",
            "평균_역매입원가율": "평균 역매입원가율(%)",
        }),
        use_container_width=True,
        hide_index=True,
    )

with col_chart:
    fig_cat = px.pie(
        cat_summary,
        names="카테고리",
        values="월매출액합계",
        title="카테고리별 매출 비중",
        hole=0.4,
    )
    st.plotly_chart(fig_cat, use_container_width=True)

# ── 핵심품목 리스트 ──────────────────────────────────────────
st.markdown("---")
st.markdown(f"### 핵심품목 목록 ({len(df_core)}개)")

display_cols = ["순위", "품목명", "카테고리", "매출비중(%)", "누적비중(%)",
                "매입원가율", "역매입원가율", "월매출액"]

st.dataframe(
    df_core[display_cols].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
)

# ── 다운로드 ─────────────────────────────────────────────────
st.markdown("---")
col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    st.download_button(
        "📥 핵심품목 엑셀 다운로드",
        data=to_excel_bytes(df_core[display_cols].reset_index(drop=True)),
        file_name="핵심품목_2080분석.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
with col_dl2:
    st.download_button(
        "📥 전체 파레토 CSV",
        data=df_pareto[display_cols].to_csv(index=False, encoding="utf-8-sig"),
        file_name="파레토분석_전체.csv",
        mime="text/csv",
    )
