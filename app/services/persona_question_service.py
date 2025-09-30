import openai
from typing import List
from app.core.config import settings
from app.core.exceptions.base import AppException
from app.repository.combine_repository import CombineRepository
from app.repository.document_repository import DocumentRepository
from app.repository.interview_repository import InterviewRepository
from app.repository.question_repository import QuestionRepository
from app.schemas.response.question_response import QuestionOutput, CreatePersonaQuestionResponse

from app.agent.comment_agent import CommentAgent
from app.agent.question_gen_agent import QuestionGenAgent
from app.agent.document_agent import DocumentAgent
from app.agent.priority_agent import PriorityAgent

client = openai.OpenAI(api_key=settings.GPT_API_KEY)


class PersonaQuestionService:
    combine_repo = CombineRepository()
    interview_repo = InterviewRepository()
    document_repo = DocumentRepository()
    question_repo = QuestionRepository()

    comment_agent = CommentAgent()
    question_gen_agent = QuestionGenAgent()
    document_agent = DocumentAgent()
    priority_agent = PriorityAgent()


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
            interview_id: str,
            count : int
    ) -> List[QuestionOutput]:

        processed_data = {}
        processed_data = {
            "department": major,
            "document": document_text,
            "interview_id" : interview_id,
        }

        summary = PersonaQuestionService.document_agent.generate_document(
            department=university,
            document=document_text
        )
        processed_data["summary"] = summary

        # comment 생성
        comment = PersonaQuestionService.comment_agent.generate_comment(
            department=major,
            document=summary
        )
        processed_data["comment"] = comment
        questions = PersonaQuestionService.question_gen_agent.generate_questions(
            department=university,
            document=document_text,
            comment=comment,
            count=count,
            persona_label=persona_label
        )

        # 질문 sort
        ranked_questions = PersonaQuestionService.priority_agent.generate_priority(
            department=university,
            questions=questions,
        )

        return comment, ranked_questions

    async def createPersonaQuestion(interview_id: str) -> CreatePersonaQuestionResponse:
        interview = await PersonaQuestionService.interview_repo.find_by_id(interview_id)
        if interview is None:
            raise AppException(status_code=404, message="인터뷰를 찾을 수 없습니다.")

        # 기존 질문 존재 여부 확인
        existing_questions = await PersonaQuestionService.question_repo.get_questions_by_interview_id(interview_id)
        if existing_questions:
            return CreatePersonaQuestionResponse(
                questions=existing_questions
            )

        combine_id = interview["combine_id"]
        combine = await PersonaQuestionService.combine_repo.find_by_id(combine_id)
        if combine is None:
            raise AppException(status_code=404, message="면접 조합을 찾을 수 없습니다.")

        user_id = combine["user_d"]
        document = await PersonaQuestionService.document_repo.find_by_user_email(user_id)

        comment, questions = await PersonaQuestionService.generate_interview_questions(
            document_text=document["content"],
            persona_label=combine["department"],
            major=combine["department"],
            university=combine["university"],
            interview_id=interview_id,
            count=combine["question_count"]
        )

        # MongoDB에 저장
        await PersonaQuestionService.question_repo.save_questions(
            interview_id=interview_id,
            persona=combine["persona"],
            major=combine["department"],
            university=combine["university"],
            questions=questions,
            comment=comment
        )

        validated_questions = [QuestionOutput(**q) for q in questions]

        return CreatePersonaQuestionResponse(
            # personaLabel=combine["persona"],
            # department=combine["department"],
            questions=validated_questions
        )
