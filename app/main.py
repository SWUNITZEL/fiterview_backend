import grpc
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket

from app.routers import document_router, answer_router, test_router, upload_router, user_router
from app.websocket.stt_handler import websocket_stt

app = FastAPI()

# 라우터 등록
app.include_router(test_router.router)
app.include_router(answer_router.router)
app.include_router(document_router.router)
app.include_router(upload_router.router)
app.include_router(user_router.router)

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
@app.websocket("/interview/{intreviewId}")
async def websocket_route(websocket: WebSocket, interviewId: int):
    await websocket_stt(websocket, interviewId)

# 서버 실행 확인용
@app.get("/")
def read_root():
    return {"message": "FastAPI server is running!"}

# 서버 실행
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
