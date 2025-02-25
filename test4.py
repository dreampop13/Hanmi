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

# 아파트 단지 정보 - 각 단지별 크롤링 간격(분) 설정
complex_ids = {
    101887: {"name": "반포리체", "interval": 17},
    112008: {"name": "반포래미안아이파크", "interval": 19},
    125080: {"name": "디에이치반포라클라스", "interval": 21},
    111687: {"name": "반포써밋", "interval": 18},
    444: {"name": "반포미도1차", "interval": 16},
    445: {"name": "반포미도2차", "interval": 20},
}

# 미리 정의된 다양한 User-Agent 목록
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.70',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1'
]

# 랜덤 User-Agent 생성 함수
def get_random_user_agent():
    return random.choice(USER_AGENTS)

# 쿠키와 헤더를 랜덤화하는 함수
def get_randomized_headers():
    # 기본 쿠키
    cookies = {
        'nhn.realestate.article.rlet_type_cd': 'A01',
        'nhn.realestate.article.trade_type_cd': '""',
        'nhn.realestate.article.ipaddress_city': '1100000000',
        'NAC': f'kfVV{get_random_string(8)}',
        'NACT': str(random.randint(1, 5)),
        '_fwb': f'{get_random_string(12)}.{int(time.time() * 1000)}',
        'landHomeFlashUseYn': 'Y',
        'NNB': f'{get_random_string(12)}',
        'SRT30': str(int(time.time())),
        'SHOW_FIN_BADGE': 'Y',
        'BNB_FINANCE_HOME_TOOLTIP_ESTATE': 'true',
        'SRT5': str(int(time.time())),
        'REALESTATE': datetime.datetime.now().strftime('%a%%20%b%%20%d%%20%Y%%20%H%%3A%M%%3A%S%%20GMT%%2B0900%%20(Korean%%20Standard%%20Time)'),
    }
    
    # 랜덤 User-Agent 생성
    user_agent = get_random_user_agent()
    
    # Authorization 토큰 가져오기 (실제로는 토큰 갱신 로직 필요)
    auth_token = get_auth_token()
    
    headers = {
        'accept': '*/*',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': f'Bearer {auth_token}',
        'priority': 'u=1, i',
        'referer': f'https://new.land.naver.com/complexes/{random.choice(list(complex_ids.keys()))}?ms=37.503762,127.013485,17&a=APT:ABYG:JGC:PRE&e=RETAIL',
        'sec-ch-ua': f'"Not(A:Brand";v="{random.randint(90, 99)}", "Google Chrome";v="{random.randint(100, 134)}", "Chromium";v="{random.randint(100, 134)}"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': user_agent,
    }
    
    return cookies, headers

# 랜덤 문자열 생성 함수
def get_random_string(length):
    import string
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# 토큰 갱신 함수 (실제로는 네이버 로그인 후 토큰을 가져오는 로직이 필요)
def get_auth_token():
    # 이 부분은 실제 구현 필요 - 현재는 하드코딩된 토큰 반환
    # 임의의 토큰 형식 생성 (실제 네이버 토큰 가져오기가 필요)
    # 실제로는 이 토큰이 만료되면 자동으로 갱신하는 로직이 필요합니다
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3NDA0MDczMzEsImV4cCI6MTc0MDQxODEzMX0.dsrTBt6XxqMxUWELrz4LOxkZmeD4e7cmjetg1k8AHqg"

# Function to get data from the API for a specific complex ID and page range with randomized delays
def fetch_data_for_complex(complex_id):
    all_articles = []
    cookies, headers = get_randomized_headers()
    
    # 페이지 수를 랜덤화하여 패턴이 예측되지 않도록 함
    total_pages = random.randint(10, 20)
    
    # 랜덤 순서로 페이지를 가져와 패턴 감지를 어렵게 함
    page_sequence = list(range(1, total_pages + 1))
    random.shuffle(page_sequence)
    
    for page in page_sequence:
        try:
            # 각 요청 사이에 랜덤한 지연 시간 추가 (2-5초)
            delay = random.uniform(2, 5)
            time.sleep(delay)
            
            # 요청 URL에 랜덤 쿼리 파라미터 추가
            random_param = f"&timestamp={int(time.time())}&rand={random.randint(1000, 9999)}"
            url = f'https://new.land.naver.com/api/articles/complex/{complex_id}?realEstateType=APT%3AABYG%3AJGC%3APRE&tradeType=&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount&maxHouseHoldCount&showArticle=false&sameAddressGroup=false&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page={page}&complexNo={complex_id}&buildingNos=&areaNos=&type=list&order=rank{random_param}'
            
            # 매 요청마다 헤더 랜덤화
            cookies, headers = get_randomized_headers()
            response = requests.get(url, cookies=cookies, headers=headers, timeout=10)

            # 응답 상태 코드 확인
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articleList", [])
                if not articles:
                    # 데이터가 없으면 더 이상 페이지를 가져오지 않음
                    break
                all_articles.extend(articles)
                logger.info(f"단지 {complex_id} 페이지 {page}: {len(articles)}개 매물 가져옴")
            elif response.status_code == 429:  # Too Many Requests
                logger.warning(f"단지 {complex_id} 페이지 {page}: 요청이 너무 많습니다. 30분 대기 후 다시 시도합니다.")
                time.sleep(1800)  # 30분 대기
                # 다시 시도
                response = requests.get(url, cookies=cookies, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get("articleList", [])
                    all_articles.extend(articles)
            else:
                logger.warning(f"단지 {complex_id} 페이지 {page} 데이터 가져오기 실패. 상태 코드: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"요청 오류 발생: {e}")
        except ValueError:
            logger.error(f"단지 {complex_id}, 페이지 {page}에 대한 JSON이 아닌 응답.")
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")

    # 크롤링 완료 시간 업데이트
    last_crawled[complex_id] = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
    
    return all_articles

# 백그라운드에서 단지별 데이터 크롤링을 수행하는 함수
def crawl_worker():
    while True:
        try:
            # 크롤링 큐에서 작업 가져오기
            complex_id = crawling_queue.get(timeout=1)
            
            # 상태 업데이트
            status_container.text(f"진행 중: {complex_ids[complex_id]['name']} 데이터 가져오는 중...")
            
            # 데이터 가져오기
            data = fetch_data_for_complex(complex_id)
            
            # 결과 저장
            crawling_results[complex_id] = data
            
            # 작업 완료 표시
            crawling_queue.task_done()
            
            # 상태 업데이트
            status_container.text(f"{complex_ids[complex_id]['name']} 데이터 업데이트 완료 ({len(data)}개 매물)")
            
            # 다음 작업 전에 랜덤 대기 (10-20초)
            time.sleep(random.uniform(10, 20))
            
        except queue.Empty:
            # 큐가 비어있으면 잠시 대기
            time.sleep(1)
        except Exception as e:
            logger.error(f"크롤링 작업 중 오류 발생: {e}")
            time.sleep(5)

# 백그라운드 작업자 시작
crawler_thread = threading.Thread(target=crawl_worker, daemon=True)
crawler_thread.start()

# 크롤링 스케줄러 함수
def schedule_crawling():
    while True:
        current_time = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
        
        for complex_id, info in complex_ids.items():
            # 해당 단지의 마지막 크롤링 시간 확인
            last_time = last_crawled.get(complex_id)
            
            # 마지막 크롤링 시간이 없거나, 설정된 간격보다 오래 지났으면 크롤링 큐에 추가
            if last_time is None or (current_time - last_time).total_seconds() / 60 >= info['interval']:
                if complex_id not in [item for item in list(crawling_queue.queue)]:
                    crawling_queue.put(complex_id)
                    logger.info(f"단지 {info['name']}({complex_id}) 크롤링 작업 예약됨")
        
        # 1분마다 스케줄 확인
        time.sleep(60)

# 크롤링 스케줄러 시작
scheduler_thread = threading.Thread(target=schedule_crawling, daemon=True)
scheduler_thread.start()

# 드롭다운 메뉴를 위한 옵션 생성
options = [info["name"] for info in complex_ids.values()]
options.insert(0, "모든 단지")  # "모든 단지" 옵션 추가

# 드롭다운 메뉴 생성
selected_complex = st.selectbox(
    "아파트 단지 선택",
    options
)

# 크롤링 초기화 버튼
if st.button("데이터 새로고침"):
    # 선택된 단지에 따라 크롤링 작업 예약
    if selected_complex == "모든 단지":
        for complex_id in complex_ids:
            if complex_id not in [item for item in list(crawling_queue.queue)]:
                crawling_queue.put(complex_id)
    else:
        # 선택된 단지 ID 찾기
        selected_id = None
        for complex_id, info in complex_ids.items():
            if info["name"] == selected_complex:
                selected_id = complex_id
                break
        
        if selected_id and selected_id not in [item for item in list(crawling_queue.queue)]:
            crawling_queue.put(selected_id)
    
    st.success("데이터 새로고침이 예약되었습니다. 잠시 기다려주세요.")

# 데이터 저장 기능
if st.button("데이터 저장"):
    if not crawling_results:
        st.warning("저장할 데이터가 없습니다. 먼저 데이터를 가져오세요.")
    else:
        # 각 단지의 데이터를 합쳐서 엑셀 파일로 저장
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for complex_id, data in crawling_results.items():
                if data:
                    df = pd.DataFrame(data)
                    df = df.rename(columns={"realtorName": "부동산", "articleName": "아파트", "tradeTypeName": "거래방식", 
                                          "buildingName": "동", "floorInfo": "층수", "dealOrWarrantPrc": "가격", "areaName": "평형"})
                    df.to_excel(writer, sheet_name=complex_ids[complex_id]["name"][:31], index=False)  # 시트 이름 제한 31자
        
        output.seek(0)
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="엑셀 파일 다운로드",
            data=output,
            file_name=f"부동산_데이터_{now}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# 크롤링 상태 및 시간 정보 표시
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

# 데이터를 표시할 빈 컨테이너 생성
data_container = st.empty()

# 메인 UI 루프
while True:
    # 새로고침 시간 업데이트
    refresh_time.text(f"마지막 UI 업데이트: {display_current_date()}")

    # 선택된 단지에 따라 데이터 표시
    with data_container.container():
        if selected_complex == "모든 단지":
            # 모든 단지 데이터 표시
            for complex_id, data in crawling_results.items():
                if data:
                    df = pd.DataFrame(data)
                    df = df.rename(columns={"realtorName": "부동산", "articleName": "아파트", "tradeTypeName": "거래방식", 
                                          "buildingName": "동", "floorInfo": "층수", "dealOrWarrantPrc": "가격", "areaName": "평형"})
                    df_display = df[["부동산", "아파트", "거래방식", "동", "층수",
                                    "가격", "평형", "direction", "articleConfirmYmd", "articleFeatureDesc",
                                    "tagList", "articleNo", "sameAddrMaxPrc", "sameAddrMinPrc"]]
                    
                    last_update = last_crawled.get(complex_id, "데이터 없음")
                    update_time = last_update.strftime("%Y-%m-%d %H:%M:%S") if isinstance(last_update, datetime.datetime) else last_update
                    
                    st.write(f"### {complex_ids[complex_id]['name']} (마지막 업데이트: {update_time})")
                    st.dataframe(df_display, height=300)  # 각 단지별로 높이 300px 설정
                else:
                    st.write(f"### {complex_ids[complex_id]['name']}: 데이터를 아직 가져오지 않았습니다.")
        else:
            # 선택된 단지 ID 찾기
            selected_id = None
            for complex_id, info in complex_ids.items():
                if info["name"] == selected_complex:
                    selected_id = complex_id
                    break
            
            if selected_id:
                # 선택된 단지의 데이터 표시
                data = crawling_results.get(selected_id, [])
                
                if data:
                    df = pd.DataFrame(data)
                    df = df.rename(columns={"realtorName": "부동산", "articleName": "아파트", "tradeTypeName": "거래방식", 
                                          "buildingName": "동", "floorInfo": "층수", "dealOrWarrantPrc": "가격", "areaName": "평형"})
                    df_display = df[["부동산", "아파트", "거래방식", "동", "층수",
                                    "가격", "평형", "direction", "articleConfirmYmd", "articleFeatureDesc",
                                    "tagList", "articleNo", "sameAddrMaxPrc", "sameAddrMinPrc"]]
                    
                    last_update = last_crawled.get(selected_id, "데이터 없음")
                    update_time = last_update.strftime("%Y-%m-%d %H:%M:%S") if isinstance(last_update, datetime.datetime) else last_update
                    
                    st.write(f"### {selected_complex} (마지막 업데이트: {update_time})")
                    
                    # 단일 단지일 경우 더 큰 높이로 설정하여 스크롤 가능하게 함
                    st.dataframe(df_display, height=900, use_container_width=True)
                    
                    # 데이터 통계 정보 표시
                    st.write(f"총 매물 수: {len(df_display)}개")
                    
                    # 가격 정보가 숫자로 되어 있는지 확인하고, 숫자라면 통계 계산
                    if df_display["가격"].dtype == 'float64' or df_display["가격"].dtype == 'int64':
                        st.write(f"평균 가격: {df_display['가격'].mean():,.0f}만원")
                        st.write(f"최저 가격: {df_display['가격'].min():,.0f}만원")
                        st.write(f"최고 가격: {df_display['가격'].max():,.0f}만원")
                else:
                    st.write(f"### {selected_complex}: 데이터를 아직 가져오지 않았습니다. '데이터 새로고침' 버튼을 눌러주세요.")

    # UI 갱신 간격 (10초)
    time.sleep(10)
