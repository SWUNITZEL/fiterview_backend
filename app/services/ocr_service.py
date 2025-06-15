import httpx
import uuid
import time
import asyncio
from pdf2image import convert_from_bytes
from io import BytesIO
from app.core.config import settings
import re


class OCRService:

    CLOVA_OCR_URL = settings.CLOVA_OCR_URL
    CLOVA_SECRET_KEY =settings.CLOVA_OCR_SECRET_KEY
    MAX_CONCURRENT_REQUESTS = 3

    HEADERS = {
        "X-OCR-SECRET": CLOVA_SECRET_KEY
    }


    # 문자열 전처리 함수: 생기부 내용에 필요없는 문자열 삭제
    def clean_text(self, text):
        # 앞머리 제거
        if "학교생활세부사항기록부" in text:
            pattern1 = rf'^.*?\b\w*학교생활세부사항기록부\(\w*\b\)'
            text = re.sub(pattern1, '', text, count=1)

        elif "수상명" in text:
            text = text[text.find("수상명"):]

        elif "체험활동상황" in text:
            text = text[text.find("체험활동상황") + 20:]

        else:
            if "정부24" in text:
                pattern = rf'^.*?\b\w*정부24\S*\b\s+\S+'
            else:
                pattern = rf'^.*?\b\w*\)'
            text = re.sub(pattern, '', text, count=1)

        # 꼬리 자르기 (고등학교 이후)
        matches = list(re.finditer(r'\b\w*고등학교\w*\b', text))
        if matches:
            text = text[:matches[-1].start()]

            # 가려진 문구 제거
            removal_patterns = [
                r'해당내용.*?않습니다\.',
                r'해당\s?학년의\s?자료가\s?없습니다',
                r'해당\s?사항\s?없음'
            ]

            for pattern in removal_patterns:
                text = re.sub(pattern, '', text)

        return text.strip()

    # 세특 추출 메서드
    def extract_features(self, text):
        if "세부능력" not in text:
            return ""

        # 기준 문자열로 나누기
        parts = text.split("세부능력및특기사항")
        seoteks = parts[1:]

        result = []
        for seotek in seoteks:
            for end_marker in ["<체육", "<진로 선택 과목>", "원점수"]:
                if end_marker in seotek:
                    seotek = seotek[:seotek.find(end_marker)]
            result.append(seotek.strip())

        return " ".join(result)


    # 메인 파이프라인 함수 정의
    def process_document(self, text):
        cleaned_text = self.clean_text(text)
        features = self.extract_features(cleaned_text)

        return {
            "text": cleaned_text,
            "features": features
        }


    # ocr
    async def send_ocr_request(self, img_bytes: bytes, page_number: int):
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
                response = await client.post(self.CLOVA_OCR_URL, headers=self.HEADERS, files=files, data=data)
                if response.status_code == 200:
                    ocr_json = response.json()
                    fields = ocr_json["images"][0].get("fields", [])
                    texts = [field["inferText"] for field in fields]
                    full_text = " ".join(texts)


                    result = self.process_document(full_text)

                    return result
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

    # ocr 전송
    async def process_pdf_ocr(self, pdf_bytes: bytes):

        images = convert_from_bytes(pdf_bytes, dpi=300, use_cropbox=False, strict=False)
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)

        async def limited_ocr_request(img_bytes, page_number):
            async with semaphore:
                return await self.send_ocr_request(img_bytes, page_number)

        tasks = []
        for idx, img in enumerate(images):
            img_byte_arr = None
            try:
                img_byte_arr = BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_byte_arr.seek(0)
                tasks.append(limited_ocr_request(img_byte_arr.getvalue(), idx + 1))
            finally:
                img.close()
                del img
                img_byte_arr.close()

        results = await asyncio.gather(*tasks)
        return results
