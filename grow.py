import streamlit as st
import time
from datetime import datetime

st.set_page_config(page_title="새마을금고 파랑새 키우기", layout="wide", page_icon="🐦")

# 파랑새 캐릭터 목록 (별도 이미지 파일 없이 작동하도록 이모지 적용)
CHARACTERS = {
    '1': {'name': '건설가 파랑새', 'emoji': '👷‍♂️🐦', 'status': '뚝딱뚝딱 집을 짓는 중!'},
    '2': {'name': '할머니 파랑새', 'emoji': '👵🐦', 'status': '따뜻한 모이를 챙겨주는 중!'},
    '3': {'name': '학자 파랑새', 'emoji': '🎓🐦', 'status': '새마을금고 금융 공부 중!'},
    '4': {'name': '먹방 파랑새', 'emoji': '🧺🐦', 'status': '맛있는 도시락을 먹는 중!'},
    '5': {'name': '정장 파랑새', 'emoji': '👔🐦', 'status': '고객님을 맞이하는 중!'},
    '6': {'name': '농부 파랑새', 'emoji': '🧑‍🌾🐦', 'status': '열심히 밭을 고르는 중!'},
    '7': {'name': '예술가 파랑새', 'emoji': '🎨🐦', 'status': '파랑새 마을 그림 그리는 중!'},
    '8': {'name': '우주 파랑새', 'emoji': '🚀🐦', 'status': '우주 탐사를 준비하는 중!'}
}

# 세션 상태 초기화
if 'bird' not in st.session_state:
    st.session_state.bird = {
        'char_id': '1',
        'fullness': 80,
        'happiness': 80,
        'cleanliness': 100,
        'level': 1,
        'xp': 0,
        'is_alive': True,
        'last_tick': datetime.now()
    }

# 행동 함수 정의
def feed():
    if st.session_state.bird['is_alive']:
        st.session_state.bird['fullness'] = min(100, st.session_state.bird['fullness'] + 25)
        st.session_state.bird['xp'] += 10
        st.toast("😋 맛있게 밥을 먹었습니다!")

def play():
    if st.session_state.bird['is_alive']:
        st.session_state.bird['happiness'] = min(100, st.session_state.bird['happiness'] + 20)
        st.session_state.bird['fullness'] = max(0, st.session_state.bird['fullness'] - 10)
        st.session_state.bird['cleanliness'] = max(0, st.session_state.bird['cleanliness'] - 10)
        st.session_state.bird['xp'] += 15
        st.toast("🎮 신나게 놀았습니다!")

def clean():
    if st.session_state.bird['is_alive']:
        st.session_state.bird['cleanliness'] = 100
        st.session_state.bird['xp'] += 5
        st.toast("🧹 둥지를 깨끗하게 청소했습니다!")

def restart():
    st.session_state.bird = {
        'char_id': '1',
        'fullness': 80,
        'happiness': 80,
        'cleanliness': 100,
        'level': 1,
        'xp': 0,
        'is_alive': True,
        'last_tick': datetime.now()
    }

# 수치 감소 로직 (시간 경과)
now = datetime.now()
elapsed = (now - st.session_state.bird['last_tick']).total_seconds()
if elapsed > 4: # 4초마다 수치 감소
    st.session_state.bird['fullness'] = max(0, st.session_state.bird['fullness'] - 3)
    st.session_state.bird['happiness'] = max(0, st.session_state.bird['happiness'] - 3)
    st.session_state.bird['cleanliness'] = max(0, st.session_state.bird['cleanliness'] - 2)
    st.session_state.bird['last_tick'] = now

    if st.session_state.bird['fullness'] <= 0 or st.session_state.bird['happiness'] <= 0:
        st.session_state.bird['is_alive'] = False

# 레벨업 체크
if st.session_state.bird['xp'] >= st.session_state.bird['level'] * 50:
    st.session_state.bird['level'] += 1
    st.balloons()
    st.toast(f"🎉 레벨 업! 현재 레벨: {st.session_state.bird['level']}")

# UI 레이아웃
st.title("🐦 새마을금고 파랑새 키우기")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("⚙️ 파랑새 선택 및 관리")
    
    selected_id = st.selectbox(
        "키울 파랑새 캐릭터를 고르세요:",
        options=list(CHARACTERS.keys()),
        format_func=lambda x: f"{x}. {CHARACTERS[x]['name']}"
    )
    st.session_state.bird['char_id'] = selected_id
    current_bird = CHARACTERS[selected_id]

    st.markdown("---")
    st.write("**돌보기 버튼**")
    
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        st.button("🍴 먹이주기", on_click=feed, disabled=not st.session_state.bird['is_alive'], use_container_width=True)
    with btn_col2:
        st.button("🧸 놀아주기", on_click=play, disabled=not st.session_state.bird['is_alive'], use_container_width=True)
    with btn_col3:
        st.button("🧹 청소하기", on_click=clean, disabled=not st.session_state.bird['is_alive'], use_container_width=True)

    if not st.session_state.bird['is_alive']:
        st.error("파랑새가 너무 배고프거나 심심해서 잠에 들었습니다...")
        st.button("🔄 다시 키우기", on_click=restart, use_container_width=True)

with col2:
    st.subheader(f"{current_bird['name']} (Lv.{st.session_state.bird['level']})")
    
    # 캐릭터 화면 구현 (이모지 기반)
    display_emoji = current_bird['emoji'] if st.session_state.bird['is_alive'] else "🪦"
    st.markdown(
        f"""
        <div style="background-color: #EBF5FF; border-radius: 20px; padding: 40px; text-align: center; border: 2px solid #0066CC;">
            <h1 style="font-size: 90px; margin: 0;">{display_emoji}</h1>
            <p style="color: #0066CC; font-weight: bold; margin-top: 10px;">{current_bird['status'] if st.session_state.bird['is_alive'] else '게임 오버'}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.write("")
    st.write("🍽️ **포만감**")
    st.progress(st.session_state.bird['fullness'] / 100)

    st.write("💖 **행복도**")
    st.progress(st.session_state.bird['happiness'] / 100)

    st.write("🧹 **청결도**")
    st.progress(st.session_state.bird['cleanliness'] / 100)

    st.write(f"⭐ **경험치**: {st.session_state.bird['xp']} / {st.session_state.bird['level'] * 50}")

# 실시간 감수 반영을 위한 자동 새로고침
if st.session_state.bird['is_alive']:
    time.sleep(2)
    st.rerun()
