# ============================================================
# list_ecos_codes.py : ECOS 항목코드 조회 → data/ecos_codes.csv 저장
#  GitHub 서버에서 ECOS 접속이 되는지 확인하는 테스트를 겸합니다.
# ============================================================
import os

import requests
import pandas as pd

from config import ECOS_TABLES_TO_INSPECT

ECOS_KEY = os.environ["ECOS_API_KEY"]


def main():
    rows = []
    for code in ECOS_TABLES_TO_INSPECT:
        url = f"https://ecos.bok.or.kr/api/StatisticItemList/{ECOS_KEY}/json/kr/1/1000/{code}"
        data = requests.get(url, timeout=60).json()
        for r in data.get("StatisticItemList", {}).get("row", []):
            rows.append({
                "통계표코드": code,
                "통계표명": r.get("STAT_NAME", ""),
                "항목코드": r.get("ITEM_CODE", ""),
                "항목명": r.get("ITEM_NAME", ""),
                "주기": r.get("CYCLE", ""),
                "단위": r.get("UNIT_NAME", ""),
            })
        print(f"[성공] {code}: 조회 완료")
    os.makedirs("data", exist_ok=True)
    pd.DataFrame(rows).to_csv("data/ecos_codes.csv", index=False, encoding="utf-8-sig")
    print(f"[완료] data/ecos_codes.csv 에 {len(rows)}건 저장")


if __name__ == "__main__":
    main()
