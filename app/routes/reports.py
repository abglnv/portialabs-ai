from fastapi import APIRouter, Depends, HTTPException
from app.utils import decode_token
from pymongo import MongoClient
import os

router = APIRouter()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["portialabs"]
reports_collection = db["reports"]
users_collection = db["users"]

@router.get("/")
async def get_reports(token: str = Depends()):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = users_collection.find_one({"email": payload["sub"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    reports = list(reports_collection.find({"user_id": user["_id"]}, {"_id": 0}))
    return reports