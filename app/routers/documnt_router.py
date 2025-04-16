from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.services.ocr_service import process_pdf_ocr
from pdf2image.exceptions import PDFInfoNotInstalledError
from PIL import UnidentifiedImageError

router = APIRouter()

@router.post("/documents/ocr")
async def convert_to_text(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        content = await file.read()
        result = await process_pdf_ocr(content)
        return JSONResponse(content={"texts": result})

    except PDFInfoNotInstalledError:
        raise HTTPException(status_code=500, detail="Poppler is not installed or not found in PATH.")

    except UnidentifiedImageError:
        raise HTTPException(status_code=422, detail="Failed to process image from PDF.")

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
