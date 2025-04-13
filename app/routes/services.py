from fastapi import APIRouter, Depends, HTTPException, Request
from app.models import Service
from app.utils import decode_token
from pymongo import MongoClient
import os
import openai
import json 
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel


router = APIRouter()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["portialabs"]
services_collection = db["services"]
users_collection = db["users"]
technologies_collection = db["technologies"]

@router.get("/my-services")
async def get_my_services(request: Request):
    """
    Get all services associated with the authenticated user.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        list: A list of services associated with the user.
    """
    payload = decode_token(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = users_collection.find_one({"email": payload["sub"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    services_cursor = services_collection.find({"user_id": user["_id"]})
    services = list(services_cursor)

    # Convert ObjectId fields to str
    for service in services:
        service["_id"] = str(service["_id"])
        service["user_id"] = str(service["user_id"])
    return services 

class AnalyzeServiceRequest(BaseModel):
    service_id: str
    description: str

@router.post("/analyze-service")
async def analyze_service(request: Request, body: AnalyzeServiceRequest):
    """
    Analyze a service's description using OpenAI to extract potentially used technologies
    and save them to the database.

    Args:
        request (Request): The FastAPI request object.
        service_id (str): The ID of the service to analyze.

    Returns:
        dict: A message indicating the result of the analysis.
    """
    payload = decode_token(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = users_collection.find_one({"email": payload["sub"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Extract the description from the service
    service_id = body.service_id
    description = body.description

    # Use OpenAI to analyze the description
    prompt = f"""
    You are a technology analyst. Analyze the following service description and extract a JSON list of potentially used technologies. 
    Each technology should have the following fields:
    - name: The name of the technology
    - version: The version of the technology (if available)
    - description: A brief description of the technology
    - vendor: The vendor or provider of the technology (if available)

    Service Description:
    {description}

    Return the output as a JSON list. Do not include any additional text or formatting.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )
        technologies_json = response.choices[0].message.content
        print(technologies_json)
        technologies = json.loads(technologies_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing service: {str(e)}")

    # Save the extracted technologies to the database
    for tech in technologies:
        tech["service_id"] = str(service_id)
        tech["user_id"] = str(user["_id"])
        tech["timestamp"] = datetime.utcnow()
        technologies_collection.insert_one(tech)

    return {"message": "Technologies analyzed and saved successfully"}

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