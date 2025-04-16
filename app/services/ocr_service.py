import httpx
import uuid
import time
import asyncio
from pdf2image import convert_from_bytes
from io import BytesIO
from app.config.config import settings

CLOVA_OCR_URL = settings.CLOVA_OCR_URL
CLOVA_SECRET_KEY =settings.CLOVA_OCR_SECRET_KEY
MAX_CONCURRENT_REQUESTS = 5

HEADERS = {
    "X-OCR-SECRET": CLOVA_SECRET_KEY
}

async def send_ocr_request(img_bytes: bytes, page_number: int):
    request_json = {
        "version": "V2",
        "requestId": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
        "images": [{
            "format": "jpg",
            "name": f"page_{page_number}"
        }]
    }

    files = {
        'file': (f"page_{page_number}.jpg", img_bytes, 'image/jpeg')
    }

    data = {
        'message': str(request_json).replace("'", '"')
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(CLOVA_OCR_URL, headers=HEADERS, files=files, data=data)
            if response.status_code == 200:
                ocr_json = response.json()
                fields = ocr_json["images"][0].get("fields", [])
                texts = [field["inferText"] for field in fields]
                full_text = " ".join(texts)
                return {"page": page_number, "text": full_text}
            else:
                return {
                    "page": page_number,
                    "text": f"Error: {response.status_code} - {response.text}"
                }
        except Exception as e:
            return {
                "page": page_number,
                "text": f"Exception: {str(e)}"
            }

async def process_pdf_ocr(pdf_bytes: bytes):
    images = convert_from_bytes(pdf_bytes, dpi=300)
    results = []

    for i in range(0, len(images), MAX_CONCURRENT_REQUESTS):
        tasks = []
        for j, img in enumerate(images[i:i + MAX_CONCURRENT_REQUESTS]):
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)
            tasks.append(send_ocr_request(img_byte_arr.getvalue(), i + j + 1))

        batch_result = await asyncio.gather(*tasks)
        results.extend(batch_result)

    return results
