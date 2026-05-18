import pandas as pd

TARGET_COST_RATE = 65.0  # 목표 원가율 기본값 (%)


def simulate_price_change(df: pd.DataFrame, price_change_pct: float) -> pd.DataFrame:
    """
    매입단가를 price_change_pct% 변경했을 때의 원가율 시뮬레이션.
    예) price_change_pct = -5 → 매입단가 5% 인하
    """
    result = df.copy()
    result["시뮬_매입단가"] = (result["매입단가"] * (1 + price_change_pct / 100)).round(0)
    result["시뮬_매입원가율"] = (result["시뮬_매입단가"] / result["판매단가"] * 100).round(1)
    result["원가율_개선"] = (result["매입원가율"] - result["시뮬_매입원가율"]).round(1)
    return result


def calc_target_price(sell_price: float, target_rate: float = TARGET_COST_RATE) -> float:
    """목표 원가율을 달성하기 위한 최대 허용 매입단가 계산."""
    return round(sell_price * target_rate / 100, 0)
