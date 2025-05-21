from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.response import CommonResponse
from app.core.exceptions.base import AppException

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=CommonResponse[None](
            success=False,
            message=exc.message,
            data=None
        ).model_dump()
    )