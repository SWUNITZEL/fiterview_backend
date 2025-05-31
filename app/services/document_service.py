from app.core.exceptions.base import AppException
from app.schemas.response.document_response import DocumentResponse
from app.services.ocr_service import OCRService
from app.services.gpt_service import GPTService
from app.models.document_model import Document
from pdf2image.exceptions import PDFInfoNotInstalledError
from PIL import UnidentifiedImageError
from app.repository.document_repository import DocumentRepository

class DocumentService:

    def __init__(self):
        self.document_repository = DocumentRepository()
        self.gpt_service = GPTService()
        self.ocr_service = OCRService()

    async def process_document(self, document, user_email):
        try:
            if not document.filename.endswith(".pdf"):
                raise AppException(status_code=400, message="Only PDF files are supported.")

            if user_email == "":
                raise AppException(status_code=400, message="Email is required.")

            print(user_email)
            content = await document.read()
            result = await self.ocr_service.process_pdf_ocr(content)

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

            gpt_result = self.gpt_service.analyze_student_record_structured(combined_features)


            document = Document(
                user_email=user_email,
                content=combined_text,
                grades=combined_grades,
                features=combined_features,
                type=gpt_result.get("type"),
                hashtags=gpt_result.get("hashtags"),
                explanation=gpt_result.get("explanation")
            )

            await self.document_repository.insert_document(document)

            return DocumentResponse(
                user_email=user_email,
                grades=combined_grades,
                type=gpt_result.get("type"),
                hashtags=gpt_result.get("hashtags"),
                explanation=gpt_result.get("explanation")
            )

        except PDFInfoNotInstalledError:
            raise AppException(status_code=500, message="Poppler is not installed or not found in PATH.")

        except UnidentifiedImageError:
            raise AppException(status_code=422, message="Failed to process image from PDF.")

        except AppException as e:
            raise e

        except Exception as e:
            raise AppException(status_code=500, message=f"Internal Server Error: {str(e)}")
