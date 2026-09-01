
import streamlit as st
import pandas as pd
from google import genai
from google.genai import types


# =========================================================
# 1. Streamlit ������
# =========================================================

st.set_page_config(
    page_title="������������ AI Agent",
    page_icon="����",
    layout="wide"
)

st.title("������������ AI Agent")
st.caption(
    "������������ ��������� ������������ ��������� ��������� ������ Tool��� ������������ ��������� AI Agent"
)


# =========================================================
# 2. Gemini ������
# =========================================================

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

MODEL_NAME = "gemini-3-flash-preview"


# =========================================================
# 3. CSV ���������
# =========================================================

uploaded_file = st.file_uploader(
    "������������ CSV ��������� ������������������.",
    type=["csv"]
)


if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    st.subheader("1. ��������� ������������")

    st.dataframe(
        df,
        use_container_width=True
    )


    # =====================================================
    # 4. Agent��� ��������� Tool ������
    # =====================================================

    def calculate_kpi():
        """
        ������ ������, ������, ���������, ���������,
        ������ ��������� ��������� ���������������.
        """

        total_count = len(df)

        completed_count = (
            df["status"]
            .astype(str)
            .str.strip()
            .eq("������")
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
                (df["urgency"].astype(str).str.strip() == "���")
                &
                (df["status"].astype(str).str.strip() != "������")
            ]
        )

        return {
            "������ ������": int(total_count),
            "������": int(completed_count),
            "���������": int(incomplete_count),
            "���������": round(completion_rate, 1),
            "������ ���������": int(urgent_incomplete_count)
        }


    def get_category_counts():
        """
        ��������������� ������ ��������� ���������������.
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
        ������������ '���'������ ������ ������������ ������ ��������� ������������.
        """

        urgent_df = df[
            (df["urgency"].astype(str).str.strip() == "���")
            &
            (df["status"].astype(str).str.strip() != "������")
        ]

        if urgent_df.empty:
            return {
                "������": 0,
                "������": []
            }

        # ������ ������ ������������ LLM��� ��������� ��������� ������
        result_df = urgent_df.head(20)

        return {
            "������": len(urgent_df),
            "������": result_df.to_dict(
                orient="records"
            )
        }


    # =====================================================
    # 5. Tool ������
    # =====================================================

    calculate_kpi_declaration = {
        "name": "calculate_kpi",
        "description": (
            "������������ ������������ ������ ������, ������, ���������, "
            "���������, ������ ��������� ��������� ���������������."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }


    get_category_counts_declaration = {
        "name": "get_category_counts",
        "description": (
            "������������ ��������������� ��������������� ������ ��������� ���������������."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }


    find_urgent_incomplete_declaration = {
        "name": "find_urgent_incomplete",
        "description": (
            "������������ '���'��������� ��������� ��������� ������ "
            "������ ��������� ��������� ������������."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }


    # =====================================================
    # 6. Tool ������
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
��������� ��������� ������������ ��������� ������ AI Agent���������.

������������ ��������� ������������,
��������� ������ ��������� Tool��� ������������ ���������������.

Tool ������ ������:

1. ������������, ��������� ��� ��������� ��������� ������
   calculate_kpi��� ���������������.

2. ��������������� ��������� ��������� ������
   get_category_counts��� ���������������.

3. ������������ ������������ ��� ��������� ��������� ������
   find_urgent_incomplete��� ���������������.

4. ������������ ������ ��������� ������������ ���������.

5. ��������� ��� ������ ���������
   '������ ������'������ ���������������.

6. ��������� ��� ������ ��������� ��������� ������������ ������
   ��������� Tool ��������� ���������������.

7. ������ ��������� ��������� ��������������� ������
   ������ ��������� ������������ ���������.

8. ������ ��������� ������������ ������ ���������������
   ������ ��������������� ��������� ��������� ���������������.
"""
    )


    # =====================================================
    # 7. Agent ������
    # =====================================================

    st.subheader("2. AI Agent������ ������ ������")

    user_request = st.text_area(
        "������ ��������� ���������������.",
        placeholder=(
            "���: ������ ������������ ��������� ������������ "
            "������������ ������������ ��� ��������� ��������� ���������."
        ),
        height=120
    )


    if st.button(
        "���� Agent ������",
        use_container_width=True
    ):

        if not user_request.strip():

            st.warning(
                "Agent������ ��������� ��������� ���������������."
            )

        else:

            with st.spinner(
                "AI Agent��� ��������� ��������� ������������ ������������..."
            ):

                # =========================================
                # 1��� Gemini ������
                # ������ Tool��� ������������ ������
                # =========================================

                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=user_request,
                    config=config
                )


                # =========================================
                # ��������� ��������� Function Call ������
                # =========================================

                function_calls = response.function_calls


                if not function_calls:

                    # Tool��� ������������ ������ ������
                    st.subheader("3. Agent ������")

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
                    # ������ Tool ������ ������
                    # =====================================

                    executed_tools = []

                    for function_call in function_calls:

                        function_name = (
                            function_call.name
                        )


                        # ---------------------------------
                        # Tool ������
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
                                f"��� ��� ������ Tool: {function_name}"
                            }


                        executed_tools.append(
                            {
                                "tool": function_name,
                                "result": result
                            }
                        )


                        # ---------------------------------
                        # Tool ��������� Gemini������ ������
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
                    # 2��� Gemini ������
                    # Tool ��������� ������������ ������ ������ ������
                    # =====================================

                    final_response = (
                        client.models.generate_content(
                            model=MODEL_NAME,
                            contents=contents,
                            config=config
                        )
                    )


                    # =====================================
                    # ������ ������
                    # =====================================

                    st.subheader("3. Agent ������ ������")


                    with st.expander(
                        "Agent��� ��������� Tool ������"
                    ):

                        for item in executed_tools:

                            st.markdown(
                                f"**{item['tool']}**"
                            )

                            st.json(
                                item["result"]
                            )


                    st.subheader("4. Agent ������ ������")

                    st.markdown(
                        final_response.text
                    )

    
