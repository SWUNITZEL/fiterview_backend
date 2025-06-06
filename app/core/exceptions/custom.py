from fastapi import status
from app.core.exceptions.base import AppException

class NotFoundException(AppException):
    def __init__(self, message: str = "상품을 찾을 수 없습니다."):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)

class InvalidVideoException(AppException):
    def __init__(self, message: str = "영상 열기 실패했습니다."):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

class ImageNotFoundException(AppException):
    def __init__(self, message: str = "이미지를 찾을 수 없습니다."):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)

class InterviewNotFoundException(AppException):
    def __init__(self, message: str = "인터뷰를 찾을 수 없습니다."):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)

class QuestionNotFoundException(AppException):
    def __init__(self, message: str = "질문을 찾을 수 없습니다."):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)
