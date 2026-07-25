# ============================================================
# collect_data.py : KOSIS/ECOS 수집 → data/dashboard_data.csv 저장
#  (이 파일은 수정할 필요가 없습니다)
# ============================================================
import os
from datetime import datetime

import requests
import pandas as pd

from config import START_YM, ECOS_SERIES, KOSIS_SERIES

ECOS_KEY = os.environ["ECOS_API_KEY"]
KOSIS_KEY = os.environ["KOSIS_API_KEY"]
NOW = datetime.now()


def period_range(cycle):
    if cycle == "M":
        return START_YM, NOW.strftime("%Y%m")
    if cycle == "D":
        return START_YM + "01", NOW.strftime("%Y%m%d")
    if cycle == "Q":
        q_start = (int(START_YM[4:6]) - 1) // 3 + 1
        q_now = (NOW.month - 1) // 3 + 1
        return f"{START_YM[:4]}Q{q_start}", f"{NOW.year}Q{q_now}"
    raise ValueError(f"지원하지 않는 주기: {cycle}")


def quarter_to_month(t):
    t = str(t).replace("Q", "")
    year, q = t[:4], int(t[4:])
    return f"{year}-{(q - 1) * 3 + 1:02d}-01"


def fetch_ecos(s):
    start, end = period_range(s["cycle"])
    url = (
        f"https://ecos.bok.or.kr/api/StatisticSearch/{ECOS_KEY}/json/kr/"
        f"1/10000/{s['stat_code']}/{s['cycle']}/{start}/{end}/{s['item_code']}"
    )
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "StatisticSearch" not in data:
        msg = data.get("RESULT", {}).get("MESSAGE", str(data)[:200])
        raise RuntimeError(f"ECOS 응답 오류: {msg}")
    df = pd.DataFrame(data["StatisticSearch"]["row"])[["TIME", "ITEM_NAME1", "DATA_VALUE"]]
    df.columns = ["기간", "항목", "값"]
    df["값"] = pd.to_numeric(df["값"], errors="coerce")
    if s["cycle"] == "D":
        df["기준월"] = pd.to_datetime(df["기간"], format="%Y%m%d").dt.strftime("%Y-%m-01")
        df = df.groupby(["기준월", "항목"], as_index=False)["값"].mean().round(3)
    elif s["cycle"] == "M":
        df["기준월"] = df["기간"].str[:4] + "-" + df["기간"].str[4:6] + "-01"
        df = df[["기준월", "항목", "값"]]
    else:  # Q
        df["기준월"] = df["기간"].apply(quarter_to_month)
        df = df[["기준월", "항목", "값"]]
    return df.sort_values("기준월").reset_index(drop=True)


def prd_to_month(p):
    p = str(p)
    if len(p) >= 6:
        return f"{p[:4]}-{p[4:6]}-01"
    return f"{p[:4]}-01-01"  # 연간 자료는 1월 1일로 표기


def fetch_kosis(s):
    if not s["url"].startswith("http"):
        raise RuntimeError("KOSIS URL이 아직 입력되지 않았습니다.")
    r = requests.get(s["url"].replace("__KEY__", KOSIS_KEY), timeout=60)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict):  # 정상이면 list, 오류면 dict
        raise RuntimeError(f"KOSIS 응답 오류: {str(data)[:300]}")
    df = pd.DataFrame(data)
    name_cols = [c for c in ["C1_NM", "C2_NM", "C3_NM", "ITM_NM"] if c in df.columns]
    df["항목"] = df[name_cols].astype(str).apply(
        lambda row: " / ".join(v for v in row if v not in ("", "nan", "None")), axis=1
    )
    df["기준월"] = df["PRD_DE"].apply(prd_to_month)
    df["값"] = pd.to_numeric(df["DT"], errors="coerce")
    df = df[["기준월", "항목", "값"]]
    return df.sort_values("기준월").reset_index(drop=True)


def main():
    os.makedirs("data", exist_ok=True)
    master_parts = []
    logs = []
    for s in ECOS_SERIES + KOSIS_SERIES:
        try:
            df = fetch_ecos(s) if "stat_code" in s else fetch_kosis(s)
            m = df.copy()
            m["대분류"] = s["category"]
            m["지표명"] = s["name"]
            m["단위"] = s["unit"]
            m["출처"] = "ECOS" if "stat_code" in s else "KOSIS"
            master_parts.append(m[["기준월", "대분류", "지표명", "항목", "값", "단위", "출처"]])
            logs.append([NOW.strftime("%Y-%m-%d %H:%M"), s["tab"], "성공", f"{len(df)}행 수집"])
            print(f"[성공] {s['tab']}: {len(df)}행")
        except Exception as e:
            logs.append([NOW.strftime("%Y-%m-%d %H:%M"), s["tab"], "실패", str(e)[:300]])
            print(f"[실패] {s['tab']}: {e}")
    if master_parts:
        pd.concat(master_parts, ignore_index=True).to_csv(
            "data/dashboard_data.csv", index=False, encoding="utf-8-sig"
        )
        print("[완료] data/dashboard_data.csv 저장")
    log_df = pd.DataFrame(logs, columns=["실행시각", "지표", "결과", "비고"])
    log_path = "data/collect_log.csv"
    if os.path.exists(log_path):
        log_df = pd.concat([pd.read_csv(log_path, encoding="utf-8-sig"), log_df], ignore_index=True)
    log_df.to_csv(log_path, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
