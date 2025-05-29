from fastapi import status
from app.core.exceptions.base import AppException

class NotFoundException(AppException):
    def __init__(self, message: str = "상품을 찾을 수 없습니다."):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)

class AlreadyExistsException(AppException):
    def __init__(self, message: str = "이미 존재하는 상품입니다."):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUE)

class SmileAnalysisException(AppException):
    def __init__(self, message: str = "smile_score 계산에 실패했습니다."):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

class InvalidVideoException(AppException):
    def __init__(self, message: str = "영상 열기 실패했습니다."):
        super().__init__(message=message, status_code=status.HTTP_422_INVALID_VIDEO)