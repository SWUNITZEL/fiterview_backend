from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ocr_service import process_pdf_ocr
from pdf2image.exceptions import PDFInfoNotInstalledError
from PIL import UnidentifiedImageError
from app.repository.document_repository import *

router = APIRouter()

@router.post("/documents/ocr")
async def convert_to_text(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        content = await file.read()
        result = await process_pdf_ocr(content)

        # text만 모아서 하나의 문자열로 만들기
        # combined_text = ''.join(item['text'] for item in result)

        combined_text = ''
        combined_grades = {}
        combined_features = ''
        for item in result:
            combined_text += item['text']

            for subject, ranks in item.get('grades', {}).items():
                if subject not in combined_grades:
                    combined_grades[subject] = []
                combined_grades[subject].extend(ranks)

            if item.get('features'):
                combined_features += item['features']

        await insert_document({"content": combined_text, "grades": combined_grades, "features": combined_features})

        return HTTPException(status_code=200, detail="ocr success")

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
        documents = await get_all_documents()

        # _id가 ObjectId 타입이면 문자열로 변환
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])

        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")