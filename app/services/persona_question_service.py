import openai
from datetime import datetime
from typing import List, Optional
from app.core.config import settings
from app.models.question_model import Question
from app.schemas.response.question_response import QuestionOutput

client = openai.OpenAI(api_key=settings.GPT_API_KEY)

class PersonaQuestionService:
    """
    페르소나 기반 질문 목록

    Returns:
        list: 페르소나 질문 목록
            - questionIndex (int): 질문 순서
            - questionText (str): 메인 질문 내용
            - hasFollowUp (bool): 후속 질문 존재 여부
            - followUpText (str): 후속 질문 내용 (hasFollowUp이 true인 경우)

    Example:
        [
            {
                "questionIndex": 4,
                "questionText": "당신의 가장 큰 장점은 무엇인가요?",
                "hasFollowUp": true,
                "followUpText": "이 장점을 발휘한 구체적인 사례를 말씀해주세요."
            },
            {
                "questionIndex": 5,
                "questionText": "당신의 단점은 무엇인가요?",
                "hasFollowUp": true,
                "followUpText": "이 단점을 극복하기 위해 어떤 노력을 하고 있나요?"
            }
        ]
    """
    @staticmethod
    async def generate_interview_questions(
        document_text: str,
        persona_label: str,
        major: str,
        interview_id: str
    ) -> List[QuestionOutput]:
        prompt = f"""
당신은 다음과 같은 성향의 대학 면접관입니다:

{persona_label}

아래는 한 수험생의 자기소개서 또는 생활기록부입니다.

아래 형식에 따라 총 10개의 질문을 생성하세요.  
질문은 지원 전공 '{major}'과 문서 내용을 기반으로 하며, 면접관의 성격도 반영되어야 합니다.

[질문 구성]
1. 자기소개 요청  
2. 대학 지원 동기  
3. 전공 지원 동기  
4. 장단점  
5~9. 경험·가치관·활동 등 기반 심화질문  
10. 마지막 한마디 요청

[문서 내용]
{document_text}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        raw_text = response.choices[0].message.content.strip()
        question_lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        questions: List[QuestionOutput] = []

        for idx, text in enumerate(question_lines):
            index = idx + 1
            has_followup = index in [4, 5, 6, 7, 8, 9]
            followup_question: Optional[str] = None

            # 4~9번 질문에 대해서 꼬리 응답 생성
            if has_followup:
                followup_prompt = f"""
당신은 '{persona_label}' 성향의 대학 면접관입니다.

다음 질문에 대해 수험자의 사고를 확장시킬 수 있는 꼬리질문 1개를 생성하세요.
[질문]
{text}
"""
                followup_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": followup_prompt}],
                    temperature=0.7
                )
                followup_question = followup_response.choices[0].message.content.strip()

            questions.append(QuestionOutput(
                interviewId=interview_id,
                questionText=text,
                questionIndex=index,
                totalQuestions=len(question_lines),
                personaLabel=persona_label,
                major=major,
                hasFollowup=has_followup,
                followupQuestion=followup_question,
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow()
            ))

        return questions