import openai
from datetime import datetime
from typing import List
from bson import ObjectId
from app.core.config import settings
from app.schemas.request.report_request import ReportRequest
from app.schemas.response.report_response import ReportResponse, QuestionReport
from app.core.database import get_mongo_client
from fastapi import HTTPException

client = openai.OpenAI(api_key=settings.GPT_API_KEY)
db = get_mongo_client()[settings.MONGO_DB_NAME]


class ReportService:
    @staticmethod
    async def generate_report(interview_id: str, data: ReportRequest) -> ReportResponse:
        report_items: List[QuestionReport] = []

        # MongoDB에서 해당 interviewId에 대한 보고서 조회
        existing_reports = await db["question_reports"].find({
            "interviewId": interview_id
        }).to_list(length=None)

        if existing_reports:
            # 이미 생성된 보고서가 있으면 그것을 반환
            for report in existing_reports:
                report_items.append(QuestionReport(
                    question=report["question"],
                    intent=report["intent"],
                    answerSummary=report["answerSummary"],
                    answerImprovement=report["answerImprovement"]
                ))
        else:
            # 해당 면접의 모든 질문과 답변 조회
            answers = await db["answers"].find({
                "interview_id": interview_id
            }).to_list(length=None)

            for answer in answers:
                question_id = answer["question_id"]
                question_doc = await db["questions"].find_one({"_id": ObjectId(question_id)})

                if not question_doc:
                    continue

                question = question_doc["question"]
                answer_text = answer["answer"]

                # GPT 호출: 질문 의도 분석
                intent_prompt = f"""

[질문 의도 평가]
다음 질문에 대해 수험자가 제시한 답변이 질문의 의도에 적절하게 부합하는지를 평가하세요.
한 문장으로 간결하게 작성하고, 구체적인 이유를 포함하세요.
[질문] {question}
[답변] {answer_text}
"""
                intent = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": intent_prompt}],
                    temperature=0.3
                ).choices[0].message.content.strip()

                # GPT 호출: 답변 요약
                summary_prompt = f"""
[답변 요약 및 평가]
다음은 수험자의 답변입니다. 답변을 간결하게 요약하고, 평가자의 시선에서 전반적인 인상을 함께 서술해 주세요.
- 답변의 핵심 내용을 1~2문장으로 요약해 주세요.
- 논리성, 구체성, 태도, 진정성 등을 종합적으로 고려해 평가자의 총평을 자연스럽게 작성해 주세요.
- 모든 내용을 3~4줄 이내의 자연스럽고 부드러운 문장으로 작성해 주세요.
[답변] {answer_text}
"""
                summary = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.4
                ).choices[0].message.content.strip()

                # GPT 호출: 답변 개선
                improve_prompt = f"""
[답변 개선]
다음은 수험자의 답변입니다. 맞춤법과 문법을 고치고, 자연스럽게 정리해 주세요. 의미는 바꾸지 마세요.
[원문]
{answer_text}
"""
                improvement = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": improve_prompt}],
                    temperature=0.3
                ).choices[0].message.content.strip()

                report_items.append(QuestionReport(
                    question=question,
                    intent=intent,
                    answerSummary=summary,
                    answerImprovement=improvement
                ))

                # 저장
                await db["question_reports"].insert_one({
                    "interviewId": interview_id,
                    "interviewType": data.interviewType,
                    "questionId": str(question_doc["_id"]),
                    "answerId": str(answer["_id"]),
                    "question": question,
                    "intent": intent,
                    "answerSummary": summary,
                    "answerImprovement": improvement,
                    "createdAt": datetime.utcnow()
                })

        return ReportResponse(
            interviewType=data.interviewType,
            report=report_items
        )

