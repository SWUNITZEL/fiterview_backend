import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket

from app.core.exceptions.base import AppException
from app.core.exceptions.handlers import app_exception_handler
from app.core.response import CommonResponse
from app.routers import (document_router, answer_router, test_router, user_router, interview_router,
                         passage_feedback_router,
                         selfinfo_feedback_router, persona_question_router)
from app.websocket.interview_websocket import websocket_interview

app = FastAPI()

# 예외 핸들러 등록
app.add_exception_handler(AppException, app_exception_handler)

# 라우터 등록
app.include_router(test_router.router)
app.include_router(document_router.router)
app.include_router(user_router.router)
app.include_router(interview_router.router)
#app.include_router(answer_router.router)
app.include_router(document_router.router)
#app.include_router(passage_feedback_router.router)
app.include_router(selfinfo_feedback_router.router)
app.include_router(persona_question_router.router)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# WebSocket
@app.websocket("/interview/{interview_id}")
async def websocket_route(websocket: WebSocket, interview_id: str):
    await websocket_interview(websocket, interview_id)

# 서버 실행 확인용
@app.get("/")
def read_root():
    return CommonResponse.success_response("server is running")

# 서버 실행
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
