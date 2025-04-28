import httpx
import uuid
import time
import asyncio
from pdf2image import convert_from_bytes
from io import BytesIO
from app.config.config import settings
import re


CLOVA_OCR_URL = settings.CLOVA_OCR_URL
CLOVA_SECRET_KEY =settings.CLOVA_OCR_SECRET_KEY
MAX_CONCURRENT_REQUESTS = 5

HEADERS = {
    "X-OCR-SECRET": CLOVA_SECRET_KEY
}

# 문자열 전처리 함수: 생기부 내용에 필요없는 문자열 삭제
def extract_text(text):
    # 맨 첫 장에 오는 생기부 다운로드 관련 문장 삭제
    if (text.find("학교생활세부사항기록부") != -1):
        pattern1 = rf'^.*?\b\w*인적\w*\b\s+\b\w+\b'
        text = re.sub(pattern1, '', text, count=1)

    else:
        pattern1 = rf'^.*?\b\w*특기사항\w*\b'
        text = re.sub(pattern1, '', text, count=1)

    matches = list(re.finditer(rf'\b\w*고등학교\w*\b', text))
    if matches:
        last_match = matches[-1]
        text = text[:last_match.start()]

    return text.strip()

# ocr
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
                print("page:", page_number)
                full_text = extract_text(full_text)         # 전처리 수행

                return {"page": page_number, "text": full_text}
            else:
                print("page:", page_number, f"    {response.status_code} - {response.text}")
                return {
                    "page": page_number,
                    "text": f"Error: {response.status_code} - {response.text}"
                }
        except Exception as e:
            print("page:", page_number, "    errormessage: ", str(e))
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
