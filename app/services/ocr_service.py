import httpx
import uuid
import time
import asyncio
from pdf2image import convert_from_bytes
from io import BytesIO
from app.core.config import settings
import re


CLOVA_OCR_URL = settings.CLOVA_OCR_URL
CLOVA_SECRET_KEY =settings.CLOVA_OCR_SECRET_KEY
MAX_CONCURRENT_REQUESTS = 5

HEADERS = {
    "X-OCR-SECRET": CLOVA_SECRET_KEY
}


# 문자열 전처리 함수: 생기부 내용에 필요없는 문자열 삭제
def clean_text(text):
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


# 성적 추출 메서드
def extract_grades(text):
    delete_index = text.find("(수강자수)")
    if delete_index == -1:
        return {}

    text = text.replace(" ", "")

    if text.find("<진로선택과목>") != -1:
        removal_patterns = r'<진로선택과목>.*?이수단위합계'
        text = re.sub(removal_patterns, '', text)

    text = (text[text.find("(수강자수)") + len("(수강자수)"):].replace("양","").replace("과학과학탐구실험", ""))

    # 과목 패턴 구성
    subject_mapping = {
        '기술': 'etc',        # 제2외국어 등
        '국어': 'korean',
        '수학': 'math',
        '영어': 'english',
        '사회': 'social',
        '과학': 'science',
        '한국사': 'history'
    }

    grade_dict = {}
    for kor_subject, eng_subject in subject_mapping.items():
        # 패턴: 과목명 뒤에 성취도(A-F) + 괄호 인원수 + 등수
        pattern = rf'(?<![가-힣]){re.escape(kor_subject)}.*?[A-F]\(?\d+\)?\s*(\d)'
        matches = re.findall(pattern, text)
        if matches:
            grade_dict[eng_subject] = [int(rank) for rank in matches]


    return grade_dict


# 세특 추출 메서드
def extract_features(text):
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
def process_document(text):
    cleaned_text = clean_text(text)
    grades = extract_grades(cleaned_text)
    features = extract_features(cleaned_text)

    return {
        "text": cleaned_text,
        "grades": grades,
        "features": features
    }


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


                result = process_document(full_text)

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

# ocr 전송: 마지막 페이지 제외
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
