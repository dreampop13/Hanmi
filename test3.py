import streamlit as st
import requests
import pandas as pd

PASSWORD = '5261'

# Streamlit page setup
st.set_page_config(page_title="한미부동산", layout="wide")

# 로그인 상태 추적 (session_state)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# 로그인 상태에 따른 동작
if not st.session_state.logged_in:
    # 비밀번호 입력창을 보이게 하고
    st.title("한미부동산")
    st.markdown("로그인이 필요합니다.")
    password = st.text_input('비밀번호를 입력하세요', type='password')

    # 비밀번호 검증 후 로그인 상태 업데이트
    if password == PASSWORD:
        st.session_state.logged_in = True
        st.session_state.password = password  # 비밀번호 상태를 session_state에 저장
        st.rerun()  # 최신 Streamlit 버전에서는 rerun() 사용
    elif password != '' and password != PASSWORD:
        st.error('비밀번호가 틀렸습니다. 다시 시도해 주세요.')

# 로그인 성공 후 페이지 로딩
else:  # 여기서 else를 사용하여 if-else 구조를 명확하게 합니다
    # 로그인되었을 때만 메인 콘텐츠 표시
    st.title("한미부동산")
    st.markdown("네이버 부동산의 실시간 매물 정보를 제공합니다. Control + R 키를 눌러 새로고침 하세요!")
    
    # Define the cookies and headers as provided
    cookies = {
        'nhn.realestate.article.rlet_type_cd': 'A01',
        'nhn.realestate.article.trade_type_cd': '""',
        'nhn.realestate.article.ipaddress_city': '1100000000',
        'NAC': 'kfVVDAh6umRQB',
        'NACT': '1',
        '_fwb': '164LrqEDbfsJMHWdPyHYrF6.1740403987456',
        'landHomeFlashUseYn': 'Y',
        'NNB': 'BFLKCVA7OW6GO',
        'SRT30': '1740403999',
        'SHOW_FIN_BADGE': 'Y',
        'BNB_FINANCE_HOME_TOOLTIP_ESTATE': 'true',
        '_fwb': '164LrqEDbfsJMHWdPyHYrF6.1740403987456',
        'SRT5': '1740407323',
        'REALESTATE': 'Mon%20Feb%2024%202025%2023%3A28%3A51%20GMT%2B0900%20(Korean%20Standard%20Time)',
        'BUC': 'FgEKqfdHd3tt5i1p64yyapwHH6Vu9LEJZmMTeGZRzo8=',
    }

    headers = {
        'accept': '*/*',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3NDA0MDczMzEsImV4cCI6MTc0MDQxODEzMX0.dsrTBt6XxqMxUWELrz4LOxkZmeD4e7cmjetg1k8AHqg',
        'priority': 'u=1, i',
        'referer': 'https://new.land.naver.com/complexes/101887?ms=37.503762,127.013485,17&a=APT:ABYG:JGC:PRE&e=RETAIL',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    }

    # 아파트 단지 정보
    complex_ids = {
        101887: "반포리체",
        112008: "반포래미안아이파크",
        125080: "디에이치반포라클라스",
        111687: "반포써밋",
        444: "반포미도1차",
        445: "반포미도2차",
    }
    
    # Function to get data from the API for a specific complex ID and page range
    @st.cache_data
    def fetch_data_for_complex(complex_id):
        all_articles = []
        for page in range(1, 30):  # Pages 1 to 30
            try:
                # Construct the URL with the current complex_id
                url = f'https://new.land.naver.com/api/articles/complex/{complex_id}?realEstateType=APT%3AABYG%3AJGC%3APRE&tradeType=&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount&maxHouseHoldCount&showArticle=false&sameAddressGroup=false&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page={page}&complexNo={complex_id}&buildingNos=&areaNos=&type=list&order=rank'
                
                # Make the request for the specific page
                response = requests.get(url, cookies=cookies, headers=headers)

                # Verify response is valid JSON
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get("articleList", [])
                    all_articles.extend(articles)
                else:
                    st.warning(f"Failed to retrieve data for complex {complex_id}, page {page}. Status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"An error occurred: {e}")
            except ValueError:
                st.error(f"Non-JSON response for complex {complex_id}, page {page}.")

        return all_articles

    # 드롭다운 메뉴를 위한 옵션 생성
    options = list(complex_ids.values())
    options.insert(0, "모든 단지")  # "모든 단지" 옵션 추가
    
    # 드롭다운 메뉴 생성
    selected_complex = st.selectbox(
        "아파트 단지 선택",
        options
    )
    
    # 선택된 단지에 따라 데이터 표시
    if selected_complex == "모든 단지":
        # 모든 단지 데이터 가져오기
        complex_data = {}
        for complex_id in complex_ids:
            complex_data[complex_id] = fetch_data_for_complex(complex_id)
            
        # 모든 단지 데이터 표시
        for complex_id, data in complex_data.items():
            if data:
                df = pd.DataFrame(data)
                df = df.rename(columns={"realtorName": "부동산", "articleName": "아파트", "tradeTypeName": "거래방식", "buildingName": "동", "floorInfo": "층수", "dealOrWarrantPrc": "가격", "areaName": "평형" })
                df_display = df[["부동산", "아파트", "거래방식", "동", "층수",
                                "가격", "평형", "direction", "articleConfirmYmd", "articleFeatureDesc",
                                "tagList", "articleNo", "sameAddrMaxPrc", "sameAddrMinPrc"]]
                
                st.write(f"### {complex_ids[complex_id]}")
                st.dataframe(df_display, height=300)  # 각 단지별로 높이 300px 설정
            else:
                st.write(f"No data available for {complex_ids[complex_id]}")
    else:
        # 선택된 단지 ID 찾기
        selected_id = None
        for complex_id, name in complex_ids.items():
            if name == selected_complex:
                selected_id = complex_id
                break
        
        if selected_id:
            # 선택된 단지의 데이터만 가져오기
            data = fetch_data_for_complex(selected_id)
            
            if data:
                df = pd.DataFrame(data)
                df = df.rename(columns={"realtorName": "부동산", "articleName": "아파트", "tradeTypeName": "거래방식", "buildingName": "동", "floorInfo": "층수", "dealOrWarrantPrc": "가격", "areaName": "평형" })
                df_display = df[["부동산", "아파트", "거래방식", "동", "층수",
                                "가격", "평형", "direction", "articleConfirmYmd", "articleFeatureDesc",
                                "tagList", "articleNo", "sameAddrMaxPrc", "sameAddrMinPrc"]]
                
                st.write(f"### {selected_complex}")
                
                # 단일 단지일 경우 더 큰 높이로 설정하여 스크롤 가능하게 함
                st.dataframe(df_display, height=600, use_container_width=True)
                
                # 데이터 통계 정보 표시
                st.write(f"총 매물 수: {len(df_display)}개")
                
                # 가격 정보가 숫자로 되어 있는지 확인하고, 숫자라면 통계 계산
                if df_display["가격"].dtype == 'float64' or df_display["가격"].dtype == 'int64':
                    st.write(f"평균 가격: {df_display['가격'].mean():,.0f}만원")
                    st.write(f"최저 가격: {df_display['가격'].min():,.0f}만원")
                    st.write(f"최고 가격: {df_display['가격'].max():,.0f}만원")
            else:
                st.write(f"No data available for {selected_complex}")