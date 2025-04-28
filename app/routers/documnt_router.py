from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.services.ocr_service import process_pdf_ocr
from pdf2image.exceptions import PDFInfoNotInstalledError
from PIL import UnidentifiedImageError

import app.database

router = APIRouter()

@router.post("/documents/ocr")
async def convert_to_text(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        content = await file.read()
        result = await process_pdf_ocr(content)

        # text만 모아서 하나의 문자열로 만들기
        combined_text = ''.join(item['text'] for item in result)
        await app.database.insert_document(app.database.documents_collection,  {"content": combined_text} )

        return JSONResponse(content={"texts": result})

    except PDFInfoNotInstalledError:
        raise HTTPException(status_code=500, detail="Poppler is not installed or not found in PATH.")

    except UnidentifiedImageError:
        raise HTTPException(status_code=422, detail="Failed to process image from PDF.")

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/documents/ocr")
async def test_get_document():
    try:
        documents_cursor = app.database.documents_collection.find()
        documents = await documents_cursor.to_list(length=None)

        # _id가 ObjectId 타입이면 문자열로 변환
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])

        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")