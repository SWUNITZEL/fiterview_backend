from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.repository.answer_repository import *
from app.services.answer_service import AnswerService

router = APIRouter()

@router.post("/answer/analysis")
async def answer_analysis(answer_id:str, answer: str):

    try:
        # 입력 검증
        if not answer.strip():
            raise HTTPException(status_code=404, detail="answer is empty.")

        # 분석 함수 실행
        final_result, hesitant_endings = await AnswerService.analysis_answer(answer_id, answer)


        return JSONResponse([final_result, hesitant_endings])

    except HTTPException as http_exc:
        raise http_exc

    except Exception as exc:
        raise HTTPException(status_code = 500,detail=f"error: {str(exc)}")

# @router.get("/answer/analysis")
# async def test_get_answer():
#     try:
#         documents = await get_all_answers()
#
#         # _id가 ObjectId 타입이면 문자열로 변환
#         for doc in documents:
#             if '_id' in doc:
#                 doc['_id'] = str(doc['_id'])
#
#         return documents
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")