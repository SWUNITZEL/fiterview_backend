from openai import AsyncOpenAI

from app.core.config import settings

client = AsyncOpenAI(api_key=settings.GPT_API_KEY)

class FollowupQuestionService:
    @staticmethod
    async def generate_followup_questions(answer: str, question: str) -> str:
        """
        답변 기반으로 꼬리 질문 생성.

        Args:
            answer (str): 답변, question (str): 원래 질문

        Returns:
            str: 생성된 꼬리 질문들

        Raises:
            InterviewNotFoundException: 답변을 찾을 수 없는 경우
        """
        # 꼬리 질문 생성
        followup_prompt = f"""
        다음은 면접에서 나온 질문과 지원자의 답변입니다. 이 답변을 바탕으로 더 깊이 있게 탐구할 수 있는 꼬리 질문 1개를 생성해주세요.

        [원본 질문]
        {question}

        [지원자 답변]
        {answer}

        꼬리 질문 작성 기준:
        - 지원자가 이미 충분히 설명한 내용은 반복하지 말 것
        - 답변에서 언급된 경험, 동기, 결과, 배운 점 등을 더 구체적으로 탐구
        - 새로운 관점에서 답변을 확장할 수 있도록 질문할 것
        - 자연스럽고 대화형 면접 상황에 적합할 것
        - 반드시 1개의 문장만 출력하고, 다른 설명이나 줄바꿈 없이 질문만 출력할 것
        """

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": followup_prompt}],
            temperature=0.7,
        )

        followup_text = response.choices[0].message.content.strip()
        # followup_questions = [q.strip() for q in followup_text.split('\n') if q.strip()]

        return followup_text
