from http.client import HTTPException
from bson import ObjectId
import uvicorn
from pydantic import BaseModel
from fastapi import WebSocket

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
from app import analysis, database
from fastapi import FastAPI
from app.routers import stt_router

app = FastAPI()

#stt 라우터 추가
app.include_router(stt_router.router)

#MongoDB 클라이언트 생성
client = database.client
db = database.database
collection = db['test_collection'] # test_collection 컬렉션 선택

# 데이터 모델
class Document(BaseModel):
    name: str
    age: int

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
        raise HTTPException(status_code=404, detail="Documnet not found")
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

@app.get("/")
async def read_root():
    return {"Hello":"World"}

@app.get("items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")



# 파일이 저장될 경로 설정
UPLOAD_DIR = './uploads/'

# 비디오와 이미지 업로드 처리
@app.post("/upload/")
async def upload_file(video: UploadFile = File(...), img: UploadFile = File(...)):
    # 파일이 저장될 경로 설정
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



if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
