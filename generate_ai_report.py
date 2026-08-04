# ============================================================
# generate_ai_report.py  (전체 교체본 v2)
#  analysis_summary.csv -> Gemini API 분석 -> data/ai_report.csv / .md
#  * 사용 가능한 모델을 자동 조회하여 선택 (404 방지)
# ============================================================
import os
import sys
import json
from datetime import datetime

import requests
import pandas as pd

API_KEY = os.environ.get("GEMINI_API_KEY", "")
BASE = "https://generativelanguage.googleapis.com/v1beta"
PREFERRED = ["flash-latest", "3.5-flash", "3-flash", "2.5-flash", "2.0-flash", "flash", "pro"]

CONTEXT = """
[사업 개요]
- 민관합동 PF 방식 도시개발사업
- 2024년 기준 타당성 검토 완료 (모든 사업비 산정의 기준시점)
- 2026년 민간참여자 공모/협상 진행
- 2027년 1월 PFV 설립 예정
- 2029년 PF대출 실행 및 보상(수용) 예정
[경보 임계치]
- 공사비: 전년동월비 +5% 초과 / 보상비: +3%p 초과 / PF금리: +0.5%p 초과
[지표 해석 지침]
- PPI는 건설공사비지수의 선행지표로, 괴리 확대는 향후 공사비 상승 신호
- 회사채 BBB- 수익률은 PF 조달금리의 근사치, AA-와의 스프레드 확대는 신용경색 신호
- 지가변동률 누적치는 2029년 보상비 상승압력의 근사치
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "종합요약": {"type": "array", "items": {"type": "string"}},
        "부문분석": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "부문": {"type": "string"},
                    "리스크등급": {"type": "string", "enum": ["높음", "보통", "낮음"]},
                    "핵심진단": {"type": "string"},
                    "근거지표": {"type": "string"},
                    "대응옵션": {"type": "string"},
                },
                "required": ["부문", "리스크등급", "핵심진단", "근거지표", "대응옵션"],
            },
        },
    },
    "required": ["종합요약", "부문분석"],
}


def build_prompt(csv_text):
    return f"""너는 지방공기업 도시개발사업의 재무 리스크 분석관이다.
{CONTEXT}

[이번 달 지표 분석 결과 (CSV)]
{csv_text}

[작성 지침]
1. 부문분석: '공사비', '보상비', 'PF금리' 3개 부문 각각에 대해
   - 리스크등급(높음/보통/낮음)을 임계치와 2024년 대비 이탈 폭을 근거로 판정
   - 핵심진단은 2문장 이내, 반드시 구체적 수치를 포함
   - 근거지표는 지표명과 수치를 간결히 나열
   - 대응옵션은 협약조건/보상시기/금융조달 등 실행 가능한 조치로 1~2개
2. 종합요약: 임원 보고용으로 정확히 5개 문장. 각 문장에 수치를 포함할 것
3. 데이터에 없는 사실을 추측해 단정하지 말 것. 결측/실패 지표는 언급하지 않아도 된다
4. 모든 문장은 한국어 서술형으로 작성"""


def pick_model():
    r = requests.get(f"{BASE}/models", params={"key": API_KEY}, timeout=60)
    if r.status_code != 200:
        print(f"[모델조회 오류 {r.status_code}] {r.text[:600]}")
    r.raise_for_status()
    names = [m["name"] for m in r.json().get("models", [])
             if "generateContent" in m.get("supportedGenerationMethods", [])]
    print("[모델] 사용 가능:", ", ".join(n.replace("models/", "") for n in names))
    for kw in PREFERRED:
        for n in names:
            base = n.replace("models/", "")
            if kw in base and "vision" not in base and "embedding" not in base:
                print(f"[모델] 선택: {base}")
                return n
    if names:
        print(f"[모델] 선택(대체): {names[0]}")
        return names[0]
    raise RuntimeError("사용 가능한 모델이 없습니다.")


def call_gemini(prompt):
    model = pick_model()
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA,
        },
    }
    r = requests.post(f"{BASE}/{model}:generateContent",
                      params={"key": API_KEY}, json=body, timeout=180)
    if r.status_code != 200:
        print(f"[생성 응답오류 {r.status_code}] {r.text[:800]}")
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


def to_outputs(parsed, ym):
    os.makedirs("data", exist_ok=True)
    rows = [{"기준월": ym, "구분": "부문분석", "부문": d["부문"], "리스크등급": d["리스크등급"],
             "핵심진단": d["핵심진단"], "근거지표": d["근거지표"], "대응옵션": d["대응옵션"]}
            for d in parsed["부문분석"]]
    for i, s in enumerate(parsed["종합요약"], 1):
        rows.append({"기준월": ym, "구분": "종합요약", "부문": str(i), "리스크등급": "",
                     "핵심진단": s, "근거지표": "", "대응옵션": ""})
    df = pd.DataFrame(rows)
    df.to_csv("data/ai_report.csv", index=False, encoding="utf-8-sig")

    hist_path = "data/ai_report_history.csv"
    hist = df
    if os.path.exists(hist_path):
        hist = pd.concat([pd.read_csv(hist_path, encoding="utf-8-sig"), df], ignore_index=True)
    hist.to_csv(hist_path, index=False, encoding="utf-8-sig")

    md = [f"# {ym} 개발사업 리스크 월간 리포트", "", "## 종합요약"]
    md += [f"{i}. {s}" for i, s in enumerate(parsed["종합요약"], 1)]
    for d in parsed["부문분석"]:
        md += ["", f"## {d['부문']} (리스크 {d['리스크등급']})",
               f"- 진단: {d['핵심진단']}", f"- 근거: {d['근거지표']}", f"- 대응: {d['대응옵션']}"]
    with open("data/ai_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"[완료] ai_report.csv({len(rows)}행), ai_report.md 생성")


def main():
    if not API_KEY:
        print("[건너뜀] GEMINI_API_KEY 가 없어 AI 리포트를 생성하지 않았습니다.")
        return
    if not os.path.exists("data/analysis_summary.csv"):
        print("[건너뜀] analysis_summary.csv 가 없습니다.")
        return
    df = pd.read_csv("data/analysis_summary.csv", encoding="utf-8-sig")
    ym = datetime.now().strftime("%Y-%m")
    try:
        parsed = call_gemini(build_prompt(df.to_csv(index=False)))
        to_outputs(parsed, ym)
    except Exception as e:
        print(f"[실패] AI 리포트 생성 오류: {str(e)[:500]}")
        sys.exit(0)


if __name__ == "__main__":
    main()
