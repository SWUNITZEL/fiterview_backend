from http.client import HTTPException

import status
from bson import ObjectId
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import os
import grpc
from app.generated import nest_pb2, nest_pb2_grpc
import analysis, database
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status


app = FastAPI()

# MongoDB 클라이언트 생성
client = database.client
db = database.database
collection = db['test_collection']

# 데이터 모델
class Document(BaseModel):
    name: str
    age: int


def get_application() -> FastAPI:
    application = FastAPI()

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )

    return application


app = get_application()
@app.post("/test/insert")
async def insert_db(document: Document):
    # Pydantic 모델을 dict로 변환
    doc_dict = document.model_dump()
    await database.insert_document(collection, doc_dict)
    return {"result": "ok"}

@app.get("/test/select/{name}", response_model=Document)
async def get_db(name: str):
    document = await database.find_document(collection, {"name":name})
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return Document(name=document['name'], age=document['age'])

@app.put("/documents/{id}")
async def update_document(id: str, doc: Document):
    # MongoDB에서 문서 업데이트
    update_result = collection.update_one({"_id": ObjectId(id)}, {"$set": doc.dict(exclude_unset=True)})
    if update_result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Document not found or no update needed")
    return {"message": "Document updated successfully"}

@app.delete("/documents/{id}")
async def delete_document(id: str):
    # MongoDB에서 문서 삭제
    delete_result = collection.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}

@app.get("items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# WebSocket을 통한 실시간 음성 스트리밍 처리
@app.websocket("/stt/ws")
async def websocket_endpoint(websocket: WebSocket):
    origin = websocket.headers.get('origin')
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    if origin not in allowed_origins:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    print("Client connected")
    await websocket.accept()

    # gRPC 채널 설정
    channel = grpc.insecure_channel('localhost:50051')  # 서버 주소
    stub = nest_pb2_grpc.NestServiceStub(channel)

    def audio_stream_generator(audio_data: bytes):
        yield nest_pb2.AudioChunk(audio_data=audio_data)

    try:
        while True:
            # WebSocket을 통해 음성 데이터 수신
            audio_data = await websocket.receive_bytes()

            # 음성 데이터를 클로바 스피치 API에 전송하고 텍스트로 변환
            response = stub.StreamingRecognize(audio_stream_generator(audio_data))

            # 응답에서 텍스트 추출
            text = response.results[0].alternatives[0].transcript  #프론트랑 연결해서 오류나면 수정필요

            # 실시간 음성 인식 결과를 클라이언트로 전송
            await websocket.send_text(f"Recognized: {text}")

    except WebSocketDisconnect:
        print("Client disconnected")

# 비디오와 이미지 업로드 처리
UPLOAD_DIR = './uploads/'

@app.post("/upload/")
async def upload_file(video: UploadFile = File(...), img: UploadFile = File(...)):

    video_filename = os.path.join(UPLOAD_DIR, video.filename)
    img_filename = os.path.join(UPLOAD_DIR, img.filename)

    # 파일 저장
    with open(video_filename, "wb") as f:
        f.write(await video.read())
    with open(img_filename, "wb") as f:
        f.write(await img.read())

    # 비디오 분석 수행
    try:
        result = analysis()
        return JSONResponse(content={"message": "성공!", "result": result}, status_code=200)
    except Exception as e:
        # 에러 발생 시 메시지 반환
        raise HTTPException(status_code=500, detail=f"Error during video analysis: {str(e)}")


# 서버 실행 확인용 (main.py에 엔드포인트를 두고 테스트 가능)
@app.get("/")
def read_root():
    return {"message": "FastAPI server is running!"}

# 서버 실행
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
