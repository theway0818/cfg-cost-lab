import pandas as pd


def calc_pareto(df: pd.DataFrame, top_pct: float = 0.8) -> pd.DataFrame:
    """
    매출액 기준 파레토 분석.
    상위 top_pct(기본 80%) 비중을 차지하는 품목에 핵심품목 플래그 추가.
    """
    result = df.copy().sort_values("월매출액", ascending=False).reset_index(drop=True)
    total = result["월매출액"].sum()
    result["매출비중(%)"] = (result["월매출액"] / total * 100).round(2)
    result["누적비중(%)"] = result["매출비중(%)"].cumsum().round(2)
    result["핵심품목"] = result["누적비중(%)"] <= (top_pct * 100)
    # 경계 품목(누적이 딱 넘어가는 첫 번째)도 포함
    first_over = result[result["누적비중(%)"] > (top_pct * 100)].index
    if len(first_over) > 0:
        result.loc[first_over[0], "핵심품목"] = True
    result["순위"] = range(1, len(result) + 1)
    return result


def get_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """카테고리별 매출액·원가율 요약."""
    grouped = df.groupby("카테고리").agg(
        품목수=("품목명", "count"),
        월매출액합계=("월매출액", "sum"),
        평균_매입원가율=("매입원가율", "mean"),
        평균_역매입원가율=("역매입원가율", "mean"),
    ).reset_index()
    grouped["평균_매입원가율"] = grouped["평균_매입원가율"].round(1)
    grouped["평균_역매입원가율"] = grouped["평균_역매입원가율"].round(1)
    grouped = grouped.sort_values("월매출액합계", ascending=False)
    return grouped
