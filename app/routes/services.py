from fastapi import APIRouter, Depends, HTTPException, Request
from app.models import Service
from app.utils import decode_token
from pymongo import MongoClient
import os

router = APIRouter()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["portialabs"]
services_collection = db["services"]
users_collection = db["users"]

@router.post("/new")
async def create_service(service: Service, request: Request):
    payload = decode_token(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = users_collection.find_one({"email": payload["sub"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    service_data = {"ip": service.ip, "domain": service.domain, "user_id": user["_id"]}
    services_collection.insert_one(service_data)
    return {"message": "Service created successfully"}

@router.put("/update/{service_id}")
async def update_service(service_id: str, service: Service, request: Request):
    payload = decode_token(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = users_collection.find_one({"email": payload["sub"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    services_collection.update_one({"_id": service_id, "user_id": user["_id"]}, {"$set": service.dict()})
    return {"message": "Service updated successfully"}

@router.delete("/delete/{service_id}")
async def delete_service(service_id: str, request: Request):
    payload = decode_token(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = users_collection.find_one({"email": payload["sub"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    services_collection.delete_one({"_id": service_id, "user_id": user["_id"]})
    return {"message": "Service deleted successfully"}