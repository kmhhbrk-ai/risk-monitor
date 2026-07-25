# ============================================================
# [설정 파일] 여러분이 수정할 파일은 이 파일 하나입니다.
#  - "확인필요" 표시가 있는 코드는 안내에 따라 실제 코드로
#    바꿔 넣은 뒤 사용하세요.
# ============================================================

# 데이터 수집 시작 시점 (YYYYMM) - 필요시 변경
START_YM = "201501"

# ------------------------------------------------------------
# 1) 한국은행 ECOS 지표
#    stat_code : 통계표코드 / item_code : 통계항목코드
#    cycle     : M(월), D(일), Q(분기)  ※ 일 단위는 자동으로 월평균 변환
# ------------------------------------------------------------
ECOS_SERIES = [
    # --- PF 대출금리 관련 (817Y002: 시장금리 일별) ---
    {"tab": "금리_CD91일",     "category": "PF금리", "stat_code": "817Y002", "cycle": "D", "item_code": "010502000", "unit": "%", "name": "CD(91일) 수익률"},           # 확인필요
    {"tab": "금리_국고채3년",  "category": "PF금리", "stat_code": "817Y002", "cycle": "D", "item_code": "010200000", "unit": "%", "name": "국고채(3년) 수익률"},         # 확인필요
    {"tab": "금리_회사채AA",   "category": "PF금리", "stat_code": "817Y002", "cycle": "D", "item_code": "010300000", "unit": "%", "name": "회사채(3년, AA-) 수익률"},    # 확인필요
    {"tab": "금리_회사채BBB",  "category": "PF금리", "stat_code": "817Y002", "cycle": "D", "item_code": "010320000", "unit": "%", "name": "회사채(3년, BBB-) 수익률"},   # 확인필요

    # --- 공사비 관련 (404Y015: 생산자물가지수 특수분류) ---
    {"tab": "PPI_형강",    "category": "공사비", "stat_code": "404Y015", "cycle": "M", "item_code": "307122AA", "unit": "2020=100", "name": "생산자물가지수(형강)"},  # 확인필요
    {"tab": "PPI_철근 및 봉강",        "category": "공사비", "stat_code": "404Y015", "cycle": "M", "item_code": "307121AA", "unit": "2020=100", "name": "생산자물가지수(철근 및 봉강)"},      # 확인필요

    # --- 보상비 관련 ---
    {"tab": "CPI_총지수",      "category": "보상비", "stat_code": "901Y009", "cycle": "M", "item_code": "0", "unit": "2020=100", "name": "소비자물가지수(총지수)"},
    {"tab": "GDP디플레이터",   "category": "보상비", "stat_code": "확인필요", "cycle": "Q", "item_code": "확인필요", "unit": "2020=100", "name": "GDP 디플레이터"},          # 확인필요
]

# ------------------------------------------------------------
# 2) KOSIS 지표
#    KOSIS 통계표 화면의 [OpenAPI] 버튼으로 생성한 URL을 그대로
#    붙여 넣되, apiKey= 뒤의 본인 인증키 부분만 __KEY__ 로 바꿔 주세요.
#    (인증키가 코드에 노출되지 않게 하기 위한 조치입니다)
# ------------------------------------------------------------
KOSIS_SERIES = [
    {"tab": "건설공사비지수",  "category": "공사비", "name": "건설공사비지수(총지수)",        "unit": "2020=100",
     "url": "https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=__KEY__&itmId=16397AAA0+&objL1=15397AA2AA+15397AA2AA1+15397AA2AA2+&objL2=&objL3=&objL4=&objL5=&objL6=&objL7=&objL8=&format=json&jsonVD=Y&prdSe=M&startPrdDe=202501&endPrdDe=202605&orgId=397&tblId=DT_39701_A003"},
    {"tab": "노임단가",        "category": "공사비", "name": "직종별 시중노임단가",           "unit": "원/일",
     "url": "https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=__KEY__&itmId=16365AAC8+&objL1=15365AG5AB+&objL2=&objL3=&objL4=&objL5=&objL6=&objL7=&objL8=&format=json&jsonVD=Y&prdSe=H&startPrdDe=201501&endPrdDe=202601&orgId=365&tblId=TX_36504_A000"},
    {"tab": "지가변동률_의왕", "category": "보상비", "name": "의왕시 용도지역별 지가변동률",  "unit": "%",
     "url": "https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=__KEY__&itmId=T1+&objL1=10+19+1931+193103+&objL2=&objL3=&objL4=&objL5=&objL6=&objL7=&objL8=&format=json&jsonVD=Y&prdSe=M&startPrdDe=202501&endPrdDe=202605&orgId=408&tblId=DT_31501N_010"},
    {"tab": "토지거래_의왕",   "category": "보상비", "name": "의왕시 토지거래 현황",          "unit": "필지",
     "url": "https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=__KEY__&itmId=13103114390T1+13103114390T2+&objL1=13102114390A.0001+13102114390A.0010+13102114390A.00100034+&objL2=ALL&objL3=&objL4=&objL5=&objL6=&objL7=&objL8=&format=json&jsonVD=Y&prdSe=M&startPrdDe=201501&endPrdDe=202605&orgId=408&tblId=DT_408_2006_S0004"},
]

# list_ecos_codes.py 가 항목코드를 조회해 시트에 적어줄 통계표 목록
ECOS_TABLES_TO_INSPECT = ["817Y002", "404Y015", "404Y014", "901Y009"]
