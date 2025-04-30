from dns.resolver import Answer
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.services import answer_service
from app import database

router = APIRouter()



@router.post("/answer/analysis")
async def answer_analysis(answer: str):

    try:
        # 입력 검증
        if not answer.strip():
            raise HTTPException(status_code=404, detail="answer is empty.")

        # 분석 함수 실행
        final_result, hesitant_endings = await answer_service.analysis_answer(answer)


        return JSONResponse("ok")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as exc:
        raise HTTPException(status_code = 500,detail=f"error: {str(exc)}")

@router.get("/answer/analysis")
async def test_get_answer():
    try:
        documents_cursor = database.answers_collection.find()
        documents = await documents_cursor.to_list(length=None)

        # _id가 ObjectId 타입이면 문자열로 변환
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])

        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")