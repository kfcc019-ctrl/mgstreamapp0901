import streamlit as st
import pandas as pd
from google import genai
from google.genai import types


# =========================================================
# 1. Streamlit 설정
# =========================================================

st.set_page_config(
    page_title="업무지원 AI Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("업무지원 AI Agent")
st.caption(
    "사용자의 요청을 판단하여 필요한 데이터 분석 Tool을 선택하는 교육용 AI Agent"
)


# =========================================================
# 2. Gemini 설정
# =========================================================

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

MODEL_NAME = "gemini-3-flash-preview"


# =========================================================
# 3. CSV 업로드
# =========================================================

uploaded_file = st.file_uploader(
    "업무지원 CSV 파일을 업로드하세요.",
    type=["csv"]
)


if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    st.subheader("1. 데이터 미리보기")

    st.dataframe(
        df,
        use_container_width=True
    )


    # =====================================================
    # 4. Agent가 사용할 Tool 함수
    # =====================================================

    def calculate_kpi():
        """
        전체 요청, 완료, 미완료, 완료율,
        긴급 미완료 건수를 계산합니다.
        """

        total_count = len(df)

        completed_count = (
            df["status"]
            .astype(str)
            .str.strip()
            .eq("완료")
            .sum()
        )

        incomplete_count = (
            total_count - completed_count
        )

        completion_rate = (
            completed_count / total_count * 100
            if total_count > 0
            else 0
        )

        urgent_incomplete_count = len(
            df[
                (df["urgency"].astype(str).str.strip() == "상")
                &
                (df["status"].astype(str).str.strip() != "완료")
            ]
        )

        return {
            "전체 요청": int(total_count),
            "완료": int(completed_count),
            "미완료": int(incomplete_count),
            "완료율": round(completion_rate, 1),
            "긴급 미완료": int(urgent_incomplete_count)
        }


    def get_category_counts():
        """
        업무분류별 요청 건수를 계산합니다.
        """

        counts = (
            df["category"]
            .astype(str)
            .str.strip()
            .value_counts()
            .to_dict()
        )

        return {
            str(category): int(count)
            for category, count in counts.items()
        }


    def find_urgent_incomplete():
        """
        긴급도가 '상'이고 아직 완료되지 않은 요청을 찾습니다.
        """

        urgent_df = df[
            (df["urgency"].astype(str).str.strip() == "상")
            &
            (df["status"].astype(str).str.strip() != "완료")
        ]

        if urgent_df.empty:
            return {
                "건수": 0,
                "요청": []
            }

        # 너무 많은 데이터를 LLM에 보내지 않도록 제한
        result_df = urgent_df.head(20)

        return {
            "건수": len(urgent_df),
            "요청": result_df.to_dict(
                orient="records"
            )
        }


    # =====================================================
    # 5. Tool 선언
    # =====================================================

    calculate_kpi_declaration = {
        "name": "calculate_kpi",
        "description": (
            "업무지원 데이터의 전체 요청, 완료, 미완료, "
            "완료율, 긴급 미완료 건수를 계산합니다."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }


    get_category_counts_declaration = {
        "name": "get_category_counts",
        "description": (
            "업무지원 데이터에서 업무분류별 요청 건수를 계산합니다."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }


    find_urgent_incomplete_declaration = {
        "name": "find_urgent_incomplete",
        "description": (
            "긴급도가 '상'이면서 상태가 완료가 아닌 "
            "긴급 미완료 요청을 찾습니다."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }


    # =====================================================
    # 6. Tool 설정
    # =====================================================

    tools = types.Tool(
        function_declarations=[
            calculate_kpi_declaration,
            get_category_counts_declaration,
            find_urgent_incomplete_declaration
        ]
    )


    config = types.GenerateContentConfig(
        tools=[tools],
        system_instruction="""
당신은 교육용 업무지원 데이터 분석 AI Agent입니다.

사용자의 요청을 분석하고,
필요한 경우 제공된 Tool을 선택하여 사용하세요.

Tool 사용 원칙:

1. 요청건수, 완료율 등 수치가 필요한 경우
   calculate_kpi를 사용하세요.

2. 업무분류별 현황이 필요한 경우
   get_category_counts를 사용하세요.

3. 긴급하게 확인해야 할 요청이 필요한 경우
   find_urgent_incomplete를 사용하세요.

4. 데이터에 없는 원인을 추측하지 마세요.

5. 확인할 수 없는 내용은
   '확인 필요'라고 표시하세요.

6. 계산할 수 있는 수치를 임의로 추정하지 말고
   반드시 Tool 결과를 사용하세요.

7. 긴급 미완료 요청이 존재한다고 해서
   장애 원인을 확정하지 마세요.

8. 최종 답변은 금융기관 또는 공공기관의
   내부 업무보고에 적합한 문체로 작성하세요.
"""
    )


    # =====================================================
    # 7. Agent 화면
    # =====================================================

    st.subheader("2. AI Agent에게 업무 요청")

    user_request = st.text_area(
        "업무 요청을 입력하세요.",
        placeholder=(
            "예: 현재 업무지원 현황을 분석하고 "
            "긴급하게 확인해야 할 사항이 있으면 알려줘."
        ),
        height=120
    )


    if st.button(
        "🤖 Agent 실행",
        use_container_width=True
    ):

        if not user_request.strip():

            st.warning(
                "Agent에게 요청할 내용을 입력하세요."
            )

        else:

            with st.spinner(
                "AI Agent가 필요한 작업을 판단하고 있습니다..."
            ):

                # =========================================
                # 1차 Gemini 호출
                # 어떤 Tool이 필요한지 판단
                # =========================================

                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=user_request,
                    config=config
                )


                # =========================================
                # 모델이 요청한 Function Call 확인
                # =========================================

                function_calls = response.function_calls


                if not function_calls:

                    # Tool이 필요하지 않은 경우
                    st.subheader("3. Agent 답변")

                    st.markdown(
                        response.text
                    )

                else:

                    contents = [
                        types.Content(
                            role="user",
                            parts=[
                                types.Part(
                                    text=user_request
                                )
                            ]
                        ),
                        response.candidates[0].content
                    ]


                    # =====================================
                    # 여러 Tool 호출 처리
                    # =====================================

                    executed_tools = []

                    for function_call in function_calls:

                        function_name = (
                            function_call.name
                        )


                        # ---------------------------------
                        # Tool 실행
                        # ---------------------------------

                        if function_name == "calculate_kpi":

                            result = calculate_kpi()


                        elif function_name == "get_category_counts":

                            result = get_category_counts()


                        elif function_name == "find_urgent_incomplete":

                            result = find_urgent_incomplete()


                        else:

                            result = {
                                "error":
                                f"알 수 없는 Tool: {function_name}"
                            }


                        executed_tools.append(
                            {
                                "tool": function_name,
                                "result": result
                            }
                        )


                        # ---------------------------------
                        # Tool 결과를 Gemini에게 전달
                        # ---------------------------------

                        function_response_part = (
                            types.Part.from_function_response(
                                name=function_name,
                                response={
                                    "result": result
                                }
                            )
                        )


                        contents.append(
                            types.Content(
                                role="user",
                                parts=[
                                    function_response_part
                                ]
                            )
                        )


                    # =====================================
                    # 2차 Gemini 호출
                    # Tool 결과를 바탕으로 최종 답변 생성
                    # =====================================

                    final_response = (
                        client.models.generate_content(
                            model=MODEL_NAME,
                            contents=contents,
                            config=config
                        )
                    )


                    # =====================================
                    # 결과 출력
                    # =====================================

                    st.subheader("3. Agent 실행 결과")


                    with st.expander(
                        "Agent가 사용한 Tool 확인"
                    ):

                        for item in executed_tools:

                            st.markdown(
                                f"**{item['tool']}**"
                            )

                            st.json(
                                item["result"]
                            )


                    st.subheader("4. Agent 최종 답변")

                    st.markdown(
                        final_response.text
                    )
