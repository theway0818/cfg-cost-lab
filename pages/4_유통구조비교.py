import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.loaders import load_excel, load_sample
from src.cost_analyzer import calc_cost_rates

st.set_page_config(page_title="유통구조 비교", page_icon="🔄", layout="wide")

with st.sidebar:
    st.title("📊 CFG Cost Lab")
    st.markdown("---")
    st.markdown("**카페게이트 구매물류팀**")
    st.caption("⚠️ 사내 전용 — 외부 공유 금지")

st.title("🔄 유통구조 재설계 비교")
st.markdown(
    "**수수료 유통(현행)** vs **직매입** 두 구조의 원가를 비교하여 "
    "구조 전환 시 이익 개선 효과를 시뮬레이션합니다."
)

with st.expander("유통구조란? (클릭해서 확인)"):
    st.markdown("""
| 구조 | 설명 | 특징 |
|------|------|------|
| **수수료 유통 (현행)** | CJ가 협력업체로부터 상품을 사서 카페게이트에 역매입 | CJ 마진 포함 → 원가 높음 |
| **직매입** | 카페게이트가 협력업체와 직접 계약 | CJ 마진 제거 → 원가 낮아질 수 있음, 단 물류비 직접 부담 |
""")

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

# ── 시나리오 파라미터 ─────────────────────────────────────────
st.markdown("---")
st.markdown("### 직매입 시나리오 설정")

col1, col2, col3 = st.columns(3)

with col1:
    direct_discount = st.slider(
        "협력업체 직매입 단가 할인율 (%)",
        min_value=0, max_value=30, value=8, step=1,
        help="CJ 마진이 빠지면서 협력업체 매입가가 낮아지는 비율입니다.",
    )

with col2:
    logistics_cost = st.slider(
        "직매입 시 물류비 (판매단가 대비 %)",
        min_value=0, max_value=20, value=5, step=1,
        help="직매입 시 카페게이트가 직접 부담하는 물류비입니다.",
    )

with col3:
    target_rate = st.number_input(
        "목표 원가율 (%)",
        min_value=40.0, max_value=90.0, value=65.0, step=0.5,
    )

# ── 계산 ─────────────────────────────────────────────────────
df_comp = df.copy()

# 현행: 역매입 원가율 기준
df_comp["현행_원가율"] = df_comp["역매입원가율"]
df_comp["현행_원가"] = df_comp["역매입단가"]

# 직매입: 협력업체 매입가에서 할인 + 물류비 직접 부담
df_comp["직매입_매입단가"] = (df_comp["매입단가"] * (1 - direct_discount / 100)).round(0)
df_comp["직매입_물류비"] = (df_comp["판매단가"] * logistics_cost / 100).round(0)
df_comp["직매입_총원가"] = df_comp["직매입_매입단가"] + df_comp["직매입_물류비"]
df_comp["직매입_원가율"] = (df_comp["직매입_총원가"] / df_comp["판매단가"] * 100).round(1)

df_comp["원가율_개선"] = (df_comp["현행_원가율"] - df_comp["직매입_원가율"]).round(1)
df_comp["개선여부"] = df_comp["직매입_원가율"] < df_comp["현행_원가율"]
df_comp["월절감액"] = ((df_comp["현행_원가"] - df_comp["직매입_총원가"]) * df_comp["월매출수량"]).astype(int)

# ── 요약 ─────────────────────────────────────────────────────
st.markdown("---")

total_rev = (df_comp["판매단가"] * df_comp["월매출수량"]).sum()
current_cost = (df_comp["현행_원가"] * df_comp["월매출수량"]).sum()
direct_cost = (df_comp["직매입_총원가"] * df_comp["월매출수량"]).sum()

current_avg = current_cost / total_rev * 100
direct_avg = direct_cost / total_rev * 100
monthly_saving = int(current_cost - direct_cost)

m1, m2, m3, m4 = st.columns(4)
m1.metric("현행 평균 원가율 (역매입)", f"{current_avg:.1f}%")
m2.metric(
    "직매입 평균 원가율",
    f"{direct_avg:.1f}%",
    delta=f"{direct_avg - current_avg:.1f}%p",
    delta_color="inverse",
)
m3.metric("목표 원가율", f"{target_rate}%")
m4.metric(
    "월 예상 절감액",
    f"₩{monthly_saving:,}",
    delta="직매입 전환 시" if monthly_saving > 0 else "비용 증가",
    delta_color="normal" if monthly_saving > 0 else "inverse",
)

# ── 비교 테이블 ──────────────────────────────────────────────
st.markdown("---")
st.markdown("### 품목별 구조 비교")

display_cols = [
    "품목명", "카테고리", "판매단가",
    "현행_원가", "현행_원가율",
    "직매입_매입단가", "직매입_물류비", "직매입_총원가", "직매입_원가율",
    "원가율_개선", "월절감액",
]

def highlight_improvement(row):
    if row["원가율_개선"] > 0:
        return ["background-color: #e8f5e9"] * len(row)
    elif row["원가율_개선"] < 0:
        return ["background-color: #ffebee"] * len(row)
    return [""] * len(row)

st.dataframe(
    df_comp[display_cols].style.apply(highlight_improvement, axis=1),
    use_container_width=True,
    height=380,
)

# ── 차트 ─────────────────────────────────────────────────────
st.markdown("---")
tab1, tab2 = st.tabs(["원가율 비교", "월 절감액"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="현행 (역매입)",
        x=df_comp["품목명"],
        y=df_comp["현행_원가율"],
        marker_color="#EF9A9A",
    ))
    fig.add_trace(go.Bar(
        name="직매입 시나리오",
        x=df_comp["품목명"],
        y=df_comp["직매입_원가율"],
        marker_color="#81C784",
    ))
    fig.add_hline(y=target_rate, line_dash="dash", line_color="blue",
                  annotation_text=f"목표 {target_rate}%")
    fig.update_layout(
        barmode="group", xaxis_tickangle=-45, height=420,
        title="유통구조별 원가율 비교",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    colors = ["#43A047" if v > 0 else "#E53935" for v in df_comp["월절감액"]]
    fig2 = go.Figure(go.Bar(
        x=df_comp["품목명"],
        y=df_comp["월절감액"],
        marker_color=colors,
        text=df_comp["월절감액"].apply(lambda x: f"₩{x:,}"),
        textposition="outside",
    ))
    fig2.add_hline(y=0, line_color="gray")
    fig2.update_layout(
        title="품목별 월 절감 예상액 (직매입 전환 시)",
        xaxis_tickangle=-45, height=420,
    )
    st.caption("녹색: 절감 | 빨간색: 비용 증가")
    st.plotly_chart(fig2, use_container_width=True)

# ── 의사결정 가이드 ──────────────────────────────────────────
st.markdown("---")
st.markdown("### 직매입 전환 우선순위 품목")

df_priority = df_comp[df_comp["원가율_개선"] > 0].sort_values("월절감액", ascending=False)

if len(df_priority) > 0:
    st.success(f"직매입 전환 시 원가 개선이 기대되는 품목: **{len(df_priority)}개**")
    st.dataframe(
        df_priority[["품목명", "카테고리", "현행_원가율", "직매입_원가율", "원가율_개선", "월절감액"]].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.warning("현재 파라미터 설정에서는 직매입 전환 시 개선되는 품목이 없습니다. 할인율을 높이거나 물류비를 낮춰보세요.")
