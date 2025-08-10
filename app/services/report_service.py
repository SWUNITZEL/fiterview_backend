import openai
from datetime import datetime
from typing import List
from bson import ObjectId
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.response.report_response import ReportResponse, QuestionReport
from app.core.database import database
from app.common.extract import extract_improved_answer
from app.services.answer_service import AnswerService
from app.common.s3_utils import generate_presigned_url

client = openai.OpenAI(api_key=settings.GPT_API_KEY)

# --- 안전 쿼리 헬퍼 ---
def _interview_filter(iid: str):
    """interview_id가 snake/camel, str/ObjectId 어떤 형태든 매칭"""
    iid = (str(iid) if iid is not None else "").strip()
    ors = [{"interview_id": iid}, {"interviewId": iid}]
    try:
        oid = ObjectId(iid)
        ors += [{"interview_id": oid}, {"interviewId": oid}]
    except Exception:
        pass
    return {"$or": ors}

def _qid_filter(qid: str):
    """questions._id가 str/ObjectId 모두 매칭"""
    ors = [{"_id": qid}]
    try:
        ors.append({"_id": ObjectId(qid)})
    except Exception:
        pass
    return {"$or": ors}


# --- 평가 카테고리 ---
EVALUATION_CATEGORIES = {
    "1": {
        "title": "질문 의도를 잘 파악한 답변이에요.",
        "detail": "질문의 본질을 잘 이해하고, 그에 맞춰 명확하게 답변했어요.\n주제에 집중하면서도 하고자 하는 말이 분명하게 드러났어요.\n면접관 입장에서 듣고 싶은 내용이 잘 담긴 모범적인 답변이에요.",
    },
    "2": {
        "title": "핵심에서 조금 벗어난 답변이에요.",
        "detail": "답변이 질문의 취지와 완전히 맞지는 않았어요.\n조금 더 핵심을 짚는 연습이 필요해 보여요.\n답변 전에 질문을 정확히 분석하고, 관련된 경험 위주로 구성해 보세요.",
    },
    "3": {
        "title": "이해하기 쉽게 잘 정리된 답변이에요.",
        "detail": "중요한 내용을 앞부분에 배치해서 듣는 사람이 이해하기 쉬웠어요.\n전체적인 구조도 논리적으로 잘 짜여 있어서 전달력이 좋았어요.\n이런 흐름은 안정감 있는 인상을 줄 수 있어요.",
    },
    "4": {
        "title": "결정적인 부분이 조금 아쉬운 답변이에요.",
        "detail": "전체적으로 나쁘지 않았지만, 가장 강조해야 할 부분이 약했어요.\n주장의 근거가 조금 부족하거나 설득력이 떨어졌을 수 있어요.\n답변을 마무리하기 전에 중요한 메시지를 더 힘 있게 전달해 보세요.",
    },
    "5": {
        "title": "경험이 잘 드러난 설득력 있는 답변이에요.",
        "detail": "자신의 경험을 바탕으로 한 논리적인 전개가 인상적이었어요.\n이야기 전개에 진정성이 담겨 있어 공감을 유도하기 좋았어요.\n면접관에게 자신을 효과적으로 어필한 좋은 사례예요.",
    },
    "6": {
        "title": "조금 더 구체적인 표현이 필요해 보여요.",
        "detail": "전하고자 하는 메시지는 있었지만 표현이 다소 추상적이었어요.\n실제 경험이나 수치가 빠져 있어 설득력이 약해졌어요.\n구체적인 사례나 결과를 곁들이면 더 신뢰감 있는 답변이 될 수 있어요.",
    },
}

class ReportService:
    @staticmethod
    def build_good_example_prompt(question: str, answer: str, major: str) -> str:
        def get_dynamic_fewshot(prompt_text: str) -> str:
            if "장단점" in prompt_text or "자신의 장점과 단점" in prompt_text:
                return """
[예시]
질문: 본인의 장점과 단점에 대해 말해주세요.
답변: 저의 장점은 성실함이고 저의 단점은 한 번 몰입하면 너무 지나칠 때가 있다는 것입니다.
Step 1. 분석: 흔한 모범답변처럼 보여 차별성이 떨어집니다.
Step 2. 개선 방향: 구체적인 사례와 그로 인한 결과를 담으면 좋습니다.
Step 3. 개선 답변: 저의 장점은 성실함입니다. 예를 들어, 영어 성적을 끌어올리기 위해 매일 공부계획을 세워 1년간 꾸준히 실천했고, 결국 1등급 향상이라는 결과를 얻었습니다...
"""
            elif "자기소개" in prompt_text or "1분 자기소개" in prompt_text:
                return """
[예시]
질문: 1분 자기소개 해보세요.
답변: 안녕하세요. 저는 ESG경영과 생성형 AI를 마케팅에 접목시키는 데 관심이 있는 학생입니다.
Step 1. 분석: 관심은 드러나지만, 구체적인 활동이나 강점이 부족합니다.
Step 2. 개선 방향: 본인의 특성과 활동을 연결해 간결히 표현해야 합니다.
Step 3. 개선 답변: 저는 ESG경영과 생성형 AI에 대해 학습하고, 실제 프로젝트에 적용한 경험이 있습니다. 이를 통해 기술적 감각과 사회적 가치를 함께 고려하는 마케터로 성장하고자 합니다.
"""
            else:
                return ""

        prompt_text = f"{question}\n{answer}\n{major}"
        example = get_dynamic_fewshot(prompt_text)

        return f"""
당신은 대학 입시 면접관이자 {major} 전공 교수입니다.
면접관의 시각에서 수험생의 답변을 분석하고 논리성과 구체성, 설득력을 기준으로 평가한 뒤, 개선된 답변을 제시해야 합니다.

질문: {question}
지원자 답변: "{answer}"

{example}

아래 형식에 맞춰 작성하세요:

Step 1. 분석:
Step 2. 개선 방향:
Step 3. 개선된 답변:
"""

    @staticmethod
    async def generate_report(interview_id: str) -> ReportResponse:
        interview_id = (str(interview_id) if interview_id is not None else "").strip()
        report_items: List[QuestionReport] = []

        # 1) 기존 보고서 재사용
        existing_reports = await database["question_reports"].find(
            {"interviewId": interview_id}
        ).to_list(length=None)

        if existing_reports:
            for report in existing_reports:
                report_items.append(
                    QuestionReport(
                        question_id=report.get("question_id") or report.get("questionId"),
                        answer_id=report.get("answer_id") or report.get("answerId"),
                        question=report["question"],
                        intent=report["intent"],
                        answerText=report["answerText"],
                        evaluation=report["evaluation"],
                        goodExample=report["goodExample"],
                        summary=report["summary"],
                        videos=report.get("videos", []),
                    )
                )
            return ReportResponse(report=report_items)

        # 2) answers 조회
        answers = await database["answers"].find(_interview_filter(interview_id)).to_list(length=None)
        if not answers:
            # 기존 동작 유지: 비어 있으면 빈 배열 반환
            return ReportResponse(report=[])

        # 3) 각 answer에 대해 report 생성
        for answer in answers:
            question_id = answer.get("question_id")
            if not question_id:
                continue

            # questions 조회 (문자열/ObjectId 모두 매칭)
            question_doc = await database["questions"].find_one(_qid_filter(question_id))
            if not question_doc:
                continue

            # 질문 텍스트 추출
            question = (
                question_doc.get("question_text")
                or question_doc.get("question")
                or ""
            )
            if not question:
                continue

            answer_text = answer.get("answer", "")
            major = question_doc.get("major", "일반")

            # GPT 호출: 질문 의도
            intent_prompt = f"""
다음 질문에 대해 수험자가 제시한 답변이 질문의 의도에 적절하게 부합하는지를 평가하세요.
절대 항목을 나열하거나 장문으로 작성하지 마.문장 하나로 간단명료하게 써야 해.
[질문]
{question}
"""
            intent = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": intent_prompt}],
                temperature=0.3,
            ).choices[0].message.content.strip()

            # GPT 호출: 평가
            evaluation_prompt = f"""
너는 지금부터 문장으로 절대 대답할 수 없어.
모든 응답은 문장이 아닌 숫자와 ,로 구성되어있어야 해

너는 간단하게 대답하는 경력있는 유명 대학입시면접 컨설턴트야. 다음 질문에 대한 답변이 어떤 카테고리에 어울리는지 판단하여 3개의 카테고리에 대한 키 값을 선택해줘

질문: {question}
질문 의도: {intent}
사용자 지망 학과: {major}
답변: {answer_text}

선택지: {{"1": "질문 의도를 잘 파악한 답변이에요.", "2": "핵심에서 조금 벗어난 답변이에요.", "3": "이해하기 쉽게 잘 정리된 답변이에요.", "4": "결정적인 부분이 조금 아쉬운 답변이에요.", "5": "경험이 잘 드러난 설득력 있는 답변이에요.", "6": "조금 더 구체적인 표현이 필요해 보여요."}}

답변형태 예시: 1,2,3
"""
            evaluation_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": evaluation_prompt}],
                temperature=0.3,
            ).choices[0].message.content.strip()

            evaluation_keys = [key.strip() for key in evaluation_response.split(",")]
            evaluation_titles = [
                EVALUATION_CATEGORIES[key]["title"]
                for key in evaluation_keys
                if key in EVALUATION_CATEGORIES
            ]

            # GPT 호출: goodExample
            good_example_prompt = ReportService.build_good_example_prompt(question, answer_text, major)
            good_example_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "너는 대학 입시 면접 전문가야."},
                    {"role": "user", "content": good_example_prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            ).choices[0].message.content.strip()
            good_example_response = extract_improved_answer(good_example_response)

            # 답변 세부 분석
            word_list, hesitant_list, hesitant_score = await AnswerService.analysis_answer(answer_text)
            top_words = ", ".join([f"{w}({c})" for w, c in word_list[:3]]) if word_list else "없음"
            hesitant_expressions = ", ".join(hesitant_list[:3]) if hesitant_list else "없음"

            # GPT 호출: summary
            summary_prompt = f"""
당신은 대학 입시 면접관입니다. 아래 정보를 바탕으로 수험자의 답변을 분석하고, 총평을 3~4줄 이내로 작성하세요.

[사용자 전공]
- {major}

[답변 요약 요소]
- 주요 단어: {top_words}
- 말끝 흐림 표현: {hesitant_expressions}
- 흐림 비율: {hesitant_score}%

[수험자 답변]
{answer_text}

요청 사항:
- 총평 안에 수험자의 답변 내용을 1~2문장으로 요약하고,
- 이어서 논리성, 태도, 구체성, 표현 방식 등을 반영한 전반적인 평가를 1~2문장으로 작성하세요.
- 흐림 표현과 흐림 비율이 높을 경우, 전달력이나 자신감이 다소 부족하다는 평가를 반영하세요.
- 전공과 단어 선택이 일치하거나 설득력 있는 경우, 그 강점을 언급하세요.
- 총평은 잘한 점과 개선점을 모두 포함하고, 표현이 자연스럽고 일관되게 이어지도록 작성하세요.
- 평가자 관점에서 작성하며, 총평 외의 설명이나 지시문은 포함하지 마세요.
"""
            summary = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.4,
            ).choices[0].message.content.strip()

            # 비디오 URL presign
            video_url = answer.get("video_url") if isinstance(answer, dict) else getattr(answer, "video_url", None)
            if video_url and video_url.startswith("s3://"):
                try:
                    _, bucket_and_key = video_url.split("s3://", 1)
                    bucket, *key_parts = bucket_and_key.split("/")
                    key = "/".join(key_parts)
                    video_url = generate_presigned_url(bucket, key)
                except Exception:
                    video_url = None

            video_paths = [video_url] if video_url else []

            # 결과 누적
            report_items.append(
                QuestionReport(
                    question_id=str(question_doc.get("_id")),
                    answer_id=str(answer.get("_id")),
                    question=question,
                    intent=intent,
                    answerText=answer_text,
                    evaluation=evaluation_titles,
                    goodExample=good_example_response,
                    summary=summary,
                    videos=video_paths,
                )
            )

            # 저장
            await database["question_reports"].insert_one(
                {
                    "interviewId": interview_id,
                    "question_id": str(question_doc.get("_id")),
                    "answer_id": str(answer.get("_id")),
                    "question": question,
                    "intent": intent,
                    "answerText": answer_text,
                    "evaluation": evaluation_titles,
                    "goodExample": good_example_response,
                    "summary": summary,
                    "createdAt": datetime.utcnow(),
                    "videos": video_paths,
                }
            )

        return ReportResponse(report=report_items)


