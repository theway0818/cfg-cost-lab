import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
from pathlib import Path

if not st.session_state.get("authentication_status"):
    st.warning("로그인이 필요합니다. 홈 화면에서 로그인해 주세요.")
    st.stop()

sys.path.append(str(Path(__file__).parent.parent))

st.set_page_config(page_title="신메뉴 BEP", page_icon="🆕", layout="wide")

with st.sidebar:
    st.title("📊 CFG Cost Lab")
    st.markdown("---")
    st.markdown("**카페게이트 구매물류팀**")
    st.caption("⚠️ 사내 전용 — 외부 공유 금지")

st.title("🆕 신메뉴 원가 · BEP 분석")
st.markdown(
    "신메뉴 출시 전 **원재료 원가율**과 **손익분기점(BEP) 판매 수량**을 미리 계산합니다.  \n"
    "BEP = 고정비 ÷ (판매가 - 변동비)"
)

with st.expander("BEP(손익분기점)이란? (클릭해서 확인)"):
    st.markdown("""
**BEP(Break-Even Point, 손익분기점)**이란 이익도 손실도 나지 않는 판매 수량입니다.

| 용어 | 의미 | 예시 |
|------|------|------|
| **판매가** | 점주가 손님에게 받는 가격 | 6,500원 |
| **변동비** | 1개 팔 때마다 드는 원재료비 | 3,200원 |
| **고정비** | 판매량과 상관없이 드는 비용 | 월 500,000원 |
| **BEP** | 고정비 ÷ (판매가 - 변동비) | 500,000 ÷ (6,500 - 3,200) = 152개 |

→ 월 152개 이상 팔아야 손해를 안 봅니다.
""")

# ── 신메뉴 기본 정보 ─────────────────────────────────────────
st.markdown("---")
st.markdown("### 1단계: 신메뉴 기본 정보")

col1, col2, col3 = st.columns(3)
with col1:
    menu_name = st.text_input("신메뉴 이름", value="신메뉴A")
with col2:
    sell_price = st.number_input("점주 판매가 (원)", min_value=100, value=6500, step=100)
with col3:
    target_rate = st.number_input("목표 원가율 (%)", min_value=10.0, max_value=90.0, value=65.0, step=0.5)

# ── 원재료 입력 ──────────────────────────────────────────────
st.markdown("---")
st.markdown("### 2단계: 원재료 구성")
st.caption("원재료를 추가하고 각각의 단가와 사용량을 입력하세요.")

if "ingredients" not in st.session_state:
    st.session_state.ingredients = [
        {"재료명": "원두A", "단위": "g", "사용량": 20, "단가(원/단위)": 90},
        {"재료명": "우유A", "단위": "ml", "사용량": 200, "단가(원/단위)": 1.4},
        {"재료명": "시럽A", "단위": "ml", "사용량": 15, "단가(원/단위)": 4.5},
    ]

col_add, col_reset = st.columns([1, 5])
with col_add:
    if st.button("+ 재료 추가"):
        st.session_state.ingredients.append(
            {"재료명": f"재료{len(st.session_state.ingredients)+1}", "단위": "g", "사용량": 0, "단가(원/단위)": 0}
        )

ingredients = []
for i, ing in enumerate(st.session_state.ingredients):
    cols = st.columns([2, 1, 1, 2, 1])
    name = cols[0].text_input("재료명", value=ing["재료명"], key=f"name_{i}", label_visibility="collapsed")
    unit = cols[1].selectbox("단위", ["g", "ml", "개"], index=["g", "ml", "개"].index(ing["단위"]) if ing["단위"] in ["g", "ml", "개"] else 0, key=f"unit_{i}", label_visibility="collapsed")
    amount = cols[2].number_input("사용량", value=float(ing["사용량"]), min_value=0.0, step=1.0, key=f"amt_{i}", label_visibility="collapsed")
    price = cols[3].number_input("단가(원/단위)", value=float(ing["단가(원/단위)"]), min_value=0.0, step=0.1, key=f"price_{i}", label_visibility="collapsed")
    cost = amount * price
    cols[4].markdown(f"**₩{cost:,.0f}**")
    ingredients.append({"재료명": name, "단위": unit, "사용량": amount, "단가(원/단위)": price, "원가": cost})

df_ing = pd.DataFrame(ingredients)
total_material_cost = df_ing["원가"].sum()

# ── BEP 계산 설정 ────────────────────────────────────────────
st.markdown("---")
st.markdown("### 3단계: 고정비·BEP 계산")

col1, col2 = st.columns(2)
with col1:
    fixed_cost = st.number_input(
        "월 고정비 (원)",
        min_value=0, value=500000, step=10000,
        help="인건비·임대료 등 이 메뉴에 배분되는 고정비입니다.",
    )
with col2:
    extra_variable = st.number_input(
        "기타 변동비 (원/개)",
        min_value=0.0, value=0.0, step=100.0,
        help="포장재·소모품 등 원재료 외 추가 변동비입니다.",
    )

variable_cost = total_material_cost + extra_variable
margin = sell_price - variable_cost
bep_qty = fixed_cost / margin if margin > 0 else float("inf")
actual_cost_rate = variable_cost / sell_price * 100 if sell_price > 0 else 0
max_allowed_cost = sell_price * target_rate / 100

# ── 결과 대시보드 ────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### 📊 {menu_name} 분석 결과")

m1, m2, m3, m4 = st.columns(4)
m1.metric("총 원재료 원가", f"₩{total_material_cost:,.0f}")
m2.metric(
    "실제 원가율",
    f"{actual_cost_rate:.1f}%",
    delta=f"목표 대비 {actual_cost_rate - target_rate:+.1f}%p",
    delta_color="inverse",
)
m3.metric("1개당 마진", f"₩{margin:,.0f}")

if bep_qty == float("inf"):
    m4.metric("월 BEP 수량", "계산 불가 (마진 ≤ 0)")
else:
    m4.metric("월 BEP 수량", f"{bep_qty:.0f}개")

# 원가율 경고
if actual_cost_rate > target_rate:
    st.error(
        f"원가율 {actual_cost_rate:.1f}%는 목표({target_rate}%)를 초과합니다. "
        f"원재료 원가를 ₩{total_material_cost - max_allowed_cost:,.0f} 줄여야 합니다."
    )
elif actual_cost_rate > target_rate * 0.95:
    st.warning(f"원가율이 목표에 근접합니다. 원재료 구성을 재검토하세요.")
else:
    st.success(f"원가율 {actual_cost_rate:.1f}% — 목표 {target_rate}% 달성!")

# ── 원재료 구성 차트 ─────────────────────────────────────────
st.markdown("---")
tab1, tab2 = st.tabs(["원재료 구성", "BEP 차트"])

with tab1:
    col_pie, col_tbl = st.columns([1, 1])
    with col_pie:
        if total_material_cost > 0:
            fig_pie = go.Figure(go.Pie(
                labels=df_ing["재료명"],
                values=df_ing["원가"],
                hole=0.4,
                texttemplate="%{label}<br>₩%{value:,.0f}<br>(%{percent})",
            ))
            fig_pie.update_layout(title="원재료별 원가 비중", height=350)
            st.plotly_chart(fig_pie, use_container_width=True)

    with col_tbl:
        st.dataframe(
            df_ing[["재료명", "단위", "사용량", "단가(원/단위)", "원가"]].assign(
                원가=df_ing["원가"].apply(lambda x: f"₩{x:,.0f}")
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown(f"**합계: ₩{total_material_cost:,.0f}** (원가율 {actual_cost_rate:.1f}%)")
        st.markdown(f"목표 원가 상한: **₩{max_allowed_cost:,.0f}**")

with tab2:
    if bep_qty != float("inf") and bep_qty > 0:
        qty_range = range(0, int(bep_qty * 2.5) + 1, max(1, int(bep_qty // 20)))
        revenue_line = [sell_price * q for q in qty_range]
        total_cost_line = [fixed_cost + variable_cost * q for q in qty_range]

        fig_bep = go.Figure()
        fig_bep.add_trace(go.Scatter(
            x=list(qty_range), y=revenue_line,
            name="매출액", line=dict(color="#1976D2", width=2),
        ))
        fig_bep.add_trace(go.Scatter(
            x=list(qty_range), y=total_cost_line,
            name="총비용", line=dict(color="#E53935", width=2),
        ))
        fig_bep.add_vline(
            x=bep_qty, line_dash="dash", line_color="green",
            annotation_text=f"BEP {bep_qty:.0f}개",
        )
        fig_bep.update_layout(
            title="BEP 차트 — 매출액 vs 총비용",
            xaxis_title="판매 수량 (개/월)",
            yaxis_title="금액 (원)",
            height=420,
        )
        st.plotly_chart(fig_bep, use_container_width=True)
    else:
        st.warning("마진이 0 이하입니다. 판매가를 높이거나 변동비를 낮추세요.")
