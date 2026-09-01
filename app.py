import streamlit as st
import pandas as pd
from google import genai


# =========================================================
# 1. Streamlit 기본 설정
# =========================================================

st.set_page_config(
    page_title="업무지원 CSV AI Agent",
    page_icon="📊",
    layout="wide"
)

st.title("업무지원 CSV AI Agent")
st.caption("교육용 합성 데이터를 분석하는 AI Agent")


# =========================================================
# 2. Gemini 설정
# =========================================================

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

# 사용할 Gemini 모델
# 모델을 변경할 경우 이 부분만 수정하면 됨
MODEL_NAME = "gemini-3-flash-preview"


# =========================================================
# 3. CSV 파일 업로드
# =========================================================

uploaded_file = st.file_uploader(
    "업무지원 CSV 파일을 업로드하세요.",
    type=["csv"]
)


# =========================================================
# 4. CSV 업로드 후 분석
# =========================================================

if uploaded_file is not None:

    # -----------------------------------------------------
    # CSV 읽기
    # -----------------------------------------------------

    df = pd.read_csv(uploaded_file)


    # =====================================================
    # 4-1. 데이터 미리보기
    # =====================================================

    st.subheader("1. 데이터 미리보기")

    st.dataframe(
        df,
        use_container_width=True
    )


    # =====================================================
    # 4-2. KPI 계산
    # =====================================================

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


    # 긴급 미완료
    urgent_incomplete = df[
        (df["urgency"].astype(str).str.strip() == "상")
        &
        (df["status"].astype(str).str.strip() != "완료")
    ]

    urgent_incomplete_count = len(
        urgent_incomplete
    )


    # =====================================================
    # 4-3. KPI 화면
    # =====================================================

    st.subheader("2. 주요 현황")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "전체 요청",
        f"{total_count}건"
    )

    col2.metric(
        "완료",
        f"{completed_count}건"
    )

    col3.metric(
        "완료율",
        f"{completion_rate:.1f}%"
    )

    col4.metric(
        "긴급 미완료",
        f"{urgent_incomplete_count}건"
    )


    # =====================================================
    # 4-4. 업무분류별 집계
    # =====================================================

    st.subheader("3. 업무분류별 요청")

    category_counts = (
        df["category"]
        .astype(str)
        .str.strip()
        .value_counts()
        .reset_index()
    )

    category_counts.columns = [
        "업무분류",
        "요청건수"
    ]


    # 왼쪽 표 / 오른쪽 차트
    category_col1, category_col2 = st.columns(2)

    with category_col1:

        st.markdown("#### 업무분류별 집계")

        st.dataframe(
            category_counts,
            use_container_width=True
        )


    with category_col2:

        st.markdown("#### 업무분류별 요청건수")

        st.bar_chart(
            category_counts.set_index("업무분류")
        )


    # =====================================================
    # 4-5. 긴급 미완료 요청
    # =====================================================

    st.subheader("4. 긴급 미완료 요청")

    if urgent_incomplete.empty:

        st.success(
            "현재 긴급 미완료 요청이 없습니다."
        )

    else:

        st.warning(
            f"긴급 미완료 요청이 "
            f"{urgent_incomplete_count}건 있습니다."
        )

        st.dataframe(
            urgent_incomplete,
            use_container_width=True
        )


    # =====================================================
    # 5. AI Agent 기능
    # =====================================================

    st.subheader("5. AI Agent")

    st.caption(
        "Python에서 계산한 결과를 바탕으로 "
        "AI가 분석 보고서 또는 보고 메일 초안을 작성합니다."
    )


    # -----------------------------------------------------
    # 버튼 2개를 나란히 배치
    # -----------------------------------------------------

    report_col, mail_col = st.columns(2)


    with report_col:

        report_button = st.button(
            "📄 AI 분석 보고서 생성",
            use_container_width=True
        )


    with mail_col:

        mail_button = st.button(
            "✉️ 보고 메일 초안 생성",
            use_container_width=True
        )


    # =====================================================
    # 5-1. AI 분석 보고서 생성
    # =====================================================

    if report_button:

        # 업무분류별 집계를 텍스트로 변환
        category_text = (
            category_counts
            .to_string(index=False)
        )


        # 긴급 미완료 상세를 텍스트로 변환
        urgent_text = (
            urgent_incomplete
            .to_string(index=False)
            if not urgent_incomplete.empty
            else "없음"
        )


        # -------------------------------------------------
        # 보고서 생성 Prompt
        # -------------------------------------------------

        report_prompt = f"""
당신은 교육용 업무지원 데이터 분석 Agent입니다.

Python에서 이미 계산한 결과를 아래에 제공합니다.

[전체 요청]
{total_count}건

[완료]
{completed_count}건

[미완료]
{incomplete_count}건

[완료율]
{completion_rate:.1f}%

[긴급 미완료]
{urgent_incomplete_count}건

[업무분류별 요청]
{category_text}

[긴급 미완료 상세]
{urgent_text}


위 계산 결과를 근거로
내부 업무보고용 분석 보고서를 작성하세요.


다음 구조를 사용합니다.

1. Executive Summary

2. 주요 현황

3. 업무분류별 특징

4. 긴급 확인 대상

5. 담당자가 확인할 사항

6. 추가 확인 필요사항


작성 원칙:

- 제공된 데이터만 근거로 작성하세요.

- 제공되지 않은 원인을 추측하지 마세요.

- 숫자를 임의로 변경하지 마세요.

- 데이터에서 확인할 수 없는 사항은
  '확인 필요'라고 표시하세요.

- 긴급 미완료 요청이 있다는 이유만으로
  실제 장애나 문제의 원인을 확정하지 마세요.

- 공공기관 또는 금융기관 내부 보고서에 적합한
  간결하고 공식적인 문체를 사용하세요.

- 이 데이터는 교육용 합성자료입니다.
"""


        # -------------------------------------------------
        # Gemini 호출
        # -------------------------------------------------

        with st.spinner(
            "AI가 분석 보고서를 작성하고 있습니다..."
        ):

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=report_prompt
            )


        # -------------------------------------------------
        # 결과 출력
        # -------------------------------------------------

        st.markdown("---")

        st.markdown(
            "### 📄 AI 분석 보고서"
        )

        st.markdown(
            response.text
        )


    # =====================================================
    # 5-2. 보고 메일 초안 생성
    # =====================================================

    if mail_button:

        # -------------------------------------------------
        # 이메일 생성 Prompt
        # -------------------------------------------------

        mail_prompt = f"""
당신은 업무보고 이메일 작성 Agent입니다.

다음 업무지원 분석 결과를 바탕으로
내부 보고용 이메일 초안을 작성하세요.


[분석 결과]

전체 요청: {total_count}건

완료: {completed_count}건

미완료: {incomplete_count}건

완료율: {completion_rate:.1f}%

긴급 미완료: {urgent_incomplete_count}건


메일은 다음 형식으로 작성하세요.


제목:

본문:


본문은 다음 순서로 구성합니다.

1. 분석대상

2. 주요 현황

3. 긴급 확인사항

4. 추가 확인 필요사항


작성 원칙:

- 제공된 분석 결과만 사용하세요.

- 데이터에 없는 원인을 추측하지 마세요.

- 숫자를 임의로 변경하지 마세요.

- 확인할 수 없는 사항은
  '확인 필요'라고 표시하세요.

- 긴급 미완료 요청이 있다는 이유만으로
  장애 원인이나 담당자의 책임을 추측하지 마세요.

- 내부 업무보고 이메일에 적합하도록
  간결하고 공식적인 문체를 사용하세요.

- 이메일 마지막에는
  '※ 본 내용은 교육용 합성자료를 기반으로 작성되었습니다.'
  라고 표시하세요.
"""


        # -------------------------------------------------
        # Gemini 호출
        # -------------------------------------------------

        with st.spinner(
            "AI가 보고 메일 초안을 작성하고 있습니다..."
        ):

            mail_response = client.models.generate_content(
                model=MODEL_NAME,
                contents=mail_prompt
            )


        # -------------------------------------------------
        # 결과 출력
        # -------------------------------------------------

        st.markdown("---")

        st.markdown(
            "### ✉️ 보고 메일 초안"
        )

        st.markdown(
            mail_response.text
        )
