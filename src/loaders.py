import pandas as pd
import streamlit as st
from pathlib import Path

REQUIRED_COLUMNS = {
    "품목명": "품목명",
    "카테고리": "카테고리",
    "매입단가": "매입단가",
    "역매입단가": "역매입단가",
    "판매단가": "판매단가",
    "월매출수량": "월매출수량",
}


def load_excel(uploaded_file) -> pd.DataFrame:
    """업로드된 엑셀 파일을 DataFrame으로 반환. 컬럼 검증 포함."""
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    df.columns = df.columns.str.strip()
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")
    numeric_cols = ["매입단가", "역매입단가", "판매단가", "월매출수량"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_sample() -> pd.DataFrame:
    """익명화된 샘플 데이터 반환 (실제 데이터 없을 때 데모용)."""
    data = {
        "품목명": [
            "원두A", "원두B", "원두C",
            "우유A", "우유B",
            "시럽A", "시럽B", "시럽C",
            "소모품A", "소모품B", "소모품C", "소모품D",
            "원두D", "우유C", "시럽D",
        ],
        "카테고리": [
            "원두", "원두", "원두",
            "우유", "우유",
            "시럽", "시럽", "시럽",
            "소모품", "소모품", "소모품", "소모품",
            "원두", "우유", "시럽",
        ],
        "매입단가": [
            18000, 22000, 15000,
            2800, 3100,
            4500, 3800, 5200,
            1200, 980, 1500, 760,
            25000, 2600, 4100,
        ],
        "역매입단가": [
            16500, 20000, 13800,
            2600, 2900,
            4100, 3500, 4800,
            1100, 900, 1380, 700,
            23000, 2400, 3800,
        ],
        "판매단가": [
            25000, 30000, 20000,
            4000, 4500,
            6000, 5500, 7000,
            1500, 1300, 2000, 1000,
            34000, 3800, 5500,
        ],
        "월매출수량": [
            1200, 800, 600,
            3500, 2100,
            900, 750, 400,
            5000, 4200, 1800, 3100,
            300, 1500, 620,
        ],
    }
    return pd.DataFrame(data)
