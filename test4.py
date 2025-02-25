import datetime
import time
import random
from zoneinfo import ZoneInfo
import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import threading
import queue
import logging
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 크롤링 상태를 추적하기 위한 글로벌 변수
last_crawled = {}
crawling_queue = queue.Queue()
crawling_results = {}

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
status_container = st.empty()

# 왼쪽 사이드바의 크롤링 상태 탭을 접고 펼치는 토글
show_sidebar = st.sidebar.checkbox("크롤링 상태 보기", value=True)

# 아파트 단지 정보 - 각 단지별 크롤링 간격(분) 설정
complex_ids = {
    101887: {"name": "반포리체", "interval": 17},
    112008: {"name": "반포래미안아이파크", "interval": 19},
    125080: {"name": "디에이치반포라클라스", "interval": 21},
    111687: {"name": "반포써밋", "interval": 18},
    444: {"name": "반포미도1차", "interval": 16},
    445: {"name": "반포미도2차", "interval": 20},
}

# 크롤링 상태 및 시간 정보 표시 (사이드바가 활성화된 경우만)
if show_sidebar:
    st.sidebar.header("크롤링 상태")
    for complex_id, info in complex_ids.items():
        last_time = last_crawled.get(complex_id)
        if last_time:
            time_diff = (datetime.datetime.now(ZoneInfo("Asia/Seoul")) - last_time).total_seconds() / 60
            next_crawl = info["interval"] - time_diff if time_diff < info["interval"] else 0

            status = f"✅ {info['name']}: {last_time.strftime('%H:%M:%S')} 갱신 (다음 갱신까지 약 {next_crawl:.1f}분)"
            if next_crawl <= 0:
                status = f"⏳ {info['name']}: {last_time.strftime('%H:%M:%S')} 갱신 (곧 갱신 예정)"
        else:
            status = f"❌ {info['name']}: 아직 데이터 없음"

        st.sidebar.text(status)

# 드롭다운 메뉴를 위한 옵션 생성
options = [info["name"] for info in complex_ids.values()]
options.insert(0, "모든 단지")  # "모든 단지" 옵션 추가

# 드롭다운 메뉴 생성
selected_complex = st.selectbox(
    "아파트 단지 선택",
    options
)

# 데이터 새로고침 버튼
if st.button("데이터 새로고침"):
    if selected_complex == "모든 단지":
        for complex_id in complex_ids:
            if complex_id not in [item for item in list(crawling_queue.queue)]:
                crawling_queue.put(complex_id)
    else:
        selected_id = next((id for id, info in complex_ids.items() if info["name"] == selected_complex), None)
        if selected_id and selected_id not in [item for item in list(crawling_queue.queue)]:
            crawling_queue.put(selected_id)

    st.success("데이터 새로고침이 예약되었습니다. 잠시 기다려주세요.")

# 데이터를 표시할 빈 컨테이너 생성
data_container = st.empty()

# 메인 UI 첫 로딩 시 바로 데이터 표시
def initial_load():
    for complex_id in complex_ids:
        if complex_id not in [item for item in list(crawling_queue.queue)]:
            crawling_queue.put(complex_id)

initial_load()

# 메인 UI 루프
while True:
    refresh_time.text(f"마지막 UI 업데이트: {display_current_date()}")

    with data_container.container():
        if selected_complex == "모든 단지":
            for complex_id, data in crawling_results.items():
                if data:
                    df = pd.DataFrame(data)
                    df = df.rename(columns={"realtorName": "부동산", "articleName": "아파트", "tradeTypeName": "거래방식", "buildingName": "동", "floorInfo": "층수", "dealOrWarrantPrc": "가격", "areaName": "평형"})
                    st.write(f"### {complex_ids[complex_id]['name']}")
                    st.dataframe(df)
        else:
            selected_id = next((id for id, info in complex_ids.items() if info["name"] == selected_complex), None)
            if selected_id and crawling_results.get(selected_id):
                df = pd.DataFrame(crawling_results[selected_id])
                df = df.rename(columns={"realtorName": "부동산", "articleName": "아파트", "tradeTypeName": "거래방식", "buildingName": "동", "floorInfo": "층수", "dealOrWarrantPrc": "가격", "areaName": "평형"})
                st.dataframe(df)

    time.sleep(60)
