from app.core.exceptions.base import AppException
from app.schemas.response.document_response import DocumentResponse
from app.services.ocr_service import OCRService
from app.agent.student_recore_agent import StudentRecordAgent
from app.models.document_model import Document
from pdf2image.exceptions import PDFInfoNotInstalledError
from PIL import UnidentifiedImageError
from app.repository.document_repository import DocumentRepository

import re

class DocumentService:

    def __init__(self):
        self.document_repository = DocumentRepository()
        self.ocr_service = OCRService()
        self.student_record_agent = StudentRecordAgent()

        # 과목 패턴 구성
        self.subject_mapping = {
            '기술': 'etc',  # 제2외국어, 기술과 가정 등
            '국어': 'korean',
            '수학': 'math',
            '영어': 'english',
            '사회': 'social',
            '과학': 'science',
            '한국사': 'history'
        }

    async def process_document(self, document, user_email):
        try:
            if not document.filename.endswith(".pdf"):
                raise AppException(status_code=400, message="Only PDF files are supported.")

            if user_email == "":
                raise AppException(status_code=400, message="Email is required.")

            content = await document.read()
            result = await self.ocr_service.process_pdf_ocr(content)

            combined_text = ''
            combined_features = ''
            for item in result:
                combined_text += item['text']

                if item.get('features'):
                    combined_features += item['features']

            combined_grades = self.process_grades(combined_text)
            recommended_major, advice, type, explanation, hashtags = self.student_record_agent.analyze_student_record(combined_features, combined_grades, len(combined_grades.get("math")))

            document = Document(
                user_email=user_email,
                content=combined_text,
                grades=combined_grades,
                features=combined_features,
                type=type,
                hashtags=hashtags,
                explanation=explanation,
                advice=advice,
                recommended_major=recommended_major

            )

            # 저장된 생활기록부가 없으면 새로 저장하고, 있으면 업데이트
            user_document = await self.document_repository.find_by_user_email(user_email)
            if user_document is None:
                await self.document_repository.insert_document(document)
            else:
                document_id = user_document.get("_id")

                await self.document_repository.update_document(document_id, document)

            return DocumentResponse(
                user_email=user_email,
                grades=combined_grades,
                type=type,
                hashtags=hashtags,
                explanation=explanation,
                advice=advice,
                recommended_major=recommended_major
            )

        except PDFInfoNotInstalledError:
            raise AppException(status_code=500, message="Poppler is not installed or not found in PATH.")

        except UnidentifiedImageError:
            raise AppException(status_code=422, message="Failed to process image from PDF.")

        except AppException as e:
            raise e

        except Exception as e:
            raise AppException(status_code=500, message=f"Internal Server Error: {str(e)}")


    # 성적 평균값 추출 파이프라인
    def process_grades (self, text):
        grade = self.extract_grades(text)

        sp = self.split_grades_by_semester(grade)

        average = self.calculate_average_grades(sp)

        result = self.restructure_by_subject(average)

        return result


    # 성적 추출
    def extract_grades(self, text):

        subject_mapping = {
            '기술': 'etc',  # 제2외국어 등
            '국어': 'korean',
            '수학': 'math',
            '영어': 'english',
            '사회': 'social',
            '과학': 'science',
            '한국사': 'history'
        }

        # 학년별로 블로 나눠 추출
        pattern = r"\[(\d학년)\](?:.*?)원점수/과목평균(.*?합계\s*\d+)"
        blocks = re.findall(pattern, text, re.DOTALL)

        results = {}

        for grade, content in blocks:

            # [수정 2] 'content'에서 첫 과목명의 시작 위치를 찾습니다.
            min_index = float('inf')

            # '정보' 과목도 '기술'로 취급되므로 탐색 리스트에 추가
            subject_names = list(subject_mapping.keys()) + ['정보']

            for subject in subject_names:
                index = content.find(subject)
                if index != -1 and index < min_index:
                    min_index = index

            # 만약 과목을 하나도 못찾았다면 이 블록은 건너뜀
            if min_index == float('inf'):
                print(f"[{grade}] 블록에서 과목을 찾지 못했습니다.")
                continue

            # 찾은 첫 과목 위치부터 content를 슬라이싱
            content = content[min_index:]

            # 공백 제거
            content = content.replace(" ", "").replace("전입학", "").replace("1PP", "\n")

            # '이수단위합계'까지만 자르기
            end_index = content.find("이수단위합계")
            if end_index != -1:
                content = content[:end_index]

            # 나머지 불필요한 문자 제거
            content = (content.replace("양", "")
                       .replace("어/한문/교", "")
                       .replace("과학과학탐구실험", ""))  # '과학'과 중복 집계 방지

            grade_dict = {}

            # 과목별로 등급 추출
            for kor_subject, eng_subject in subject_mapping.items():
                # 절대평가 배제하지 않고 그냥 실행
                pattern_subject = kor_subject

                if kor_subject == '국어':
                    base_pattern = rf'{pattern_subject}.*?'
                else:
                    base_pattern = rf'(?<![가-힣]){pattern_subject}.*?'

                pattern = base_pattern + r'\([\d\.]+\)\(\d+\)(\d)'

                matches = re.findall(pattern, content)

                # (예외 처리) 만약 위 패턴으로 못찾았는데, A(272) 같은 패턴이 있다면 그것도 시도
                if not matches:
                    pattern_alpha = rf'(?<![가-힣]){pattern_subject}.*?[A-F]\(\d+\)(\d)'
                    matches = re.findall(pattern_alpha, content)

                grade_dict[eng_subject] = [int(rank) for rank in matches] if matches else []

            results[grade] = grade_dict
        return results


    # 학년 정보를 학기 정보로 분할
    def split_grades_by_semester(self, grades_dict):
        result = {}

        for grade_year, subjects in grades_dict.items():
            semester_data = {'1학기': {}, '2학기': {}}

            for subject, ranks in subjects.items():
                if not ranks:
                    semester_data['1학기'][subject] = []
                    semester_data['2학기'][subject] = []
                else:
                    mid = (len(ranks) + 1) // 2
                    # 홀수 개일 때는 앞쪽을 1학기라고 가정
                    semester_data['1학기'][subject] = ranks[:mid]
                    semester_data['2학기'][subject] = ranks[mid:]

            result[grade_year] = semester_data

        return result


    # 평균 계산
    def calculate_average_grades(self, grades_by_semester):
        result = {}

        for grade_year, semesters in grades_by_semester.items():
            result[grade_year] = {}

            for semester, subjects in semesters.items():
                subject_avgs = {}

                for subject, ranks in subjects.items():
                    cleaned = []
                    for r in ranks:
                        try:
                            cleaned.append(int(r))
                        except (ValueError, TypeError):
                            continue

                    if cleaned:
                        avg = round(sum(cleaned) / len(cleaned), 2)
                    else:
                        avg = None

                    subject_avgs[subject] = avg

                result[grade_year][semester] = subject_avgs

        return result


    # 과목을 키값으로 하고, 평균 정보를 리스트로 갖는 딕셔너리로 변환
    def restructure_by_subject(self, avg_by_semester):
        subject_dict = {}

        # 학년, 학기, 과목 순으로 루프
        for grade_year in avg_by_semester:
            for semester in avg_by_semester[grade_year]:
                for subject, avg in avg_by_semester[grade_year][semester].items():
                    # 해당 과목 없으면 리스트 생성
                    if subject not in subject_dict:
                        subject_dict[subject] = []

                    # 평균값이 존재하면 평균값을, 아니면 0을 추가
                    if avg is None:
                        subject_dict[subject].append(0)
                    else:
                        subject_dict[subject].append(avg)

        return subject_dict

