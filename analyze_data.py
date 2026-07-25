# ============================================================
# analyze_data.py : dashboard_data.csv 를 읽어
#  1) 지표별 요약(전년동월비, 2024년 대비, 경보) → data/analysis_summary.csv
#  2) 마일스톤 시점 참고 전망(밴드 포함)        → data/forecast_long.csv
#  (이 파일은 수정할 필요가 없습니다. 임계치만 아래에서 조정 가능)
# ============================================================
import os
import numpy as np
import pandas as pd

BASELINE_YEAR = 2024        # 타당성 검토 기준연도
TREND_WINDOW = 24           # 추세 산정에 사용할 최근 개월 수
FORECAST_END = "2029-12-01" # 전망 종료 시점

# 경보 임계치 (필요시 조정)
TH = {"공사비": 5.0,   # 전년동월비 +5% 초과 시 경보 (%)
      "보상비": 3.0,   # 전년동월 대비 +3%p 초과 시 경보 (%p)
      "PF금리": 0.5}   # 전년동월 대비 +0.5%p 초과 시 경보 (%p)


def main():
    df = pd.read_csv("data/dashboard_data.csv", encoding="utf-8-sig")
    df["기준월"] = pd.to_datetime(df["기준월"])
    df = df.dropna(subset=["값"])

    summary, fc_rows = [], []
    for (cat, name, item, unit, src), g in df.groupby(["대분류", "지표명", "항목", "단위", "출처"]):
        g = g.sort_values("기준월").reset_index(drop=True)
        if len(g) < 15:
            continue
        latest, latest_dt = g["값"].iloc[-1], g["기준월"].iloc[-1]

        # 1) 전년동월비
        prev = g[g["기준월"] == latest_dt - pd.DateOffset(years=1)]["값"]
        if cat == "PF금리" or unit == "%":  # 금리·변동률형 지표는 %p 차이
            yoy = round(latest - prev.iloc[0], 3) if len(prev) else np.nan
            yoy_unit = "%p"
        else:                # 지수·단가는 % 변화율
            yoy = round((latest / prev.iloc[0] - 1) * 100, 2) if len(prev) else np.nan
            yoy_unit = "%"

        # 2) 2024년(타당성 기준연도) 평균 대비
        base = g[g["기준월"].dt.year == BASELINE_YEAR]["값"].mean()
        if cat == "PF금리" or unit == "%":
            vs_base = round(latest - base, 3) if pd.notna(base) else np.nan
        else:
            vs_base = round((latest / base - 1) * 100, 2) if pd.notna(base) else np.nan

        # 3) 경보 판정
        alert = "정상"
        if pd.notna(yoy) and yoy > TH.get(cat, 999):
            alert = "경보"
        elif pd.notna(yoy) and yoy > TH.get(cat, 999) * 0.6:
            alert = "주의"

        # 4) 참고 전망 (금리·변동률=현수준 유지+변동성 밴드 / 지수=추세 연장+잔차 밴드)
        h_months = pd.date_range(latest_dt + pd.DateOffset(months=1), FORECAST_END, freq="MS")
        r = g.tail(TREND_WINDOW).copy()
        t = (r["기준월"].dt.year * 12 + r["기준월"].dt.month).values.astype(float)
        if cat == "PF금리" or unit == "%":
            vol = g["값"].diff().dropna().tail(TREND_WINDOW).std()
            for i, d in enumerate(h_months, 1):
                band = 1.96 * vol * np.sqrt(i)
                fc_rows.append([d, cat, name, item, np.nan,
                                round(latest, 3), round(latest - band, 3), round(latest + band, 3)])
        else:
            slope, intercept = np.polyfit(t, r["값"].values, 1)
            resid = r["값"].values - (slope * t + intercept)
            band = 1.96 * resid.std()
            for d in h_months:
                tt = d.year * 12 + d.month
                c = slope * tt + intercept
                fc_rows.append([d, cat, name, item, np.nan,
                                round(c, 3), round(c - band, 3), round(c + band, 3)])

        # 실적도 전망 파일에 함께 기록 (Looker에서 한 차트에 그리기 위함)
        for _, row in g.iterrows():
            fc_rows.append([row["기준월"], cat, name, item, row["값"], np.nan, np.nan, np.nan])

        # 마일스톤 시점 전망값 추출
        fdf = pd.DataFrame(fc_rows, columns=["기준월","대분류","지표명","항목","실적","전망중심","전망하단","전망상단"])
        def at(dt_str):
            m = fdf[(fdf["지표명"] == name) & (fdf["항목"] == item) & (fdf["기준월"] == dt_str)]["전망중심"]
            return m.iloc[0] if len(m) else np.nan

        summary.append([cat, name, item, unit, src,
                        latest_dt.strftime("%Y-%m"), latest,
                        yoy, yoy_unit, round(base, 2) if pd.notna(base) else np.nan, vs_base,
                        at("2027-01-01"), at("2029-01-01"), alert])

    pd.DataFrame(summary, columns=[
        "대분류","지표명","항목","단위","출처","최신월","최신값",
        "전년동월비","전년동월비단위","기준연도평균(2024)","2024대비",
        "전망_2027-01(PFV설립)","전망_2029-01(PF·보상)","경보상태"
    ]).to_csv("data/analysis_summary.csv", index=False, encoding="utf-8-sig")

    pd.DataFrame(fc_rows, columns=["기준월","대분류","지표명","항목","실적","전망중심","전망하단","전망상단"]
    ).sort_values(["지표명","항목","기준월"]).to_csv("data/forecast_long.csv", index=False, encoding="utf-8-sig")
    print("[완료] analysis_summary.csv, forecast_long.csv 저장")


if __name__ == "__main__":
    main()
