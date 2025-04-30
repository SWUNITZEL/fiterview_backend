from bson import ObjectId
from fastapi import APIRouter, HTTPException
from app.models.test import Test
from app.repository.test_repository import *

router = APIRouter()

@router.post("/test/insert")
async def insert_doc(document: Test):
    await insert_document(document.model_dump())
    return {"result": "ok"}

@router.get("/test/select/{name}", response_model=Test)
async def get_doc(name: str):
    doc = await find_document({"name": name})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return Test(name=doc['name'], age=doc['age'])

@router.put("/documents/{id}")
async def update_doc(id: str, doc: Test):
    result = await update_document(ObjectId(id), doc.dict(exclude_unset=True))
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Updated"}

@router.delete("/documents/{id}")
async def delete_doc(id: str):
    result = await delete_document(ObjectId(id))
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Deleted"}
