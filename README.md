# CFG Cost Lab

카페게이트 구매물류팀을 위한 **원가율 진단·시뮬레이션 도구**

## 개요

매출원가율 70%대 → 65% 인하 목표 달성을 위해,  
협력업체 매입가와 CJ 역매입가를 2축으로 분리 분석하는 내부 전용 웹 도구입니다.

## 실행 환경

- Python 3.11 이상
- 인터넷 연결 불필요 (사내 PC 전용)

## 설치 방법

```bash
# 1. 가상환경 생성
python -m venv .venv

# 2. 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 3. 라이브러리 설치
pip install -r requirements.txt
```

## 실행 방법

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 자동 오픈

## 폴더 구조

```
cfg-cost-lab/
├── app.py                  # 메인 진입점 (홈 화면)
├── pages/
│   ├── 1_품목별원가율.py    # Phase 1 기능 1
│   └── 2_핵심품목_2080.py  # Phase 1 기능 2
├── src/
│   ├── loaders.py          # 엑셀 파일 읽기
│   ├── cost_analyzer.py    # 원가율 계산 로직
│   ├── pareto.py           # 파레토(20·80) 분석
│   └── simulator.py        # 시뮬레이션 로직
├── data/
│   ├── raw/        ← Git 제외 (실제 거래 데이터)
│   ├── processed/  ← 가공된 중간 결과
│   └── samples/    ← 익명화 샘플 데이터
└── tests/
```

## 로드맵

| Phase | 내용 | 기간 |
|-------|------|------|
| Phase 1 | 품목별 원가율 전수조사 + 20·80 분석 | 현재 |
| Phase 2 | 점주 판가 가이드라인 시뮬레이터 | +2주 |
| Phase 3 | 유통구조 재설계 비교 | +2주 |
| Phase 4 | 메뉴 원가 + 신메뉴 BEP 분석 | +3~4주 |

## 보안 주의사항

- `data/raw/` 폴더는 Git에 절대 올리지 않습니다.
- 실제 거래처명·단가는 코드에 하드코딩하지 않습니다.
- 외부 서버(클라우드)로 데이터를 전송하는 기능은 없습니다.
