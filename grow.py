import streamlit as st
import time
from datetime import datetime

# --- 초기 설정 ---
# 앱 제목 및 레이아웃 설정
st.set_page_config(page_title="새마을금고 파랑새 키우기", layout="wide", page_icon="🐦")

# --- 세션 상태 초기화 ---
# 새의 상태를 저장하기 위한 세션 상태
if 'bird_state' not in st.session_state:
    st.session_state.bird_state = {
        'selected_character': '1', # 메인 이미지의 '1. 건설가 새'로 시작
        'name': '새마을금고 작업자 파랑새',
        'fullness': 80,       # 포만감 (0~100)
        'happiness': 80,      # 행복도 (0~100)
        'cleanliness': 100,   # 청결도 (0~100)
        'level': 1,           # 레벨
        'xp': 0,             # 경험치
        'is_alive': True,      # 생존 여부
        'start_time': datetime.now(), # 시작 시간
        'last_tick': datetime.now(),   # 마지막 상태 업데이트 시간
        'current_image': 'image_0_worker.png' # 기본 이미지 (실제 이미지 경로 필요)
    }

# 캐릭터별 정보 (메인 이미지의 번호와 매칭)
character_data = {
    '1': {'name': '작업자 파랑새', 'image_base': 'image_0_worker'}, # 실제 경로 필요
    '2': {'name': '할머니 파랑새', 'image_base': 'image_0_grandma'},
    '3': {'name': '요리사 파랑새', 'image_base': 'image_0_chef'},
    '4': {'name': '거대 파랑새', 'image_base': 'image_0_giant'},
    '5': {'name': '농부 파랑새', 'image_base': 'image_0_farmer'},
    '6': {'name': '학자 파랑새', 'image_base': 'image_0_scholar'},
    '7': {'name': '예술가 파랑새', 'image_base': 'image_0_artist'},
    '8': {'name': '비행사 파랑새', 'image_base': 'image_0_pilot'},
    '9': {'name': '집배원 파랑새', 'image_base': 'image_0_messenger'},
    '10': {'name': '신사 파랑새', 'image_base': 'image_0_gentleman'},
    '11': {'name': '아기 파랑새', 'image_base': 'image_0_baby'},
    '12': {'name': '우주 비행사 파랑새', 'image_base': 'image_0_astro'},
}

# --- 게임 로직 함수 ---

def feed():
    """먹이 주기: 포만감 증가, 경험치 소폭 증가"""
    if st.session_state.bird_state['is_alive']:
        st.session_state.bird_state['fullness'] = min(100, st.session_state.bird_state['fullness'] + 20)
        st.session_state.bird_state['xp'] += 5
        st.sidebar.success(f"{st.session_state.bird_state['name']}가 밥을 맛있게 먹었습니다!")
        update_character_image('happy')

def play():
    """놀아 주기: 행복도 증가, 포만감 및 청결도 감소, 경험치 증가"""
    if st.session_state.bird_state['is_alive']:
        st.session_state.bird_state['happiness'] = min(100, st.session_state.bird_state['happiness'] + 15)
        st.session_state.bird_state['fullness'] = max(0, st.session_state.bird_state['fullness'] - 10)
        st.session_state.bird_state['cleanliness'] = max(0, st.session_state.bird_state['cleanliness'] - 5)
        st.session_state.bird_state['xp'] += 15
        st.sidebar.info(f"{st.session_state.bird_state['name']}와 함께 즐거운 시간을 보냈습니다!")
        update_character_image('happy')

def clean():
    """청소하기: 청결도 증가, 경험치 소폭 증가"""
    if st.session_state.bird_state['is_alive']:
        st.session_state.bird_state['cleanliness'] = 100
        st.session_state.bird_state['xp'] += 10
        st.sidebar.warning(f"{st.session_state.bird_state['name']}의 둥지가 깨끗해졌습니다!")
        update_character_image('neutral')

def check_level_up():
    """경험치에 따른 레벨 업 체크"""
    current_level = st.session_state.bird_state['level']
    xp_needed = current_level * 100
    if st.session_state.bird_state['xp'] >= xp_needed:
        st.session_state.bird_state['level'] += 1
        st.session_state.bird_state['xp'] = st.session_state.bird_state['xp'] - xp_needed
        st.balloons()
        st.sidebar.success(f"🎉 축하합니다! {st.session_state.bird_state['name']}가 레벨 {st.session_state.bird_state['level']}(으)로 성장했습니다!")

def decay_stats():
    """시간 경과에 따른 상태 감소"""
    current_time = datetime.now()
    time_delta = current_time - st.session_state.bird_state['last_tick']
    
    # 5초마다 상태 감소
    if time_delta.total_seconds() > 5:
        decay_amount = 2
        st.session_state.bird_state['fullness'] = max(0, st.session_state.bird_state['fullness'] - decay_amount)
        st.session_state.bird_state['happiness'] = max(0, st.session_state.bird_state['happiness'] - decay_amount)
        # 청결도는 행복도가 낮을 때 더 빨리 감소
        cleanliness_decay = decay_amount + (1 if st.session_state.bird_state['happiness'] < 30 else 0)
        st.session_state.bird_state['cleanliness'] = max(0, st.session_state.bird_state['cleanliness'] - cleanliness_decay)
        
        st.session_state.bird_state['last_tick'] = current_time
        
        # 사망 체크
        if st.session_state.bird_state['fullness'] <= 0 or \
           st.session_state.bird_state['happiness'] <= 0 or \
           st.session_state.bird_state['cleanliness'] <= 0:
            st.session_state.bird_state['is_alive'] = False
            update_character_image('sad')
            st.sidebar.error(f"{st.session_state.bird_state['name']}가 그만... 다시 시작하려면 페이지를 새로고침하세요.")
        else:
            # 상태에 따른 이미지 업데이트
            if st.session_state.bird_state['fullness'] < 20 or st.session_state.bird_state['happiness'] < 20:
                update_character_image('sad')
            elif st.session_state.bird_state['fullness'] > 80 and st.session_state.bird_state['happiness'] > 80:
                update_character_image('happy')
            else:
                update_character_image('neutral')

def update_character_image(emotion):
    """상태에 따른 캐릭터 이미지 경로 업데이트 (실제 이미지 경로 필요)"""
    char_key = st.session_state.bird_state['selected_character']
    base_path = character_data[char_key]['image_base']
    # 예: 'image_0_worker_happy.png'와 같은 형식으로 매칭
    # 실제 사용 시 해당 파일들이 같은 폴더에 있어야 함
    st.session_state.bird_state['current_image'] = f"{base_path}_{emotion}.png"

def restart_game():
    """게임 초기화"""
    del st.session_state.bird_state
    st.rerun()

# --- 스트림릿 UI 구성 ---

# 상단: 메인 UI 이미지 및 안내 문구
st.title("새마을금고 파랑새 키우기 - 당신의 파랑새 마을")
st.image("image_1.png", use_container_width=True) # 생성된 메인 UI 이미지

if 'first_run' not in st.session_state:
    st.info("안녕하세요! 새마을금고 파랑새 마을에 오신 것을 환영합니다.\n위의 이미지에서 키우고 싶은 파랑새의 번호를 확인하세요.\n사이드바에서 번호를 선택하여 게임을 시작할 수 있습니다.")
    st.session_state.first_run = False

# 사이드바: 캐릭터 선택 및 행동
with st.sidebar:
    st.header("파랑새 정보 및 행동")
    
    if st.session_state.bird_state['is_alive']:
        # 캐릭터 선택 드롭다운 (이미지의 번호와 매칭)
        # 실제로는 번호로만 연결하고, 이름은 표시
        char_options = [f"{k}. {v['name']}" for k, v in character_data.items()]
        selected_option = st.selectbox(
            "당신의 파랑새를 선택하세요", 
            char_options, 
            index=int(st.session_state.bird_state['selected_character']) - 1,
            key='character_select_sidebar'
        )
        
        # 선택된 번호 업데이트
        new_char_key = selected_option.split('.')[0]
        if new_char_key != st.session_state.bird_state['selected_character']:
            st.session_state.bird_state['selected_character'] = new_char_key
            st.session_state.bird_state['name'] = character_data[new_char_key]['name']
            update_character_image('neutral')
            st.rerun() # 캐릭터 변경 후 앱 재실행하여 이미지 업데이트

        # 행동 버튼
        st.subheader("행동")
        col1, col2, col3 = st.columns(3)
        with col1: st.button("🍴 먹이 주기", on_click=feed, use_container_width=True)
        with col2: st.button("🧸 놀아 주기", on_click=play, use_container_width=True)
        with col3: st.button("🧹 청소하기", on_click=clean, use_container_width=True)
        
        st.divider()
        
        if st.button("정보 확인", use_container_width=True):
             st.info(f"{st.session_state.bird_state['name']}\n레벨: {st.session_state.bird_state['level']}\n경험치: {st.session_state.bird_state['xp']}")

    else:
        st.subheader("게임 오버")
        st.button("다시 시작", on_click=restart_game, use_container_width=True)

# 메인 화면: 캐릭터 상태 및 이미지
col1, col2 = st.columns([1, 2])

with col1:
    st.header(f"{st.session_state.bird_state['name']}")
    
    # 상태 바 표시
    st.write("🍽️ 포만감")
    st.progress(st.session_state.bird_state['fullness'] / 100, text=f"{st.session_state.bird_state['fullness']}%")
    
    st.write("💖 행복도")
    st.progress(st.session_state.bird_state['happiness'] / 100, text=f"{st.session_state.bird_state['happiness']}%")
    
    st.write("🧹 청결도")
    st.progress(st.session_state.bird_state['cleanliness'] / 100, text=f"{st.session_state.bird_state['cleanliness']}%")
    
    st.divider()
    
    # 성장 정보
    st.subheader(f"레벨 {st.session_state.bird_state['level']}")
    xp_needed = st.session_state.bird_state['level'] * 100
    st.write(f"경험치: {st.session_state.bird_state['xp']} / {xp_needed}")
    st.progress(st.session_state.bird_state['xp'] / xp_needed, text=f"{(st.session_state.bird_state['xp'] / xp_needed * 100):.1f}%")

with col2:
    # 캐릭터 이미지 표시 (실제 이미지 경로가 필요함)
    # 이미지 0의 '1. 건설가 새' 이미지를 기본으로 사용한다고 가정
    # 실제로는 'image_0_worker_neutral.png' 등의 이미지를 직접 준비해야 함
    st.image(st.session_state.bird_state['current_image'], use_container_width=True) # 선택된 캐릭터 이미지

# 시간에
