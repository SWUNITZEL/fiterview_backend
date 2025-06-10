import openai
from datetime import datetime
from typing import List
from app.core.config import settings
from app.core.exceptions.base import AppException
from app.repository.combine_repository import CombineRepository
from app.repository.document_repository import DocumentRepository
from app.repository.interview_repository import InterviewRepository
from app.repository.question_repository import QuestionRepository
from app.schemas.response.question_response import QuestionOutput, CreatePersonaQuestionResponse

client = openai.OpenAI(api_key=settings.GPT_API_KEY)


class PersonaQuestionService:
    combine_repo = CombineRepository()
    interview_repo = InterviewRepository()
    document_repo = DocumentRepository()
    question_repo = QuestionRepository()

    """
    페르소나 기반 질문 목록

    Returns:
        list: 페르소나 질문 목록
            - questionIndex (int): 질문 순서
            - questionText (str): 메인 질문 내용
            - hasFollowUp (bool): 후속 질문 존재 여부

    Example:
        [
            {
                "questionIndex": 4,
                "questionText": "당신의 가장 큰 장점은 무엇인가요?",
                "hasFollowUp": true,
            },
            {
                "questionIndex": 5,
                "questionText": "당신의 단점은 무엇인가요?",
                "hasFollowUp": true,
            }
        ]
    """

    @staticmethod
    async def generate_interview_questions(
            document_text: str,
            persona_label: List[str],
            major: str,
            university: str,
            interview_id: str
    ) -> List[QuestionOutput]:
        prompt = f"""
당신은 다음과 같은 성향의 대학 면접관입니다:

{persona_label}

아래는 한 수험생의 자기소개서 또는 생활기록부입니다.

아래 형식에 따라 총 10개의 질문을 생성하세요.  
질문은 지원 전공 '{major}'과 지원 대학 '{university}' 정보를 반영하며, 문서 내용을 기반으로 면접관의 성격도 드러나야 합니다.

[질문 구성]
1. 자기소개 요청  
2. 대학 지원 동기  
3. 전공 지원 동기  
4. 장단점  
5~9. 경험·가치관·활동 등 기반 심화질문  
10. 마지막 한마디 요청

질문은 오직 10개만 생성하세요. 인사말이나 마무리 멘트는 제외합니다.

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

            questions.append(QuestionOutput(
                interviewId=interview_id,
                questionText=text,
                questionIndex=index,
                totalQuestions=len(question_lines),
                personaLabel=persona_label,
                major=major,
                university=university,
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow()
            ))

        return questions

    async def createPersonaQuestion(interview_id: str) -> CreatePersonaQuestionResponse:
        interview = await PersonaQuestionService.interview_repo.find_by_id(interview_id)
        if interview is None:
            raise AppException(status_code=404, message="인터뷰를 찾을 수 없습니다.")

        combine_id = interview["combine_id"]
        combine = await PersonaQuestionService.combine_repo.find_by_id(combine_id)
        if combine is None:
            raise AppException(status_code=404, message="면접 조합을 찾을 수 없습니다.")

        user_id = combine["user_d"]
        document = await PersonaQuestionService.document_repo.find_by_user_email(user_id)

        questions = await PersonaQuestionService.generate_interview_questions(
            document_text=document["features"],
            persona_label=combine["department"],
            major=combine["department"],
            university=combine["university"],
            interview_id=interview_id
        )

        # MongoDB에 저장
        await PersonaQuestionService.question_repo.save_questions(
            persona=combine["persona"],
            major=combine["department"],
            university=combine["university"],
            questions=questions
        )

        return CreatePersonaQuestionResponse(
            # personaLabel=combine["persona"],
            # department=combine["department"],
            questions=questions
        )
