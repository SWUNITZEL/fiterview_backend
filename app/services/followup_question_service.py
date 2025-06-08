import openai
from typing import List
from bson import ObjectId
from app.core.config import settings
from app.core.database import get_mongo_client
from app.schemas.response.followup_question_response import FollowupQuestionResponse
from app.core.exceptions.custom import InterviewNotFoundException


client = openai.OpenAI(api_key=settings.GPT_API_KEY)
db = get_mongo_client()
class FollowupQuestionService:
    @staticmethod
    async def generate_followup_questions(answer_id: str) -> FollowupQuestionResponse:
        """
        답변 기반으로 꼬리 질문 생성.
        
        Args:
            answer_id (str): 답변 ID
            
        Returns:
            FollowupQuestionResponse: 생성된 꼬리 질문들
            
        Raises:
            InterviewNotFoundException: 답변을 찾을 수 없는 경우
        """
        # 답변 조회
        answer_doc = await db["answers"].find_one({"_id": ObjectId(answer_id)})
        if not answer_doc:
            raise InterviewNotFoundException("답변을 찾을 수 없습니다.")
        
        answer_text = answer_doc["answer"]
        question_id = answer_doc.get("question_id")
        
        # 원본 질문도 함께 조회 (컨텍스트를 위해)
        original_question = ""
        if question_id:
            question_doc = await db["questions"].find_one({"_id": ObjectId(question_id)})
            if question_doc:
                original_question = question_doc["question"]
        
        # 꼬리 질문 생성
        followup_prompt = f"""
다음은 면접에서 나온 질문과 지원자의 답변입니다. 이 답변을 바탕으로 더 깊이 있게 탐구할 수 있는 꼬리 질문 1개를 생성해주세요.

[원본 질문]
{original_question}

[지원자 답변]
{answer_text}

꼬리 질문은 다음 기준을 고려하여 한 문장으로 작성해주세요:
- 답변 내용을 더 구체적으로 설명하도록 유도
- 답변에서 언급된 경험이나 배경을 심화 탐구
- 자연스럽고 대화형 면접 상황에 적합

반드시 1개의 문장만 출력하고, 다른 설명이나 줄바꿈 없이 질문만 출력해주세요.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": followup_prompt}],
            temperature=0.7
        )
        
        # 응답을 파싱하여 질문 목록으로 변환
        followup_text = response.choices[0].message.content.strip()
        followup_questions = [q.strip() for q in followup_text.split('\n') if q.strip()]
        
        # 결과 반환
        return FollowupQuestionResponse(
            answerId=answer_id,
            originalAnswer=answer_text,
            followupQuestions=followup_questions
        ) 