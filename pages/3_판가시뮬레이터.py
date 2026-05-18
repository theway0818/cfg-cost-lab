import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.loaders import load_excel, load_sample
from src.cost_analyzer import calc_cost_rates
from src.simulator import TARGET_COST_RATE, calc_target_price

st.set_page_config(page_title="판가 시뮬레이터", page_icon="💹", layout="wide")

with st.sidebar:
    st.title("📊 CFG Cost Lab")
    st.markdown("---")
    st.markdown("**카페게이트 구매물류팀**")
    st.caption("⚠️ 사내 전용 — 외부 공유 금지")

st.title("💹 점주 판가 가이드라인 시뮬레이터")
st.markdown("매입단가·물류비를 조정하면 목표 원가율 달성에 필요한 판매가가 자동으로 계산됩니다.")

# ── 데이터 로드 ──────────────────────────────────────────────
col_upload, col_sample = st.columns([3, 1])
with col_upload:
    uploaded = st.file_uploader("엑셀 파일 업로드 (.xlsx)", type=["xlsx"])
with col_sample:
    use_sample = st.checkbox("샘플 데이터 사용", value=True if not uploaded else False)

df_raw = None
if uploaded:
    try:
        df_raw = load_excel(uploaded)
    except ValueError as e:
        st.error(f"파일 오류: {e}")
        st.stop()
elif use_sample:
    df_raw = load_sample()
    st.info("샘플 데이터(익명화)를 표시합니다.")

if df_raw is None:
    st.stop()

df = calc_cost_rates(df_raw)

# ── 시뮬레이션 변수 설정 ─────────────────────────────────────
st.markdown("---")
st.markdown("### 시뮬레이션 변수 설정")

col1, col2, col3 = st.columns(3)

with col1:
    target_rate = st.number_input(
        "목표 원가율 (%)",
        min_value=40.0, max_value=90.0,
        value=TARGET_COST_RATE, step=0.5,
        help="달성하고자 하는 매출원가율 목표값입니다.",
    )

with col2:
    purchase_change = st.slider(
        "매입단가 변동 (%)",
        min_value=-30, max_value=30, value=0, step=1,
        help="협력업체와 협상을 통해 매입단가를 몇 % 조정할지 설정합니다.",
    )

with col3:
    logistics_cost_pct = st.slider(
        "물류비 추가 비율 (%)",
        min_value=0, max_value=20, value=0, step=1,
        help="판매단가 대비 물류비가 차지하는 비율입니다.",
    )

# ── 시뮬레이션 계산 ──────────────────────────────────────────
df_sim = df.copy()
df_sim["시뮬_매입단가"] = (df_sim["매입단가"] * (1 + purchase_change / 100)).round(0)
df_sim["물류비"] = (df_sim["판매단가"] * logistics_cost_pct / 100).round(0)
df_sim["시뮬_총원가"] = df_sim["시뮬_매입단가"] + df_sim["물류비"]
df_sim["시뮬_원가율"] = (df_sim["시뮬_총원가"] / df_sim["판매단가"] * 100).round(1)
df_sim["목표달성_필요판가"] = (df_sim["시뮬_총원가"] / (target_rate / 100)).round(0)
df_sim["현재대비_판가변동"] = df_sim["목표달성_필요판가"] - df_sim["판매단가"]
df_sim["목표달성여부"] = df_sim["시뮬_원가율"] <= target_rate

# ── 요약 지표 ────────────────────────────────────────────────
st.markdown("---")
total_revenue = (df_sim["판매단가"] * df_sim["월매출수량"]).sum()
total_sim_cost = (df_sim["시뮬_총원가"] * df_sim["월매출수량"]).sum()
sim_avg_rate = total_sim_cost / total_revenue * 100
achieved = df_sim["목표달성여부"].sum()

m1, m2, m3, m4 = st.columns(4)
m1.metric("현재 평균 매입원가율", f"{df['매입원가율'].mean():.1f}%")
m2.metric(
    "시뮬레이션 평균 원가율",
    f"{sim_avg_rate:.1f}%",
    delta=f"{sim_avg_rate - df['매입원가율'].mean():.1f}%p",
    delta_color="inverse",
)
m3.metric("목표 원가율", f"{target_rate}%")
m4.metric(
    "목표 달성 품목",
    f"{achieved}개 / {len(df_sim)}개",
    delta_color="off",
)

# ── 결과 테이블 ──────────────────────────────────────────────
st.markdown("---")
st.markdown("### 품목별 시뮬레이션 결과")

cat_filter = st.selectbox(
    "카테고리 필터",
    ["전체"] + sorted(df_sim["카테고리"].unique().tolist()),
)
df_view = df_sim if cat_filter == "전체" else df_sim[df_sim["카테고리"] == cat_filter]

display_cols = [
    "품목명", "카테고리", "판매단가",
    "매입단가", "시뮬_매입단가",
    "물류비", "시뮬_원가율",
    "목표달성_필요판가", "현재대비_판가변동", "목표달성여부",
]

def color_achieved(row):
    color = "#e8f5e9" if row["목표달성여부"] else "#ffebee"
    return [f"background-color: {color}"] * len(row)

st.dataframe(
    df_view[display_cols].style.apply(color_achieved, axis=1),
    use_container_width=True,
    height=400,
)

# ── 비교 차트 ────────────────────────────────────────────────
st.markdown("---")
tab1, tab2 = st.tabs(["원가율 비교", "필요 판가 변동"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="현재 매입원가율",
        x=df_view["품목명"],
        y=df_view["매입원가율"],
        marker_color="#90CAF9",
    ))
    fig.add_trace(go.Bar(
        name="시뮬레이션 원가율",
        x=df_view["품목명"],
        y=df_view["시뮬_원가율"],
        marker_color="#1976D2",
    ))
    fig.add_hline(y=target_rate, line_dash="dash", line_color="green",
                  annotation_text=f"목표 {target_rate}%")
    fig.update_layout(
        barmode="group", xaxis_tickangle=-45, height=420,
        title="현재 vs 시뮬레이션 원가율 비교",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    colors = ["#43A047" if v <= 0 else "#E53935" for v in df_view["현재대비_판가변동"]]
    fig2 = go.Figure(go.Bar(
        x=df_view["품목명"],
        y=df_view["현재대비_판가변동"],
        marker_color=colors,
        text=df_view["현재대비_판가변동"].apply(lambda x: f"+{int(x):,}" if x > 0 else f"{int(x):,}"),
        textposition="outside",
    ))
    fig2.add_hline(y=0, line_color="gray")
    fig2.update_layout(
        title="목표 달성을 위한 판가 변동 필요액 (원)",
        xaxis_tickangle=-45, height=420,
    )
    st.caption("녹색: 현재 판가로도 목표 달성 | 빨간색: 판가 인상 필요")
    st.plotly_chart(fig2, use_container_width=True)
