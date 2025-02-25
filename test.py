import datetime
from zoneinfo import ZoneInfo
import time
import streamlit as st
import requests
import pandas as pd
from io import BytesIO

# Function to display current date and time in KST
def display_current_date():
    return datetime.datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

# Streamlit page setup
st.set_page_config(page_title="한미부동산", layout="wide")

# 로그인 체크 없이 바로 메인 콘텐츠 표시
st.title("한미부동산")
st.markdown("<small style='color: #666;'>네이버 부동산의 실시간 매물 정보를 제공합니다.</small>", unsafe_allow_html=True)

# 새로고침 시간을 표시할 컨테이너
refresh_time = st.empty()

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
def fetch_data_for_complex(complex_id):
    all_articles = []
    for page in range(1, 25):  # Pages 1 to 30
        try:
            url = f'https://new.land.naver.com/api/articles/complex/{complex_id}?realEstateType=APT%3AABYG%3AJGC%3APRE&tradeType=&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount&maxHouseHoldCount&showArticle=false&sameAddressGroup=false&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page={page}&complexNo={complex_id}&buildingNos=&areaNos=&type=list&order=rank'
            
            response = requests.get(url, cookies=cookies, headers=headers)

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

# 실시간 업데이트 루프
while True:
    refresh_time.text(f"마지막 업데이트: {display_current_date()}")
    time.sleep(300)
