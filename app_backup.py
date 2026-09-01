import streamlit as st
from google import genai

st.set_page_config(
    page_title="업무지원 AI 도우미",
    page_icon="🤖",
    layout="centered"
)

st.title("업무지원 AI 도우미")
st.caption("Gemini API를 활용한 교육용 AI 앱")

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

user_input = st.text_area(
    "업무 요청 내용을 입력하세요.",
    height=150,
    placeholder="예: VPN 접속이 되지 않아 외부에서 업무시스템에 접속할 수 없습니다."
)

if st.button("AI 분석"):

    if not user_input.strip():
        st.warning("업무 요청 내용을 입력해주세요.")

    else:
        prompt = f"""
당신은 IT 업무지원 Agent입니다.

다음 요청을 단계적으로 처리하세요.

[입력]
{user_input}

다음 형식으로 답하세요.

1. 요청 요약
2. 예상 업무분류
3. 긴급도
4. 추가 확인이 필요한 정보
5. 담당자가 해야 할 다음 행동

중요:
- 입력에 없는 원인은 추측하지 마세요.
- 실제 장애 원인을 확정하지 마세요.
- 확인할 수 없는 사항은 '확인 필요'라고 표시하세요.
"""

        with st.spinner("AI가 분석하고 있습니다..."):

            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )

        st.subheader("AI 분석 결과")
        st.write(response.text)
