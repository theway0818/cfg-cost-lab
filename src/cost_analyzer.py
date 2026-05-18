import pandas as pd

ABNORMAL_THRESHOLD = 80.0  # 이 값 초과 시 비정상 플래그


def calc_cost_rates(df: pd.DataFrame) -> pd.DataFrame:
    """매입 원가율, 역매입 원가율, 비정상 플래그를 계산해서 컬럼 추가."""
    result = df.copy()
    result["매입원가율"] = (result["매입단가"] / result["판매단가"] * 100).round(1)
    result["역매입원가율"] = (result["역매입단가"] / result["판매단가"] * 100).round(1)
    result["매입_비정상"] = result["매입원가율"] > ABNORMAL_THRESHOLD
    result["역매입_비정상"] = result["역매입원가율"] > ABNORMAL_THRESHOLD
    result["월매출액"] = (result["판매단가"] * result["월매출수량"]).astype(int)
    return result


def get_summary(df: pd.DataFrame) -> dict:
    """전체 요약 지표 반환."""
    total_revenue = df["월매출액"].sum()
    total_purchase_cost = (df["매입단가"] * df["월매출수량"]).sum()
    total_reverse_cost = (df["역매입단가"] * df["월매출수량"]).sum()

    return {
        "총_월매출액": int(total_revenue),
        "총_매입원가": int(total_purchase_cost),
        "총_역매입원가": int(total_reverse_cost),
        "평균_매입원가율": round(total_purchase_cost / total_revenue * 100, 1),
        "평균_역매입원가율": round(total_reverse_cost / total_revenue * 100, 1),
        "비정상_품목수_매입": int(df["매입_비정상"].sum()),
        "비정상_품목수_역매입": int(df["역매입_비정상"].sum()),
        "전체_품목수": len(df),
    }


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """DataFrame을 엑셀 바이트로 변환 (다운로드용)."""
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="원가율분석")
    return buffer.getvalue()
