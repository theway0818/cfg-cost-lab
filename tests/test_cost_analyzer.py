import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.loaders import load_sample
from src.cost_analyzer import calc_cost_rates, get_summary, ABNORMAL_THRESHOLD
from src.pareto import calc_pareto, get_category_summary
from src.simulator import calc_target_price, TARGET_COST_RATE


def test_cost_rate_formula():
    """매입 원가율 계산 공식 검증."""
    df = pd.DataFrame({
        "품목명": ["테스트"],
        "카테고리": ["테스트"],
        "매입단가": [6500],
        "역매입단가": [6000],
        "판매단가": [10000],
        "월매출수량": [100],
    })
    result = calc_cost_rates(df)
    assert result["매입원가율"].iloc[0] == 65.0, "매입원가율 계산 오류"
    assert result["역매입원가율"].iloc[0] == 60.0, "역매입원가율 계산 오류"
    assert result["월매출액"].iloc[0] == 1_000_000, "월매출액 계산 오류"
    print("[PASS] 원가율 계산 공식 정상")


def test_abnormal_flag():
    """비정상 플래그 (원가율 > 80%) 검증."""
    df = pd.DataFrame({
        "품목명": ["정상품목", "비정상품목"],
        "카테고리": ["A", "A"],
        "매입단가": [6000, 9000],
        "역매입단가": [5500, 8500],
        "판매단가": [10000, 10000],
        "월매출수량": [100, 50],
    })
    result = calc_cost_rates(df)
    assert result["매입_비정상"].iloc[0] == False, "정상 품목이 비정상으로 표시됨"
    assert result["매입_비정상"].iloc[1] == True, "비정상 품목이 정상으로 표시됨"
    print("[PASS] 비정상 플래그 정상")


def test_pareto_core_items():
    """파레토 분석 — 핵심품목 누적 비중 80% 이상 포함 검증."""
    df = load_sample()
    df = calc_cost_rates(df)
    df_pareto = calc_pareto(df, top_pct=0.8)
    core = df_pareto[df_pareto["핵심품목"]]
    assert core["매출비중(%)"].sum() >= 80.0, "핵심품목 누적 비중이 80% 미만"
    assert "순위" in df_pareto.columns, "순위 컬럼 없음"
    print(f"[PASS] 파레토 분석 정상 - 핵심품목 {len(core)}개 / 전체 {len(df_pareto)}개")


def test_target_price_calc():
    """목표 원가율 달성 매입단가 계산 검증."""
    max_price = calc_target_price(sell_price=10000, target_rate=65.0)
    assert max_price == 6500.0, f"목표 매입단가 계산 오류: {max_price}"
    print("[PASS] 목표 매입단가 계산 정상")


def test_sample_data_integrity():
    """샘플 데이터 컬럼 무결성 검증."""
    df = load_sample()
    required = ["품목명", "카테고리", "매입단가", "역매입단가", "판매단가", "월매출수량"]
    for col in required:
        assert col in df.columns, f"필수 컬럼 누락: {col}"
    assert len(df) > 0, "샘플 데이터가 비어있음"
    assert (df["매입단가"] > 0).all(), "매입단가에 0 이하 값 포함"
    assert (df["판매단가"] > df["매입단가"]).all(), "판매단가가 매입단가보다 낮은 품목 존재"
    print(f"[PASS] 샘플 데이터 무결성 정상 - {len(df)}개 품목")


if __name__ == "__main__":
    print("=== CFG Cost Lab 테스트 실행 ===\n")
    test_sample_data_integrity()
    test_cost_rate_formula()
    test_abnormal_flag()
    test_pareto_core_items()
    test_target_price_calc()
    print("\n모든 테스트 통과!")
